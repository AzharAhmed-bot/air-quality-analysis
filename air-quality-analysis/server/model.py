import pandas as pd
import numpy as np
import torch
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
import torch.nn as nn
import matplotlib.pyplot as plt

# === USER CHOICE PROMPT ===
print("Sensor types:\n 1. DHT22 (humidity/temperature)\n 2. PMS5003 (P0, P1, P2)")
sensor_type = input("Choose sensor type (DHT22 or PMS5003): ").strip().lower()

if sensor_type == "dht22":
    value_type = input("Predict 'humidity' or 'temperature'? ").strip().lower()
    target_column = value_type
elif sensor_type == "pms5003":
    value_type = input("Predict 'P0', 'P1', or 'P2'? ").strip().upper()
    target_column = value_type
else:
    raise ValueError("Invalid sensor type")

# === Load and preprocess dataset ===
df = pd.read_csv("air_quality_kenya_all_20250621_112219.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Select necessary columns
numeric_cols = ["P2", "P1", "P0", "humidity", "temperature", "location_traffic",
                "location_industry", "location_oven", "latitude", "longitude", "altitude"]
df_numeric = df[["timestamp", "location_id"] + [col for col in numeric_cols if col in df.columns]]

# Aggregate readings by minute per location
df_numeric = df_numeric.groupby([pd.Grouper(key='timestamp', freq='min'), 'location_id']).mean().reset_index()

# Add cyclical time features
df_numeric["hour"] = df_numeric["timestamp"].dt.hour
df_numeric["hour_sin"] = np.sin(2 * np.pi * df_numeric["hour"] / 24)
df_numeric["hour_cos"] = np.cos(2 * np.pi * df_numeric["hour"] / 24)

# Impute missing values
impute_cols = [col for col in ["P2", "P1", "P0", "humidity", "temperature", "location_traffic",
                               "location_industry", "location_oven"] if col in df_numeric.columns]
imputer = KNNImputer(n_neighbors=3)
df_numeric[impute_cols] = imputer.fit_transform(df_numeric[impute_cols])

# Scale features
scale_cols = impute_cols + ["hour_sin", "hour_cos"]
scaler = StandardScaler()
df_numeric[scale_cols] = scaler.fit_transform(df_numeric[scale_cols])

# Compute graph edges
def compute_edges(df, dist_threshold=0.01, time_threshold=120):
    edges = []
    coords = df[["latitude", "longitude"]].values
    timestamps = df["timestamp"].astype(np.int64) // 10**9
    locations = df["location_id"].values
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if abs(timestamps[i] - timestamps[j]) <= time_threshold:
                if locations[i] == locations[j]:
                    edges.append([i, j])
                    edges.append([j, i])
                else:
                    dist = np.sqrt((coords[i][0] - coords[j][0]) ** 2 +
                                   (coords[i][1] - coords[j][1]) ** 2)
                    if dist < dist_threshold:
                        edges.append([i, j])
                        edges.append([j, i])
    return np.array(edges)

edges = compute_edges(df_numeric)
edge_index = torch.tensor(edges, dtype=torch.long).t()

# Build graph data
x = torch.tensor(df_numeric[scale_cols].values, dtype=torch.float)
y = torch.tensor(df_numeric[target_column].values, dtype=torch.float).view(-1, 1)
data = Data(x=x, edge_index=edge_index, y=y)

# Time-based train/val/test split
train_end = df_numeric["timestamp"].min() + pd.Timedelta(minutes=6)
val_end = train_end + pd.Timedelta(minutes=2)

train_idx = df_numeric[df_numeric["timestamp"] < train_end].index
val_idx = df_numeric[(df_numeric["timestamp"] >= train_end) & (df_numeric["timestamp"] < val_end)].index
test_idx = df_numeric[df_numeric["timestamp"] >= val_end].index

# Define GNN model
class GNNModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.conv1 = GCNConv(input_dim, 16)
        self.conv2 = GCNConv(16, 8)
        self.dropout = nn.Dropout(0.2)
        self.dense = nn.Linear(8, 1)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = self.dropout(x)
        return self.dense(x)

# Train the model
model = GNNModel(input_dim=len(scale_cols))
optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
model.train()

for epoch in range(100):
    pred = model(data.x, data.edge_index)
    mask = ~torch.isnan(data.y[train_idx])
    loss = nn.MSELoss()(pred[train_idx][mask], data.y[train_idx][mask])
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Train Loss: {loss.item():.4f}")

# Evaluate the model
model.eval()
with torch.no_grad():
    pred = model(data.x, data.edge_index).detach().numpy()
    y_true = data.y[test_idx].numpy()
    y_pred = pred[test_idx]
    mask = ~np.isnan(y_true)
    mae = mean_absolute_error(y_true[mask], y_pred[mask])
    rmse = np.sqrt(mean_squared_error(y_true[mask], y_pred[mask]))
    r2 = r2_score(y_true[mask], y_pred[mask])

print(f"\nGNN prediction results for {target_column}:")
print(f"MAE : {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R²  : {r2:.3f}")

# Inverse transform predictions
target_column_index = scale_cols.index(target_column)
y_pred_real = scaler.inverse_transform(
    np.pad(y_pred, ((0, 0), (0, len(scale_cols) - 1)), mode='constant')
)[:, target_column_index]

# Inverse transform true values for comparison
y_true_real = scaler.inverse_transform(
    np.pad(y_true, ((0, 0), (0, len(scale_cols) - 1)), mode='constant')
)[:, target_column_index]

# Save real-value predictions
pred_df = pd.DataFrame({
    "location_id": df_numeric.loc[test_idx, "location_id"].values,
    "timestamp": df_numeric.loc[test_idx, "timestamp"].values,
    f"predicted_{target_column}": y_pred_real,
    f"actual_{target_column}": y_true_real
})
pred_df.to_json(f"predicted_{target_column}.json", orient="records", date_format="iso")
print(f"✅ Real-valued predictions saved to 'predicted_{target_column}.json'")

# Plot predictions vs actual
plt.figure(figsize=(12, 6))
plt.plot(pred_df["timestamp"], pred_df[f"predicted_{target_column}"], label="Predicted", color='orange')
plt.plot(pred_df["timestamp"], pred_df[f"actual_{target_column}"], label="Actual", color='blue', alpha=0.7)
plt.xlabel("Timestamp")
plt.ylabel(f"{target_column} (real units)")
plt.title(f"Predicted vs Actual {target_column.capitalize()} Over Time")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('prediction_vs_actual.png')
