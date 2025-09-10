import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

@dataclass
class SensorRecommendation:
    sensor_id: int
    location_id: int
    latitude: float
    longitude: float
    city: str
    placement_score: float  # 0-100
    is_optimal: bool
    priority_level: str  # "HIGH", "MEDIUM", "LOW"
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    technical_details: Dict

class SensorPlacementRecommendationSystem:
    """
    Hybrid recommendation system that combines:
    1. Domain expertise rules
    2. Statistical analysis 
    3. ML-based anomaly detection
    4. Spatial analysis
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.2, random_state=42)
        self.clustering_model = DBSCAN(eps=0.3, min_samples=2)
        
        # Domain knowledge weights
        self.criteria_weights = {
            'data_quality': 0.25,
            'spatial_coverage': 0.25, 
            'environmental_context': 0.20,
            'temporal_reliability': 0.15,
            'technical_performance': 0.15
        }
    
    def analyze_all_sensors(self, df: pd.DataFrame) -> List[SensorRecommendation]:
        """
        Main function: Analyze all sensors and provide recommendations
        """
        print("🔍 Starting comprehensive sensor placement analysis...")
        print(f"📊 Analyzing {df['sensor'].nunique()} sensors across {df['location_id'].nunique()} locations")
        
        # Prepare data for analysis
        sensor_profiles = self._create_sensor_profiles(df)
        
        # Run all analysis components
        recommendations = []
        
        for i, (sensor_id, profile) in enumerate(sensor_profiles.items()):
            print(f"🔬 Analyzing sensor {sensor_id} ({i+1}/{len(sensor_profiles)})...")
            
            # Get sensor data
            sensor_data = df[df['sensor'] == sensor_id]
            
            # Run comprehensive analysis
            recommendation = self._analyze_single_sensor(
                sensor_id, profile, sensor_data, df, sensor_profiles
            )
            
            recommendations.append(recommendation)
        
        # Sort by placement score
        recommendations.sort(key=lambda x: x.placement_score, reverse=True)
        
        print("✅ Analysis complete!")
        return recommendations
    
    def _create_sensor_profiles(self, df: pd.DataFrame) -> Dict:
        """Create statistical profiles for each sensor"""
        
        profiles = {}
        
        for sensor_id in df['sensor'].unique():
            sensor_data = df[df['sensor'] == sensor_id]
            sensor_data['timestamp'] = pd.to_datetime(sensor_data['timestamp'], errors='coerce')

            
            if len(sensor_data) == 0:
                continue
                
            # Basic info
            location_info = sensor_data.iloc[0]
            
            # Statistical profile
            profile = {
                # Location info
                'location_id': location_info['location_id'],
                'latitude': location_info['latitude'],
                'longitude': location_info['longitude'],
                'city': location_info['city'],
                'altitude': location_info.get('altitude', 0),
                
                # Environmental context
                'traffic_level': location_info['location_traffic'],
                'industry_presence': location_info['location_industry'], 
                'oven_presence': location_info['location_oven'],
                
                # Technical info
                'sensor_type': location_info['sensor_type_name'],
                'manufacturer': location_info['sensor_manufacturer'],
                'is_public': location_info['sensor_public'],
                
                # Data statistics
                'total_readings': len(sensor_data),
                'unique_hours': sensor_data['hour'].nunique(),
                'unique_days': sensor_data['day_of_week'].nunique(),
                'date_range': (sensor_data['timestamp'].max() - sensor_data['timestamp'].min()).days,
                
                # Pollutant statistics
                'pollutant_stats': self._calculate_pollutant_stats(sensor_data),
                'data_completeness': self._calculate_completeness(sensor_data),
                'temporal_consistency': self._calculate_temporal_consistency(sensor_data),
            }
            
            profiles[sensor_id] = profile
        
        return profiles
    
    def _calculate_pollutant_stats(self, sensor_data: pd.DataFrame) -> Dict:
        """Calculate pollutant statistics"""
        stats = {}
        
        for pollutant in ['P1', 'P2', 'P0', 'humidity', 'temperature']:
            if pollutant in sensor_data.columns:
                values = sensor_data[pollutant].dropna()
                if len(values) > 0:
                    stats[pollutant] = {
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'completeness': len(values) / len(sensor_data)
                    }
                else:
                    stats[pollutant] = {'mean': 0, 'std': 0, 'completeness': 0}
        
        return stats
    
    def _calculate_completeness(self, sensor_data: pd.DataFrame) -> float:
        """Calculate overall data completeness score"""
        key_columns = ['P1', 'P2', 'P0', 'humidity', 'temperature']
        completeness_scores = []
        
        for col in key_columns:
            if col in sensor_data.columns:
                completeness = sensor_data[col].notna().sum() / len(sensor_data)
                completeness_scores.append(completeness)
        
        return np.mean(completeness_scores) if completeness_scores else 0
    
    def _calculate_temporal_consistency(self, sensor_data: pd.DataFrame) -> float:
        """Calculate temporal consistency score"""
        if len(sensor_data) < 2:
            return 0
        
        # Check hour coverage (good sensors report across different hours)
        hour_coverage = sensor_data['hour'].nunique() / 24
        
        # Check day coverage
        day_coverage = sensor_data['day_of_week'].nunique() / 7
        
        # Check for reasonable time distribution
        time_distribution = 1.0
        if 'timestamp' in sensor_data.columns:
            hourly_counts = sensor_data.groupby('hour').size()
            cv = hourly_counts.std() / hourly_counts.mean() if hourly_counts.mean() > 0 else 0
            time_distribution = max(0, 1 - cv/2)  
        
        return (hour_coverage * 0.4 + day_coverage * 0.3 + time_distribution * 0.3)
    
    def _analyze_single_sensor(self, sensor_id: int, profile: Dict, 
                             sensor_data: pd.DataFrame, all_data: pd.DataFrame,
                             all_profiles: Dict) -> SensorRecommendation:
        """Comprehensive analysis of a single sensor"""
        
        scores = {}
        strengths = []
        weaknesses = []
        recommendations = []
        
        # 1. Data Quality Analysis
        data_quality_score = self._assess_data_quality(profile, sensor_data)
        scores['data_quality'] = data_quality_score
        
        if data_quality_score >= 0.8:
            strengths.append(f"Excellent data quality ({data_quality_score:.2f}) - consistent readings")
        elif data_quality_score >= 0.6:
            strengths.append(f"Good data quality ({data_quality_score:.2f})")
        elif data_quality_score >= 0.4:
            weaknesses.append(f"Moderate data quality ({data_quality_score:.2f}) - some missing readings")
            recommendations.append("Investigate connectivity issues and improve data collection reliability")
        else:
            weaknesses.append(f"Poor data quality ({data_quality_score:.2f}) - frequent missing data")
            recommendations.append("Priority: Fix technical issues causing data loss")
        
        # 2. Spatial Coverage Analysis
        spatial_score = self._assess_spatial_coverage(profile, all_profiles)
        scores['spatial_coverage'] = spatial_score
        
        if spatial_score >= 0.8:
            strengths.append(f"Optimal spatial positioning ({spatial_score:.2f}) - good coverage contribution")
        elif spatial_score >= 0.6:
            strengths.append(f"Good spatial positioning ({spatial_score:.2f})")
        elif spatial_score >= 0.4:
            weaknesses.append(f"Suboptimal location ({spatial_score:.2f}) - close to other sensors")
            recommendations.append("Consider relocating to fill coverage gaps")
        else:
            weaknesses.append(f"Poor spatial coverage ({spatial_score:.2f}) - redundant location")
            recommendations.append("High priority: Relocate sensor to improve network coverage")
        
        # 3. Environmental Context Analysis
        env_score = self._assess_environmental_context(profile, sensor_data)
        scores['environmental_context'] = env_score
        
        if env_score >= 0.7:
            strengths.append(f"Excellent environmental placement ({env_score:.2f})")
        elif env_score >= 0.5:
            strengths.append(f"Good environmental context ({env_score:.2f})")
        else:
            weaknesses.append(f"Suboptimal environmental placement ({env_score:.2f})")
            recommendations.append("Review local environmental factors affecting readings")
        
        # 4. Temporal Reliability Analysis  
        temporal_score = profile['temporal_consistency']
        scores['temporal_reliability'] = temporal_score
        
        if temporal_score >= 0.8:
            strengths.append(f"Excellent temporal coverage ({temporal_score:.2f})")
        elif temporal_score >= 0.6:
            strengths.append(f"Good temporal reliability ({temporal_score:.2f})")
        else:
            weaknesses.append(f"Poor temporal coverage ({temporal_score:.2f})")
            recommendations.append("Improve sensor uptime and reporting frequency")
        
        # 5. Technical Performance Analysis
        tech_score = self._assess_technical_performance(profile, sensor_data, all_data)
        scores['technical_performance'] = tech_score
        
        if tech_score >= 0.7:
            strengths.append(f"Good technical performance ({tech_score:.2f})")
        elif tech_score < 0.5:
            weaknesses.append(f"Technical performance issues ({tech_score:.2f})")
            recommendations.append("Check sensor calibration and maintenance")
        
        # Calculate overall placement score
        placement_score = sum(scores[criterion] * weight 
                            for criterion, weight in self.criteria_weights.items())
        placement_score *= 100  # Convert to 0-100 scale
        
        # Determine optimality and priority
        is_optimal = placement_score >= 70
        if placement_score >= 80:
            priority_level = "HIGH"  # High priority to maintain
        elif placement_score >= 60:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"  # Low priority - needs major improvements
        
        # Add default recommendation if none exist
        if not recommendations:
            recommendations.append("Sensor placement is optimal - maintain current configuration")
        
        return SensorRecommendation(
            sensor_id=sensor_id,
            location_id=profile['location_id'],
            latitude=profile['latitude'],
            longitude=profile['longitude'],
            city=profile['city'],
            placement_score=placement_score,
            is_optimal=is_optimal,
            priority_level=priority_level,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            technical_details=scores
        )
    
    def _assess_data_quality(self, profile: Dict, sensor_data: pd.DataFrame) -> float:
        """Assess data quality based on completeness and consistency"""
        
        # Data completeness (40%)
        completeness_score = profile['data_completeness']
        
        # Temporal consistency (35%)
        temporal_score = profile['temporal_consistency']
        
        # Data volume (25%) - more readings generally better
        volume_score = min(profile['total_readings'] / 1000, 1.0)  # Cap at 1000 readings
        
        return (completeness_score * 0.4 + temporal_score * 0.35 + volume_score * 0.25)
    
    def _assess_spatial_coverage(self, profile: Dict, all_profiles: Dict) -> float:
        """
        Improved spatial score that accounts for redundancy and under-coverage.
        Uses DBSCAN clustering + distance factor. Robust to missing IDs.
        """
        # Build lists of valid sensor ids and coords (skip entries with missing coords)
        sensor_ids = []
        coords = []
        for sid, p in all_profiles.items():
            lat = p.get('latitude')
            lon = p.get('longitude')
            if pd.isna(lat) or pd.isna(lon):
                continue
            sensor_ids.append(sid)
            coords.append((lat, lon))

        # If few sensors, return good score
        if len(coords) < 2:
            return 1.0

        coords_arr = np.array(coords, dtype=float)

        # Scale coords for clustering (works with latitude/longitude)
        try:
            scaled = self.scaler.fit_transform(coords_arr)
            labels = self.clustering_model.fit_predict(scaled)
        except Exception:
            # If clustering fails for any reason, fallback to simple distance-based score
            labels = np.full(len(coords_arr), -1)

        # Try to find this sensor's index in sensor_ids via sensor_id
        sensor_idx = None
        sid_self = profile.get('sensor_id')
        if sid_self is not None:
            try:
                sensor_idx = sensor_ids.index(sid_self)
            except ValueError:
                sensor_idx = None

        # Fallback: match by location_id if sensor_id not found
        if sensor_idx is None:
            loc_id = profile.get('location_id')
            for i, sid in enumerate(sensor_ids):
                if all_profiles[sid].get('location_id') == loc_id:
                    sensor_idx = i
                    break

        # Another fallback: pick nearest coordinate match
        if sensor_idx is None:
            # compute distances to coords and pick the closest to profile lat/lon
            p_lat = profile.get('latitude')
            p_lon = profile.get('longitude')
            if pd.isna(p_lat) or pd.isna(p_lon):
                return 0.6  # unknown position -> penalize mildly
            dists = []
            for lat, lon in coords_arr:
                dists.append(self._haversine_distance(p_lat, p_lon, lat, lon))
            if len(dists) == 0:
                return 0.6
            sensor_idx = int(np.argmin(dists))

        # Now compute cluster_penalty
        sensor_cluster = labels[sensor_idx] if len(labels) > sensor_idx else -1
        if sensor_cluster == -1:
            cluster_penalty = 0.8  # outlier -> fills gap
        else:
            cluster_size = int((labels == sensor_cluster).sum())
            if cluster_size > 5:
                cluster_penalty = 0.4
            elif cluster_size > 2:
                cluster_penalty = 0.7
            else:
                cluster_penalty = 1.0

        # Compute min distance to any other sensor (use all_profiles)
        distances = [
            self._haversine_distance(profile['latitude'], profile['longitude'],
                                    other['latitude'], other['longitude'])
            for sid, other in all_profiles.items()
            if sid != profile.get('sensor_id') and not pd.isna(other.get('latitude')) and not pd.isna(other.get('longitude'))
        ]
        min_distance = min(distances) if distances else 10.0
        distance_factor = 1.0 if min_distance > 5 else 0.6

        # Weighted final score (0-1)
        return float(cluster_penalty * 0.6 + distance_factor * 0.4)


    
    def _assess_environmental_context(self, profile: Dict, sensor_data: pd.DataFrame) -> float:
        """Assess environmental context suitability"""
        
        score = 0.5  # Base score
        
        # Traffic context (good for urban monitoring)
        if profile['traffic_level'] in ['high', 'medium']:
            score += 0.15
        
        # Industry context (important for pollution monitoring)  
        if profile['industry_presence'] in ['high', 'medium']:
            score += 0.15
        
        # Check for reasonable pollution readings
        pollutant_stats = profile['pollutant_stats']
        
        if 'P2' in pollutant_stats:
            p2_mean = pollutant_stats['P2']['mean']
            if 5 <= p2_mean <= 100:  # Reasonable PM2.5 range
                score += 0.1
            elif p2_mean > 200:  # Very high - might indicate local interference
                score -= 0.1
        
        # Check data variability (too constant suggests sensor issues)
        if 'P1' in pollutant_stats:
            p1_std = pollutant_stats['P1']['std']
            p1_mean = pollutant_stats['P1']['mean']
            if p1_mean > 0:
                cv = p1_std / p1_mean
                if 0.1 <= cv <= 2.0:  # Reasonable variability
                    score += 0.1
        
        # Altitude consideration
        if 1000 <= profile.get('altitude', 1500) <= 2500:  # Reasonable for Kenya
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_technical_performance(self, profile: Dict, sensor_data: pd.DataFrame, 
                                    all_data: pd.DataFrame) -> float:
        """Assess technical performance compared to network average"""
        
        # Sensor type reliability
        type_score = 0.7  # Default
        if profile['sensor_type'] in ['pms5003', 'sds011']:  # Known good sensors
            type_score = 0.9
        elif profile['sensor_type'] == 'unknown':
            type_score = 0.4
        
        # Manufacturer reliability
        manuf_score = 0.7  # Default
        if profile['manufacturer'] in ['PlanTower', 'Nova Fitness']:
            manuf_score = 0.9
        
        # Compare readings with network average (representativeness)
        repr_score = self._calculate_representativeness(sensor_data, all_data)
        
        return (type_score * 0.3 + manuf_score * 0.2 + repr_score * 0.5)
    
    def _calculate_representativeness(self, sensor_data: pd.DataFrame, all_data: pd.DataFrame) -> float:
        """How representative are this sensor's readings of the broader network"""
        
        scores = []
        
        for pollutant in ['P1', 'P2', 'P0']:
            if pollutant in sensor_data.columns and pollutant in all_data.columns:
                sensor_mean = sensor_data[pollutant].mean()
                network_mean = all_data[pollutant].mean()
                
                if pd.notna(sensor_mean) and pd.notna(network_mean) and network_mean > 0:
                    relative_diff = abs(sensor_mean - network_mean) / network_mean
                    score = max(0, 1 - relative_diff)  # Closer to network mean = better
                    scores.append(score)
        
        return np.mean(scores) if scores else 0.5
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return float('inf')
        
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        return R * 2 * np.arcsin(np.sqrt(a))

