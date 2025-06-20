import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split



def merge_rows():
    df = pd.read_csv('air_quality_kenya_3967_20250619_191144.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    has_hum_temp = df['humidity'].notna() & df['temperature'].notna()
    has_p_values = df[['P0', 'P1', 'P2']].notna().all(axis=1)
    df_hum_temp = df[has_hum_temp].copy()
    df_p_values = df[has_p_values].copy()
    merged_rows = []
    used_indices = set()

    for i, hum_row in df_hum_temp.iterrows():
        available_p_rows = df_p_values.loc[~df_p_values.index.isin(used_indices)]

        if available_p_rows.empty:
            break

        time_diffs = (available_p_rows['timestamp'] - hum_row['timestamp']).abs()
        nearest_idx = time_diffs.idxmin()
        p_row = available_p_rows.loc[nearest_idx]
        combined = hum_row.copy()
        combined['P0'] = p_row['P0']
        combined['P1'] = p_row['P1']
        combined['P2'] = p_row['P2']
        sensor_fields = ['sensor', 'sensor_type_name', 'sensor_manufacturer', 'software_version']
        for field in sensor_fields:
            combined[f'{field}_2'] = p_row[field]

        merged_rows.append(combined)
        used_indices.add(nearest_idx)

    # Create final DataFrame
    final_df = pd.DataFrame(merged_rows)
    return final_df


df=merge_rows()

features=["sensor_type_name","sensor_manufacturer","software_version",
            "sensor","location_id","city","country","hour","day_of_week","is_weekend","temperature","humidity",
            "P0","P1","location_traffic","location_industry","location_oven",
            "latitude","longitude","altitude","sensor_public"]


target=['P2']

x=df[features]
y=df[target]


print(y.value_counts())


X_train,X_test,y_train,y_test=train_test_split(
    x,y,test_size=0.2, random_state=42 
)

numerical_features=X_train.select_dyptes(include)