import math
from typing import Dict, List, Tuple
from datetime import datetime

class SafetyScorer:
    """
    Comprehensive safety scoring system for route evaluation
    considering weather, traffic, road conditions, and historical data
    """
    
    # Risk weights for different factors (total = 1.0)
    RISK_WEIGHTS = {
        'weather': 0.25,
        'traffic': 0.20,
        'road_condition': 0.15,
        'visibility': 0.15,
        'incident_history': 0.15,
        'time_of_day': 0.10
    }
    
    # Weather risk scores (0-100, higher = more dangerous)
    WEATHER_RISKS = {
        'clear': 10,
        'cloudy': 15,
        'fog': 60,
        'light_rain': 35,
        'rain': 50,
        'heavy_rain': 75,
        'snow': 80,
        'ice': 95,
        'hail': 85
    }
    
    # Traffic congestion risk scores
    TRAFFIC_RISKS = {
        'light': 15,
        'moderate': 35,
        'heavy': 60,
        'standstill': 80
    }
    
    # Road condition risk scores
    ROAD_CONDITION_RISKS = {
        'dry': 10,
        'wet': 40,
        'standing_water': 65,
        'snow_covered': 75,
        'icy': 90,
        'construction': 55
    }
    
    def calculate_route_safety_score(self, route_data: Dict) -> Dict:
        """
        Calculate comprehensive safety score for a route
        Returns score 0-100 (100 = safest)
        """
        
        # Calculate individual risk components
        weather_risk = self._calculate_weather_risk(route_data.get('weather', {}))
        traffic_risk = self._calculate_traffic_risk(route_data.get('traffic', {}))
        road_risk = self._calculate_road_condition_risk(route_data.get('road_conditions', {}))
        visibility_risk = self._calculate_visibility_risk(route_data.get('weather', {}))
        incident_risk = self._calculate_incident_history_risk(route_data.get('incident_history', {}))
        time_risk = self._calculate_time_of_day_risk(route_data.get('departure_time', ''))
        
        # Weighted average of all risks
        total_risk = (
            weather_risk * self.RISK_WEIGHTS['weather'] +
            traffic_risk * self.RISK_WEIGHTS['traffic'] +
            road_risk * self.RISK_WEIGHTS['road_condition'] +
            visibility_risk * self.RISK_WEIGHTS['visibility'] +
            incident_risk * self.RISK_WEIGHTS['incident_history'] +
            time_risk * self.RISK_WEIGHTS['time_of_day']
        )
        
        # Convert risk to safety score (0-100, higher is safer)
        safety_score = max(0, min(100, 100 - total_risk))
        
        # Determine safety level
        safety_level = self._get_safety_level(safety_score)
        
        # Get specific hazards
        hazards = self._identify_hazards(route_data)
        
        # Get recommendations
        recommendations = self._get_safety_recommendations(
            weather_risk, traffic_risk, road_risk, visibility_risk, time_risk, hazards
        )
        
        return {
            'safety_score': round(safety_score, 1),
            'safety_level': safety_level,
            'risk_breakdown': {
                'weather_risk': round(weather_risk, 1),
                'traffic_risk': round(traffic_risk, 1),
                'road_condition_risk': round(road_risk, 1),
                'visibility_risk': round(visibility_risk, 1),
                'incident_history_risk': round(incident_risk, 1),
                'time_of_day_risk': round(time_risk, 1)
            },
            'identified_hazards': hazards,
            'safety_recommendations': recommendations,
            'estimated_incident_probability': self._calculate_incident_probability(total_risk),
            'driver_alert_level': self._get_alert_level(safety_score)
        }
    
    def _calculate_weather_risk(self, weather_data: Dict) -> float:
        """
        Calculate risk based on weather conditions
        """
        condition = weather_data.get('conditions', 'clear').lower()
        base_risk = self.WEATHER_RISKS.get(condition, 50)
        
        # Adjust for precipitation intensity
        precip_intensity = weather_data.get('precipitation_intensity', 0)
        if precip_intensity > 0.5:
            base_risk += 15
        elif precip_intensity > 0.2:
            base_risk += 10
        
        # Adjust for wind speed
        wind_speed = weather_data.get('wind_speed_mph', 0)
        if wind_speed > 30:
            base_risk += 20
        elif wind_speed > 20:
            base_risk += 10
        
        # Temperature extremes
        temp = weather_data.get('temperature_f', 70)
        if temp < 32:  # Freezing conditions
            base_risk += 15
        elif temp > 100:  # Extreme heat
            base_risk += 5
        
        return min(100, base_risk)
    
    def _calculate_traffic_risk(self, traffic_data: Dict) -> float:
        """
        Calculate risk based on traffic conditions
        """
        congestion = traffic_data.get('congestion_level', 'light').lower()
        base_risk = self.TRAFFIC_RISKS.get(congestion, 35)
        
        # Adjust for incident count
        incidents = traffic_data.get('incidents', 0)
        base_risk += incidents * 10
        
        # Adjust for average speed vs speed limit
        avg_speed = traffic_data.get('average_speed_mph', 55)
        speed_limit = traffic_data.get('speed_limit_mph', 65)
        
        if avg_speed < speed_limit * 0.5:  # Very slow traffic
            base_risk += 20
        elif avg_speed > speed_limit:  # Speeding traffic
            base_risk += 15
        
        return min(100, base_risk)
    
    def _calculate_road_condition_risk(self, road_data: Dict) -> float:
        """
        Calculate risk based on road conditions
        """
        condition = road_data.get('surface_condition', 'dry').lower()
        base_risk = self.ROAD_CONDITION_RISKS.get(condition, 30)
        
        # Adjust for construction zones
        if road_data.get('construction_zones', 0) > 0:
            base_risk += 20
        
        # Adjust for road type
        road_type = road_data.get('road_type', 'highway').lower()
        if road_type == 'mountain':
            base_risk += 25
        elif road_type == 'rural':
            base_risk += 15
        elif road_type == 'urban':
            base_risk += 10
        
        return min(100, base_risk)
    
    def _calculate_visibility_risk(self, weather_data: Dict) -> float:
        """
        Calculate risk based on visibility
        """
        visibility = weather_data.get('visibility_miles', 10)
        
        if visibility < 0.25:
            return 95  # Extremely dangerous
        elif visibility < 0.5:
            return 80
        elif visibility < 1:
            return 60
        elif visibility < 3:
            return 40
        elif visibility < 5:
            return 25
        elif visibility < 10:
            return 15
        else:
            return 5
    
    def _calculate_incident_history_risk(self, history_data: Dict) -> float:
        """
        Calculate risk based on historical incident data
        """
        # Average incidents per day on this route
        avg_incidents = history_data.get('avg_daily_incidents', 0)
        
        if avg_incidents > 5:
            base_risk = 80
        elif avg_incidents > 3:
            base_risk = 60
        elif avg_incidents > 1:
            base_risk = 40
        elif avg_incidents > 0.5:
            base_risk = 25
        else:
            base_risk = 10
        
        # Adjust for severity of past incidents
        severe_incidents = history_data.get('severe_incidents_last_month', 0)
        base_risk += severe_incidents * 5
        
        return min(100, base_risk)
    
    def _calculate_time_of_day_risk(self, departure_time: str) -> float:
        """
        Calculate risk based on time of day
        """
        try:
            hour = datetime.fromisoformat(departure_time).hour
        except:
            hour = 12  # Default to noon if parsing fails
        
        # Risk by hour (0-23)
        risk_by_hour = {
            0: 60, 1: 65, 2: 70, 3: 70, 4: 65, 5: 50,  # Late night/early morning
            6: 40, 7: 45, 8: 50, 9: 35, 10: 25, 11: 20,  # Morning
            12: 20, 13: 20, 14: 25, 15: 30, 16: 40, 17: 50,  # Afternoon/evening rush
            18: 55, 19: 50, 20: 45, 21: 40, 22: 45, 23: 55  # Evening/night
        }
        
        return risk_by_hour.get(hour, 35)
    
    def _get_safety_level(self, safety_score: float) -> str:
        """
        Convert numerical score to safety level
        """
        if safety_score >= 90:
            return "Excellent"
        elif safety_score >= 75:
            return "Good"
        elif safety_score >= 60:
            return "Fair"
        elif safety_score >= 40:
            return "Poor"
        else:
            return "Hazardous"
    
    def _identify_hazards(self, route_data: Dict) -> List[Dict]:
        """
        Identify specific hazards on the route
        """
        hazards = []
        
        weather = route_data.get('weather', {})
        if weather.get('conditions', '').lower() in ['heavy_rain', 'snow', 'ice']:
            hazards.append({
                'type': 'weather',
                'severity': 'high',
                'description': f"Dangerous weather: {weather.get('conditions')}"
            })
        
        if weather.get('visibility_miles', 10) < 1:
            hazards.append({
                'type': 'visibility',
                'severity': 'high',
                'description': f"Low visibility: {weather.get('visibility_miles')} miles"
            })
        
        traffic = route_data.get('traffic', {})
        if traffic.get('incidents', 0) > 0:
            hazards.append({
                'type': 'traffic',
                'severity': 'medium',
                'description': f"{traffic.get('incidents')} active incidents on route"
            })
        
        # Check for specific hazard zones
        hazard_zones = route_data.get('hazard_zones', [])
        for zone in hazard_zones:
            hazards.append({
                'type': zone.get('hazard_type', 'unknown'),
                'severity': zone.get('severity', 'medium'),
                'description': zone.get('description', 'Hazard zone ahead'),
                'location': zone.get('location', {})
            })
        
        return hazards
    
    def _get_safety_recommendations(self, weather_risk: float, traffic_risk: float,
                                   road_risk: float, visibility_risk: float,
                                   time_risk: float, hazards: List) -> List[str]:
        """
        Generate specific safety recommendations
        """
        recommendations = []
        
        if weather_risk > 60:
            recommendations.append("Reduce speed by 10-15 mph in current weather conditions")
            recommendations.append("Increase following distance to 6+ seconds")
        
        if visibility_risk > 50:
            recommendations.append("Use low beam headlights and fog lights if equipped")
            recommendations.append("Consider delaying departure until visibility improves")
        
        if traffic_risk > 60:
            recommendations.append("Allow extra time for journey due to congestion")
            recommendations.append("Stay alert for sudden stops in heavy traffic")
        
        if road_risk > 60:
            recommendations.append("Exercise extreme caution on road surface")
            recommendations.append("Avoid sudden braking or acceleration")
        
        if time_risk > 50:
            recommendations.append("Take regular breaks to combat fatigue")
            recommendations.append("Ensure proper vehicle lighting for night driving")
        
        # Add hazard-specific recommendations
        for hazard in hazards:
            if hazard['severity'] == 'high':
                recommendations.append(f"HIGH ALERT: {hazard['description']}")
        
        if not recommendations:
            recommendations.append("Conditions are favorable for safe driving")
        
        return recommendations[:5]  # Limit to top 5 most important
    
    def _calculate_incident_probability(self, total_risk: float) -> float:
        """
        Estimate probability of incident based on risk score
        """
        # Simple exponential model for incident probability
        # Low risk (20) = ~1% chance, High risk (80) = ~15% chance
        probability = (math.exp(total_risk / 50) - 1) / 10
        return min(25, round(probability, 1))  # Cap at 25% for display
    
    def _get_alert_level(self, safety_score: float) -> str:
        """
        Determine driver alert level
        """
        if safety_score < 40:
            return "RED - High Risk"
        elif safety_score < 60:
            return "YELLOW - Moderate Risk"
        else:
            return "GREEN - Low Risk"
    
    def compare_routes_safety(self, routes: List[Dict]) -> List[Dict]:
        """
        Compare safety across multiple routes
        """
        results = []
        
        for route in routes:
            safety_analysis = self.calculate_route_safety_score(route)
            results.append({
                'route_id': route.get('route_id'),
                'route_name': route.get('name', 'Unknown'),
                'safety_score': safety_analysis['safety_score'],
                'safety_level': safety_analysis['safety_level'],
                'alert_level': safety_analysis['driver_alert_level'],
                'top_hazards': safety_analysis['identified_hazards'][:2],  # Top 2 hazards
                'incident_probability': safety_analysis['estimated_incident_probability']
            })
        
        # Sort by safety score (highest first)
        results.sort(key=lambda x: x['safety_score'], reverse=True)
        
        # Add ranking
        for i, result in enumerate(results):
            result['safety_rank'] = i + 1
        
        return results