def generate_comprehensive_report(recommendations: List[SensorRecommendation]) -> None:
    """Generate a comprehensive recommendation report"""
    
    print("\n" + "="*80)
    print("🎯 SENSOR PLACEMENT RECOMMENDATION SYSTEM REPORT")
    print("="*80)
    
    total_sensors = len(recommendations)
    optimal_sensors = sum(1 for r in recommendations if r.is_optimal)
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   Total sensors analyzed: {total_sensors}")
    print(f"   Optimally placed: {optimal_sensors} ({optimal_sensors/total_sensors*100:.1f}%)")
    print(f"   Need optimization: {total_sensors - optimal_sensors} ({(total_sensors-optimal_sensors)/total_sensors*100:.1f}%)")
    
    # Performance distribution
    high_priority = sum(1 for r in recommendations if r.priority_level == "HIGH")
    medium_priority = sum(1 for r in recommendations if r.priority_level == "MEDIUM")
    low_priority = sum(1 for r in recommendations if r.priority_level == "LOW")
    
    print(f"\n🏆 PRIORITY DISTRIBUTION:")
    print(f"   High Priority (Maintain): {high_priority} sensors")
    print(f"   Medium Priority (Monitor): {medium_priority} sensors") 
    print(f"   Low Priority (Optimize): {low_priority} sensors")
    
    avg_score = np.mean([r.placement_score for r in recommendations])
    print(f"\n📈 NETWORK PERFORMANCE:")
    print(f"   Average placement score: {avg_score:.1f}/100")
    
    print(f"\n🏅 TOP PERFORMING SENSORS:")
    for i, rec in enumerate(recommendations[:5]):
        print(f"   {i+1}. Sensor {rec.sensor_id} ({rec.city}) - Score: {rec.placement_score:.1f}")
    
    print(f"\n⚠️  SENSORS REQUIRING ATTENTION:")
    bottom_sensors = [r for r in recommendations if not r.is_optimal]
    for i, rec in enumerate(bottom_sensors[:3]):
        print(f"   {i+1}. Sensor {rec.sensor_id} ({rec.city}) - Score: {rec.placement_score:.1f}")
    
    print(f"\n📋 DETAILED SENSOR ASSESSMENTS:")
    print("-" * 80)
    
    for i, rec in enumerate(recommendations):
        status = f"✅ OPTIMAL ({rec.priority_level})" if rec.is_optimal else f"❌ NEEDS WORK ({rec.priority_level})"
        
        print(f"\n{i+1}. SENSOR {rec.sensor_id} | {rec.city} | {status}")
        print(f"   📍 Location: ({rec.latitude:.4f}, {rec.longitude:.4f})")
        print(f"   🎯 Placement Score: {rec.placement_score:.1f}/100")
        
        print(f"   📊 Component Scores:")
        for metric, score in rec.technical_details.items():
            print(f"      • {metric.replace('_', ' ').title()}: {score:.3f}")
        
        if rec.strengths:
            print(f"   ✅ Strengths:")
            for strength in rec.strengths:
                print(f"      • {strength}")
        
        if rec.weaknesses:
            print(f"   ❌ Issues:")
            for weakness in rec.weaknesses:
                print(f"      • {weakness}")
        
        if rec.recommendations:
            print(f"   💡 Recommendations:")
            for recommendation in rec.recommendations:
                print(f"      • {recommendation}")
    
    print(f"\n" + "="*80)
    print("📋 SUMMARY RECOMMENDATIONS:")
    print("="*80)
    
    if optimal_sensors >= total_sensors * 0.8:
        print("🎉 EXCELLENT: Your sensor network is well-optimized!")
    elif optimal_sensors >= total_sensors * 0.6:
        print("👍 GOOD: Most sensors are well-placed, minor optimizations needed.")
    else:
        print("⚠️  ATTENTION NEEDED: Significant improvements required for optimal coverage.")
    
    print(f"\n🔧 PRIORITY ACTIONS:")
    action_count = 0
    for rec in recommendations:
        if not rec.is_optimal and action_count < 5:
            print(f"   {action_count + 1}. Sensor {rec.sensor_id}: {rec.recommendations[0]}")
            action_count += 1

