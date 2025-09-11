import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

@dataclass
class LocationRecommendation:
    location_id: int
    city: str
    latitude: float
    longitude: float
    pms_sensor_id: int
    dht_sensor_id: Optional[int]
    placement_score: float  # 0-100
    is_optimal: bool
    priority_level: str  # "HIGH", "MEDIUM", "LOW"
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    technical_details: Dict

class EnhancedSensorPlacementRecommendationSystem:
    """
    Enhanced recommendation system for merged sensor data
    Analyzes complete sensor stations (PMS + DHT) at each location
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(contamination=0.2, random_state=42)
        
        # Updated criteria weights for merged sensor analysis
        self.criteria_weights = {
            'data_quality': 0.30,        # More important with merged sensors
            'spatial_coverage': 0.25,    # Critical for network optimization
            'sensor_completeness': 0.20, # Both PMS and DHT working
            'temporal_consistency': 0.15, # 48hr coverage analysis
            'measurement_reliability': 0.10 # Data accuracy and stability
        }
    
    def analyze_all_locations(self, df: pd.DataFrame) -> List[LocationRecommendation]:
        """
        Main function: Analyze all sensor locations and provide recommendations
        """
        print("🔍 Starting enhanced sensor location analysis...")
        print(f"📊 Analyzing {df['location_id'].nunique()} locations with {len(df):,} total readings")
        print(f"📅 Data timespan: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Create location profiles
        location_profiles = self._create_location_profiles(df)
        
        # Run analysis for each location
        recommendations = []
        
        for i, (location_id, profile) in enumerate(location_profiles.items()):
            print(f"🔬 Analyzing location {location_id} - {profile['city']} ({i+1}/{len(location_profiles)})...")
            
            # Get location data
            location_data = df[df['location_id'] == location_id].copy()
            
            # Run comprehensive analysis
            recommendation = self._analyze_single_location(
                location_id, profile, location_data, df, location_profiles
            )
            
            recommendations.append(recommendation)
        
        # Sort by placement score
        recommendations.sort(key=lambda x: x.placement_score, reverse=True)
        
        print("✅ Enhanced analysis complete!")
        return recommendations
    
    def _create_location_profiles(self, df: pd.DataFrame) -> Dict:
        """Create comprehensive profiles for each sensor location"""
        
        profiles = {}
        
        for location_id in df['location_id'].unique():
            location_data = df[df['location_id'] == location_id].copy()
            
            if len(location_data) == 0:
                continue
            
            # Basic location info
            first_record = location_data.iloc[0]
            
            # Time analysis
            location_data['timestamp'] = pd.to_datetime(location_data['timestamp'])
            location_data = location_data.sort_values('timestamp')
            
            # Create comprehensive profile
            profile = {
                # Location identifiers
                'location_id': location_id,
                'city': first_record['city'],
                'country': first_record['country'],
                'latitude': first_record['latitude'],
                'longitude': first_record['longitude'],
                'altitude': first_record['altitude'],
                
                # Sensor configuration
                'pms_sensor_id': first_record['pms_sensor_id'],
                'pms_sensor_type': first_record['pms_sensor_type'],
                'pms_manufacturer': first_record['pms_manufacturer'],
                'dht_sensor_id': first_record['dht_sensor_id'] if pd.notna(first_record['dht_sensor_id']) else None,
                'dht_sensor_type': first_record['dht_sensor_type'] if pd.notna(first_record['dht_sensor_type']) else None,
                'dht_manufacturer': first_record['dht_manufacturer'] if pd.notna(first_record['dht_manufacturer']) else None,
                
                # Data volume and coverage
                'total_readings': len(location_data),
                'time_span_hours': (location_data['timestamp'].max() - location_data['timestamp'].min()).total_seconds() / 3600,
                'unique_hours': len(location_data['timestamp'].dt.floor('H').unique()),
                'unique_days': len(location_data['timestamp'].dt.date.unique()),
                
                # Sensor data completeness
                'pms_completeness': self._calculate_sensor_completeness(location_data, ['P1', 'P2', 'P0']),
                'dht_completeness': self._calculate_sensor_completeness(location_data, ['humidity', 'temperature']),
                
                # Measurement statistics
                'pollutant_stats': self._calculate_enhanced_pollutant_stats(location_data),
                'environmental_stats': self._calculate_environmental_stats(location_data),
                
                # Data quality metrics
                'temporal_consistency': self._calculate_enhanced_temporal_consistency(location_data),
                'measurement_stability': self._calculate_measurement_stability(location_data),
                
                # Coverage analysis
                'hour_coverage': self._calculate_hour_coverage(location_data),
                'day_coverage': self._calculate_day_coverage(location_data),
            }
            
            profiles[location_id] = profile
        
        return profiles
    
    def _calculate_sensor_completeness(self, data: pd.DataFrame, columns: List[str]) -> Dict:
        """Calculate completeness for specific sensor measurements"""
        completeness = {}
        
        for col in columns:
            if col in data.columns:
                valid_readings = data[col].notna().sum()
                total_readings = len(data)
                completeness[col] = {
                    'completeness_rate': valid_readings / total_readings if total_readings > 0 else 0,
                    'valid_readings': valid_readings,
                    'total_readings': total_readings
                }
            else:
                completeness[col] = {'completeness_rate': 0, 'valid_readings': 0, 'total_readings': len(data)}
        
        # Overall completeness for this sensor type
        rates = [comp['completeness_rate'] for comp in completeness.values()]
        completeness['overall'] = np.mean(rates) if rates else 0
        
        return completeness
    
    def _calculate_enhanced_pollutant_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate enhanced statistics for pollutant measurements"""
        stats = {}
        
        pollutants = ['P1', 'P2', 'P0']
        
        for pollutant in pollutants:
            if pollutant in data.columns:
                values = data[pollutant].dropna()
                if len(values) > 0:
                    stats[pollutant] = {
                        'mean': values.mean(),
                        'median': values.median(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'q75': values.quantile(0.75),
                        'q25': values.quantile(0.25),
                        'coefficient_variation': values.std() / values.mean() if values.mean() > 0 else 0,
                        'completeness': len(values) / len(data),
                        'readings_count': len(values)
                    }
                    
                    # Check for realistic ranges (Kenya context)
                    if pollutant == 'P2':  # PM2.5
                        stats[pollutant]['within_normal_range'] = (5 <= stats[pollutant]['mean'] <= 150)
                    elif pollutant == 'P1':  # PM10
                        stats[pollutant]['within_normal_range'] = (10 <= stats[pollutant]['mean'] <= 200)
                    elif pollutant == 'P0':  # PM1
                        stats[pollutant]['within_normal_range'] = (3 <= stats[pollutant]['mean'] <= 100)
                else:
                    stats[pollutant] = {'mean': 0, 'readings_count': 0, 'completeness': 0, 'within_normal_range': False}
        
        return stats
    
    def _calculate_environmental_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate statistics for environmental measurements (humidity, temperature)"""
        stats = {}
        
        env_params = ['humidity', 'temperature']
        
        for param in env_params:
            if param in data.columns:
                values = data[param].dropna()
                if len(values) > 0:
                    stats[param] = {
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'completeness': len(values) / len(data),
                        'coefficient_variation': values.std() / values.mean() if values.mean() > 0 else 0
                    }
                    
                    # Check for realistic ranges (Kenya context)
                    if param == 'humidity':
                        stats[param]['within_normal_range'] = (20 <= stats[param]['mean'] <= 95)
                    elif param == 'temperature':
                        stats[param]['within_normal_range'] = (15 <= stats[param]['mean'] <= 40)
                else:
                    stats[param] = {'mean': 0, 'completeness': 0, 'within_normal_range': False}
        
        return stats
    
    def _calculate_enhanced_temporal_consistency(self, data: pd.DataFrame) -> Dict:
        """Calculate enhanced temporal consistency metrics"""
        if len(data) < 2:
            return {'overall_score': 0, 'details': 'Insufficient data'}
        
        data_sorted = data.sort_values('timestamp')
        
        # Calculate time intervals between readings
        time_diffs = data_sorted['timestamp'].diff().dropna()
        
        consistency_metrics = {
            'mean_interval_minutes': time_diffs.mean().total_seconds() / 60 if len(time_diffs) > 0 else 0,
            'std_interval_minutes': time_diffs.std().total_seconds() / 60 if len(time_diffs) > 0 else 0,
            'min_interval_minutes': time_diffs.min().total_seconds() / 60 if len(time_diffs) > 0 else 0,
            'max_interval_minutes': time_diffs.max().total_seconds() / 60 if len(time_diffs) > 0 else 0,
        }
        
        # Calculate consistency score
        if consistency_metrics['mean_interval_minutes'] > 0:
            cv = consistency_metrics['std_interval_minutes'] / consistency_metrics['mean_interval_minutes']
            consistency_score = max(0, 1 - cv/2)  # Lower CV = better consistency
        else:
            consistency_score = 0
        
        # Hour coverage consistency
        hourly_counts = data_sorted.groupby(data_sorted['timestamp'].dt.hour).size()
        hour_consistency = 1 - (hourly_counts.std() / hourly_counts.mean()) if hourly_counts.mean() > 0 else 0
        hour_consistency = max(0, min(1, hour_consistency))
        
        overall_score = (consistency_score * 0.6 + hour_consistency * 0.4)
        
        return {
            'overall_score': overall_score,
            'interval_consistency': consistency_score,
            'hour_consistency': hour_consistency,
            'details': consistency_metrics
        }
    
    def _calculate_measurement_stability(self, data: pd.DataFrame) -> Dict:
        """Calculate measurement stability over time"""
        stability_scores = {}
        
        key_measurements = ['P1', 'P2', 'P0', 'humidity', 'temperature']
        
        for measurement in key_measurements:
            if measurement in data.columns:
                values = data[measurement].dropna()
                if len(values) > 10:  # Need sufficient data
                    # Calculate rolling statistics to assess stability
                    rolling_mean = values.rolling(window=min(10, len(values)//3)).mean()
                    rolling_std = values.rolling(window=min(10, len(values)//3)).std()
                    
                    # Stability = consistency of rolling statistics
                    mean_stability = 1 - (rolling_mean.std() / rolling_mean.mean()) if rolling_mean.mean() > 0 else 0
                    std_stability = 1 - (rolling_std.std() / rolling_std.mean()) if rolling_std.mean() > 0 else 0
                    
                    stability_scores[measurement] = max(0, (mean_stability + std_stability) / 2)
                else:
                    stability_scores[measurement] = 0
        
        overall_stability = np.mean(list(stability_scores.values())) if stability_scores else 0
        
        return {
            'overall_stability': overall_stability,
            'individual_scores': stability_scores
        }
    
    def _calculate_hour_coverage(self, data: pd.DataFrame) -> Dict:
        """Calculate hour-by-hour coverage analysis"""
        hours_with_data = set(data['timestamp'].dt.hour)
        total_possible_hours = 24
        
        coverage_rate = len(hours_with_data) / total_possible_hours
        
        # Identify gaps
        all_hours = set(range(24))
        missing_hours = sorted(list(all_hours - hours_with_data))
        
        return {
            'coverage_rate': coverage_rate,
            'hours_covered': len(hours_with_data),
            'missing_hours': missing_hours,
            'has_night_coverage': any(h in hours_with_data for h in [22, 23, 0, 1, 2, 3, 4, 5]),
            'has_day_coverage': any(h in hours_with_data for h in [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]),
            'has_peak_hours': any(h in hours_with_data for h in [7, 8, 17, 18, 19])  # Rush hours
        }
    
    def _calculate_day_coverage(self, data: pd.DataFrame) -> Dict:
        """Calculate day-by-day coverage analysis"""
        unique_dates = data['timestamp'].dt.date.unique()
        days_covered = len(unique_dates)
        
        # Expected days (based on 48 hour data)
        expected_days = 3  # 48 hours should span 2-3 days
        
        return {
            'days_covered': days_covered,
            'coverage_completeness': min(1.0, days_covered / expected_days)
        }
    
    def _analyze_single_location(self, location_id: int, profile: Dict, 
                               location_data: pd.DataFrame, all_data: pd.DataFrame,
                               all_profiles: Dict) -> LocationRecommendation:
        """Comprehensive analysis of a single sensor location"""
        
        scores = {}
        strengths = []
        weaknesses = []
        recommendations = []
        
        # 1. Data Quality Analysis (30%)
        data_quality_score = self._assess_enhanced_data_quality(profile, location_data)
        scores['data_quality'] = data_quality_score
        
        if data_quality_score >= 0.85:
            strengths.append(f"Excellent data quality ({data_quality_score:.2f}) - highly reliable readings")
        elif data_quality_score >= 0.70:
            strengths.append(f"Good data quality ({data_quality_score:.2f})")
        elif data_quality_score >= 0.50:
            weaknesses.append(f"Moderate data quality ({data_quality_score:.2f}) - some reliability issues")
            recommendations.append("Monitor sensor maintenance and data transmission stability")
        else:
            weaknesses.append(f"Poor data quality ({data_quality_score:.2f}) - significant reliability issues")
            recommendations.append("URGENT: Investigate and fix data collection problems")
        
        # 2. Spatial Coverage Analysis (25%)
        spatial_score = self._assess_enhanced_spatial_coverage(profile, all_profiles)
        scores['spatial_coverage'] = spatial_score
        
        if spatial_score >= 0.80:
            strengths.append(f"Optimal spatial positioning ({spatial_score:.2f}) - excellent network coverage")
        elif spatial_score >= 0.65:
            strengths.append(f"Good spatial positioning ({spatial_score:.2f})")
        elif spatial_score >= 0.45:
            weaknesses.append(f"Suboptimal location ({spatial_score:.2f}) - limited coverage contribution")
            recommendations.append("Consider strategic relocation to improve network coverage")
        else:
            weaknesses.append(f"Poor spatial coverage ({spatial_score:.2f}) - redundant or poorly positioned")
            recommendations.append("HIGH PRIORITY: Relocate sensor to fill coverage gaps")
        
        # 3. Sensor Completeness Analysis (20%)
        completeness_score = self._assess_sensor_completeness(profile)
        scores['sensor_completeness'] = completeness_score
        
        if completeness_score >= 0.90:
            strengths.append(f"Complete sensor setup ({completeness_score:.2f}) - both PMS and DHT functioning")
        elif completeness_score >= 0.70:
            strengths.append(f"Good sensor completeness ({completeness_score:.2f})")
        else:
            weaknesses.append(f"Incomplete sensor setup ({completeness_score:.2f})")
            if profile['dht_sensor_id'] is None:
                recommendations.append("Add humidity/temperature sensor for complete environmental monitoring")
            else:
                recommendations.append("Fix non-functioning sensors for complete measurement capability")
        
        # 4. Temporal Consistency Analysis (15%)
        temporal_score = profile['temporal_consistency']['overall_score']
        scores['temporal_consistency'] = temporal_score
        
        if temporal_score >= 0.80:
            strengths.append(f"Excellent temporal reliability ({temporal_score:.2f})")
        elif temporal_score >= 0.60:
            strengths.append(f"Good temporal consistency ({temporal_score:.2f})")
        else:
            weaknesses.append(f"Poor temporal reliability ({temporal_score:.2f})")
            recommendations.append("Improve sensor uptime and data reporting frequency")
        
        # 5. Measurement Reliability Analysis (10%)
        reliability_score = self._assess_measurement_reliability(profile, location_data, all_data)
        scores['measurement_reliability'] = reliability_score
        
        if reliability_score >= 0.75:
            strengths.append(f"Reliable measurements ({reliability_score:.2f})")
        elif reliability_score < 0.50:
            weaknesses.append(f"Questionable measurement reliability ({reliability_score:.2f})")
            recommendations.append("Calibrate sensors and check for interference")
        
        # Calculate overall placement score
        placement_score = sum(scores[criterion] * weight 
                            for criterion, weight in self.criteria_weights.items())
        placement_score *= 100  # Convert to 0-100 scale
        
        # Determine optimality and priority
        is_optimal = placement_score >= 75  # Higher threshold for enhanced system
        if placement_score >= 85:
            priority_level = "HIGH"   # High priority to maintain
        elif placement_score >= 65:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"    # Needs significant improvements
        
        # Add coverage-specific recommendations
        hour_coverage = profile['hour_coverage']
        if not hour_coverage['has_peak_hours']:
            recommendations.append("Improve data collection during peak traffic hours (7-8am, 5-7pm)")
        if not hour_coverage['has_night_coverage']:
            recommendations.append("Ensure 24-hour monitoring capability for complete daily patterns")
        
        # Add default recommendation if none exist
        if not recommendations:
            recommendations.append("Location is well-optimized - maintain current sensor configuration")
        
        return LocationRecommendation(
            location_id=location_id,
            city=profile['city'],
            latitude=profile['latitude'],
            longitude=profile['longitude'],
            pms_sensor_id=profile['pms_sensor_id'],
            dht_sensor_id=profile['dht_sensor_id'],
            placement_score=placement_score,
            is_optimal=is_optimal,
            priority_level=priority_level,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            technical_details=scores
        )
    
    def _assess_enhanced_data_quality(self, profile: Dict, location_data: pd.DataFrame) -> float:
        """Enhanced data quality assessment for merged sensors"""
        
        # PMS sensor completeness (50%)
        pms_completeness = profile['pms_completeness']['overall']
        
        # DHT sensor completeness (30%)
        dht_completeness = profile['dht_completeness']['overall']
        
        # Temporal consistency (20%)
        temporal_score = profile['temporal_consistency']['overall_score']
        
        return (pms_completeness * 0.5 + dht_completeness * 0.3 + temporal_score * 0.2)
    
    def _assess_enhanced_spatial_coverage(self, profile: Dict, all_profiles: Dict) -> float:
        """Enhanced spatial coverage assessment"""
        
        # Calculate distances to all other locations
        distances = []
        for other_location, other_profile in all_profiles.items():
            if other_location == profile['location_id']:
                continue
            
            dist = self._haversine_distance(
                profile['latitude'], profile['longitude'],
                other_profile['latitude'], other_profile['longitude']
            )
            distances.append(dist)
        
        if not distances:
            return 1.0  # Only location
        
        min_distance = min(distances)
        avg_distance = np.mean(distances)
        
        # Enhanced scoring for Kenya's geography
        if min_distance < 5:     # Too close (< 5km)
            proximity_score = 0.4
        elif min_distance < 15:  # Close (5-15km)
            proximity_score = 0.7
        elif min_distance < 50:  # Good distance (15-50km) - ideal for Kenya
            proximity_score = 1.0
        elif min_distance < 100: # Far (50-100km)
            proximity_score = 0.8
        else:                    # Very far (>100km)
            proximity_score = 0.9
        
        # Average distance consideration
        if avg_distance < 25:
            avg_score = 0.6
        elif avg_distance < 75:
            avg_score = 1.0
        else:
            avg_score = 0.8
        
        # City coverage bonus
        city_bonus = 0
        cities_covered = {other_profile['city'] for other_profile in all_profiles.values()}
        if len(cities_covered) >= 8:  # Good city diversity
            city_bonus = 0.1
        
        return min(1.0, proximity_score * 0.6 + avg_score * 0.4 + city_bonus)
    
    def _assess_sensor_completeness(self, profile: Dict) -> float:
        """Assess completeness of sensor setup at location"""
        
        pms_score = profile['pms_completeness']['overall']
        dht_score = profile['dht_completeness']['overall']
        
        # Bonus for having both sensor types
        both_sensors_bonus = 0.1 if profile['dht_sensor_id'] is not None else 0
        
        # Weight: PMS is more critical (70%), DHT adds value (30%)
        completeness = pms_score * 0.7 + dht_score * 0.3 + both_sensors_bonus
        
        return min(1.0, completeness)
    
    def _assess_measurement_reliability(self, profile: Dict, location_data: pd.DataFrame, 
                                     all_data: pd.DataFrame) -> float:
        """Assess reliability and accuracy of measurements"""
        
        # Check if measurements are within expected ranges
        range_scores = []
        
        # Pollutant range checks
        pollutant_stats = profile['pollutant_stats']
        for pollutant in ['P1', 'P2', 'P0']:
            if pollutant in pollutant_stats:
                if pollutant_stats[pollutant]['within_normal_range']:
                    range_scores.append(1.0)
                else:
                    range_scores.append(0.3)  # Suspicious readings
        
        # Environmental parameter range checks
        env_stats = profile['environmental_stats']
        for param in ['humidity', 'temperature']:
            if param in env_stats:
                if env_stats[param]['within_normal_range']:
                    range_scores.append(1.0)
                else:
                    range_scores.append(0.3)
        
        range_score = np.mean(range_scores) if range_scores else 0.5
        
        # Measurement stability
        stability_score = profile['measurement_stability']['overall_stability']
        
        # Compare with network averages (representativeness)
        repr_score = self._calculate_network_representativeness(location_data, all_data)
        
        return (range_score * 0.4 + stability_score * 0.3 + repr_score * 0.3)
    
    
    
    def _calculate_network_representativeness(self, location_data: pd.DataFrame, 
                                            all_data: pd.DataFrame) -> float:
        """Calculate how representative this location's readings are of the network"""
        
        scores = []
        
        for measurement in ['P1', 'P2', 'P0', 'humidity', 'temperature']:
            if (measurement in location_data.columns and measurement in all_data.columns):
                location_mean = location_data[measurement].mean()
                network_mean = all_data[measurement].mean()
                
                if pd.notna(location_mean) and pd.notna(network_mean) and network_mean > 0:
                    relative_diff = abs(location_mean - network_mean) / network_mean
                    # Score: closer to network mean = better, but allow some variation
                    score = max(0, 1 - relative_diff) if relative_diff <= 1 else 0.2
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

def generate_enhanced_report(recommendations: List[LocationRecommendation]) -> None:
    """Generate enhanced comprehensive recommendation report"""
    
    print("\n" + "="*85)
    print("🎯 ENHANCED SENSOR LOCATION RECOMMENDATION SYSTEM REPORT")
    print("="*85)
    
    total_locations = len(recommendations)
    optimal_locations = sum(1 for r in recommendations if r.is_optimal)
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   Total locations analyzed: {total_locations}")
    print(f"   Optimally configured: {optimal_locations} ({optimal_locations/total_locations*100:.1f}%)")
    print(f"   Need optimization: {total_locations - optimal_locations} ({(total_locations-optimal_locations)/total_locations*100:.1f}%)")
    
    # Performance distribution
    high_priority = sum(1 for r in recommendations if r.priority_level == "HIGH")
    medium_priority = sum(1 for r in recommendations if r.priority_level == "MEDIUM")
    low_priority = sum(1 for r in recommendations if r.priority_level == "LOW")
    
    print(f"\n🏆 PRIORITY DISTRIBUTION:")
    print(f"   High Priority (Maintain): {high_priority} locations")
    print(f"   Medium Priority (Monitor): {medium_priority} locations") 
    print(f"   Low Priority (Optimize): {low_priority} locations")
    
    avg_score = np.mean([r.placement_score for r in recommendations])
    print(f"\n📈 NETWORK PERFORMANCE:")
    print(f"   Average placement score: {avg_score:.1f}/100")
    
    # Sensor configuration analysis
    complete_setups = sum(1 for r in recommendations if r.dht_sensor_id is not None)
    print(f"   Complete sensor setups (PMS+DHT): {complete_setups}/{total_locations} ({complete_setups/total_locations*100:.1f}%)")
    
    print(f"\n🏅 TOP PERFORMING LOCATIONS:")
    for i, rec in enumerate(recommendations[:5]):
        sensor_info = f"PMS:{rec.pms_sensor_id}"
        if rec.dht_sensor_id:
            sensor_info += f"+DHT:{rec.dht_sensor_id}"
        print(f"   {i+1}. Location {rec.location_id} ({rec.city}) - Score: {rec.placement_score:.1f} - {sensor_info}")
    
    print(f"\n⚠️  LOCATIONS REQUIRING ATTENTION:")
    attention_locations = [r for r in recommendations if not r.is_optimal]
    for i, rec in enumerate(attention_locations[:3]):
        print(f"   {i+1}. Location {rec.location_id} ({rec.city}) - Score: {rec.placement_score:.1f}")
    
    print(f"\n📋 DETAILED LOCATION ASSESSMENTS:")
    print("-" * 85)
    
    for i, rec in enumerate(recommendations):
        status = f"✅ OPTIMAL ({rec.priority_level})" if rec.is_optimal else f"❌ NEEDS WORK ({rec.priority_level})"
        
        print(f"\n{i+1}. LOCATION {rec.location_id} | {rec.city} | {status}")
        print(f"   📍 Coordinates: ({rec.latitude:.4f}, {rec.longitude:.4f})")
        print(f"   🎯 Placement Score: {rec.placement_score:.1f}/100")
        
        # Sensor configuration info
        sensor_config = f"PMS Sensor: {rec.pms_sensor_id}"
        if rec.dht_sensor_id:
            sensor_config += f" | DHT Sensor: {rec.dht_sensor_id}"
        else:
            sensor_config += " | DHT Sensor: Not configured"
        print(f"   🔧 {sensor_config}")
        
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
    
    print(f"\n" + "="*85)
    print("📋 NETWORK OPTIMIZATION RECOMMENDATIONS:")
    print("="*85)
    
    if optimal_locations >= total_locations * 0.8:
        print("🎉 EXCELLENT: Your sensor network is very well optimized!")
        print("   → Focus on maintaining current high-performing locations")
    elif optimal_locations >= total_locations * 0.6:
        print("👍 GOOD: Most locations are well-configured with room for improvement.")
        print("   → Address medium and low priority locations systematically")
    else:
        print("⚠️  ATTENTION NEEDED: Significant network optimization required.")
        print("   → Prioritize fixing low-performing locations immediately")
    
    print(f"\n🔧 IMMEDIATE ACTION ITEMS:")
    action_count = 0
    for rec in recommendations:
        if not rec.is_optimal and action_count < 5:
            print(f"   {action_count + 1}. Location {rec.location_id} ({rec.city}): {rec.recommendations[0]}")
            action_count += 1
    
    # Network coverage analysis
    cities = list(set(rec.city for rec in recommendations))
    print(f"\n🗺️  GEOGRAPHIC COVERAGE:")
    print(f"   Cities covered: {len(cities)} ({', '.join(sorted(cities))})")
    
    if len(cities) >= 10:
        print("   ✅ Excellent geographic diversity")
    elif len(cities) >= 6:
        print("   👍 Good geographic coverage")
    else:
        print("   ⚠️  Limited geographic diversity - consider expanding to more cities")

def analyze_enhanced_sensor_network(df: pd.DataFrame) -> List[LocationRecommendation]:
    """
    Main function to analyze your enhanced sensor network and get recommendations
    """
    print("🚀 Starting Enhanced Sensor Network Analysis...")
    print(f"📊 Dataset Overview:")
    print(f"   - Total records: {len(df):,}")
    print(f"   - Unique locations: {df['location_id'].nunique()}")
    print(f"   - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   - Cities: {', '.join(sorted(df['city'].unique()))}")
    
    system = EnhancedSensorPlacementRecommendationSystem()
    recommendations = system.analyze_all_locations(df)
    generate_enhanced_report(recommendations)
    
    # Save detailed results to CSV
    results_data = []
    for rec in recommendations:
        results_data.append({
            'location_id': rec.location_id,
            'city': rec.city,
            'latitude': rec.latitude,
            'longitude': rec.longitude,
            'pms_sensor_id': rec.pms_sensor_id,
            'dht_sensor_id': rec.dht_sensor_id if rec.dht_sensor_id else 'Not configured',
            'placement_score': rec.placement_score,
            'is_optimal': rec.is_optimal,
            'priority_level': rec.priority_level,
            'data_quality_score': rec.technical_details.get('data_quality', 0),
            'spatial_coverage_score': rec.technical_details.get('spatial_coverage', 0),
            'sensor_completeness_score': rec.technical_details.get('sensor_completeness', 0),
            'temporal_consistency_score': rec.technical_details.get('temporal_consistency', 0),
            'measurement_reliability_score': rec.technical_details.get('measurement_reliability', 0),
            'strengths': ' | '.join(rec.strengths),
            'weaknesses': ' | '.join(rec.weaknesses),
            'recommendations': ' | '.join(rec.recommendations)
        })
    
    results_df = pd.DataFrame(results_data)
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    filename = f"enhanced_sensor_recommendations_{timestamp}.csv"
    results_df.to_csv(filename, index=False)
    print(f"\n💾 Detailed results saved to: {filename}")
    
    return recommendations

def quick_network_summary(df: pd.DataFrame) -> None:
    """
    Quick summary of your network before running full analysis
    """
    print("📊 QUICK NETWORK SUMMARY:")
    print("=" * 50)
    
    print(f"📈 Data Volume:")
    print(f"   • Total readings: {len(df):,}")
    print(f"   • Locations: {df['location_id'].nunique()}")
    print(f"   • Time span: {(pd.to_datetime(df['timestamp']).max() - pd.to_datetime(df['timestamp']).min()).total_seconds() / 3600:.1f} hours")
    
    print(f"\n🔧 Sensor Configuration:")
    pms_sensors = df['pms_sensor_id'].nunique()
    dht_sensors = df['dht_sensor_id'].notna().sum() > 0
    print(f"   • PMS sensors: {pms_sensors}")
    print(f"   • DHT sensors available: {'Yes' if dht_sensors else 'No'}")
    
    print(f"\n📍 Geographic Coverage:")
    cities = df['city'].unique()
    print(f"   • Cities: {len(cities)} ({', '.join(sorted(cities))})")
    
    print(f"\n🌬️  Data Completeness:")
    for col in ['P1', 'P2', 'P0', 'humidity', 'temperature']:
        if col in df.columns:
            completeness = (df[col].notna().sum() / len(df)) * 100
            print(f"   • {col}: {completeness:.1f}% complete")
    
    print("\n✅ Ready for enhanced analysis!")


def compute_dynamic_scores(df, expected_interval="15min", max_distance_km=5):
    """
    Compute dynamic sensor scores:
    - Data Quality
    - Temporal Coverage
    - Spatial Coverage
    And combine into a Sensor Health Index (0–100).
    """

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    results = {}

    for loc, group in df.groupby("location_id"):
        scores = {}

        # ===============================
        # 1. DATA QUALITY SCORE
        # ===============================
        total_expected = len(group)
        missing_count = group.isnull().sum().sum()
        data_quality = 1 - (missing_count / (total_expected * len(group.columns)))
        scores["data_quality"] = max(0, min(1, data_quality))  # clamp 0–1

        # ===============================
        # 2. TEMPORAL COVERAGE SCORE
        # ===============================
        group_sorted = group.sort_values("timestamp")
        gaps = group_sorted["timestamp"].diff().dropna().dt.total_seconds() / 60.0  # minutes
        if len(gaps) > 0:
            avg_gap = gaps.mean()
            expected_gap = pd.Timedelta(expected_interval).total_seconds() / 60.0
            temporal_score = 1 - (avg_gap / (expected_gap * 2))  # tolerance factor
        else:
            temporal_score = 0
        scores["temporal_coverage"] = max(0, min(1, temporal_score))

        # ===============================
        # 3. SPATIAL COVERAGE SCORE
        # ===============================
        if "latitude" in group.columns and "longitude" in group.columns:
            lat, lon = group["latitude"].iloc[0], group["longitude"].iloc[0]
            if pd.notnull(lat) and pd.notnull(lon):
                # Check nearest neighbor distance
                others = df[(df["location_id"] != loc) & df["latitude"].notnull() & df["longitude"].notnull()]
                if not others.empty:
                    dists = np.sqrt((others["latitude"] - lat) ** 2 + (others["longitude"] - lon) ** 2)
                    min_dist = dists.min() * 111  # rough km conversion
                    spatial_score = min(1, max(0, min_dist / max_distance_km))
                else:
                    spatial_score = 1
            else:
                spatial_score = 0
        else:
            spatial_score = 0
        scores["spatial_coverage"] = spatial_score

        # ===============================
        # 4. COMPOSITE HEALTH INDEX
        # ===============================
        scores["sensor_health_index"] = round(
            (scores["data_quality"] * 0.4 +
             scores["temporal_coverage"] * 0.3 +
             scores["spatial_coverage"] * 0.3) * 100, 2
        )

        results[loc] = scores

    return pd.DataFrame(results).T.sort_values("sensor_health_index", ascending=False)


# Convenience function for your workflow
def run_complete_analysis(file_path: str):
    print(f"📂 Loading dataset: {file_path}")
    df = pd.read_csv(file_path)

    df['timestamp'] = pd.to_datetime(
        df['timestamp'],
        format="mixed",      
        errors="coerce",     
        utc=True             
    )
    bad_rows = df[df['timestamp'].isna()]
    if not bad_rows.empty:
        print("⚠️ Warning: Some timestamps could not be parsed:")
        print(bad_rows['timestamp'].unique()[:10])  

    df = df.sort_values(by=['location_id', 'timestamp']).reset_index(drop=True)

    recommendations = {
        "total_records": len(df),
        "time_span": f"{df['timestamp'].min()} → {df['timestamp'].max()}",
        "locations": df['location_id'].nunique(),
    }

    return recommendations


# Example usage
if __name__ == "__main__":

    df = pd.read_csv('air_quality_merged_kenya_all_drop_20250911_155137.csv')
    recommendations = analyze_enhanced_sensor_network(df)
    recommendations = run_complete_analysis('air_quality_merged_kenya_all_drop_20250911_155137.csv')

    dynamic_score = compute_dynamic_scores(df)
    print(dynamic_score)