# Main analysis function
def analyze_sensor_network(df: pd.DataFrame) -> List[SensorRecommendation]:
    """
    Main function to analyze your sensor network and get recommendations
    """
    system = SensorPlacementRecommendationSystem()
    recommendations = system.analyze_all_sensors(df)
    generate_comprehensive_report(recommendations)
    
    # Save results to CSV
    results_data = []
    for rec in recommendations:
        results_data.append({
            'sensor_id': rec.sensor_id,
            'location_id': rec.location_id, 
            'city': rec.city,
            'latitude': rec.latitude,
            'longitude': rec.longitude,
            'placement_score': rec.placement_score,
            'is_optimal': rec.is_optimal,
            'priority_level': rec.priority_level,
            'data_quality_score': rec.technical_details.get('data_quality', 0),
            'spatial_coverage_score': rec.technical_details.get('spatial_coverage', 0),
            'environmental_context_score': rec.technical_details.get('environmental_context', 0),
            'temporal_reliability_score': rec.technical_details.get('temporal_reliability', 0),
            'technical_performance_score': rec.technical_details.get('technical_performance', 0),
            'strengths': '; '.join(rec.strengths),
            'weaknesses': '; '.join(rec.weaknesses),
            'recommendations': '; '.join(rec.recommendations)
        })
    
    results_df = pd.DataFrame(results_data)
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    filename = f"sensor_placement_recommendations_{timestamp}.csv"
    results_df.to_csv(filename, index=False)
    print(f"📁 Results saved to: {filename}")
    
    return recommendations

# Example usage
if __name__ == "__main__":
    # Load your data
    df = pd.read_csv("air_quality_kenya_all_20250910_164831.csv")
    
    # Run analysis
    recommendations = analyze_sensor_network(df)
    
    print("🚀 Load your CSV data and call: analyze_sensor_network(df)")