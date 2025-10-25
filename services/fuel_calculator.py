import math
from typing import Dict, List, Tuple
import json

class FuelCalculator:
    """
    Advanced fuel calculation service considering multiple factors
    for accurate consumption estimates
    """
    
    # Base fuel consumption factors
    WEATHER_IMPACT = {
        'clear': 1.0,
        'rain': 1.08,      # 8% increase
        'light_rain': 1.04,
        'heavy_rain': 1.12,
        'snow': 1.15,      # 15% increase
        'fog': 1.05,
        'wind': 1.06
    }
    
    TRAFFIC_IMPACT = {
        'light': 1.0,
        'moderate': 1.15,   # 15% increase due to stop-and-go
        'heavy': 1.30,      # 30% increase
        'standstill': 1.45  # 45% increase - lots of idling
    }
    
    CARGO_WEIGHT_IMPACT = {
        # Impact per 1000 lbs of cargo
        'fuel_increase_per_1000_lbs': 0.05  # 5% per 1000 lbs
    }
    
    SPEED_EFFICIENCY = {
        # MPG multipliers based on speed ranges
        'under_25': 0.75,   # City driving, lots of stops
        '25_45': 0.90,      # Mixed driving
        '45_55': 1.0,       # Optimal efficiency
        '55_65': 0.95,      # Highway speed
        '65_75': 0.88,      # Higher speed, more drag
        'over_75': 0.80     # Significant efficiency loss
    }
    
    def calculate_fuel_consumption(self, route_data: Dict, vehicle_data: Dict) -> Dict:
        """
        Calculate detailed fuel consumption for a route
        """
        
        # Base MPG from vehicle data
        base_mpg = self._get_base_mpg(route_data, vehicle_data)
        
        # Apply all adjustment factors
        weather_factor = self._calculate_weather_impact(route_data.get('weather', {}))
        traffic_factor = self._calculate_traffic_impact(route_data.get('traffic', {}))
        cargo_factor = self._calculate_cargo_impact(vehicle_data.get('cargo_weight_lbs', 0))
        speed_factor = self._calculate_speed_impact(route_data.get('average_speed_mph', 55))
        elevation_factor = self._calculate_elevation_impact(route_data.get('elevation_gain_ft', 0))
        
        # Calculate adjusted MPG
        adjusted_mpg = base_mpg * weather_factor * traffic_factor * cargo_factor * speed_factor * elevation_factor
        
        # Calculate total fuel needed
        distance = route_data.get('distance_miles', 0)
        fuel_needed = distance / adjusted_mpg if adjusted_mpg > 0 else 0
        
        # Calculate cost (assuming $3.50 per gallon average)
        fuel_cost = fuel_needed * route_data.get('fuel_price_per_gallon', 3.50)
        
        # Calculate emissions (2.31 kg CO2 per liter, 3.785 liters per gallon)
        co2_emissions_kg = fuel_needed * 3.785 * 2.31
        
        return {
            'base_mpg': round(base_mpg, 2),
            'adjusted_mpg': round(adjusted_mpg, 2),
            'fuel_gallons_needed': round(fuel_needed, 2),
            'fuel_cost_usd': round(fuel_cost, 2),
            'co2_emissions_kg': round(co2_emissions_kg, 2),
            'efficiency_factors': {
                'weather_impact': round((1 - weather_factor) * 100, 1),
                'traffic_impact': round((1 - traffic_factor) * 100, 1),
                'cargo_impact': round((1 - cargo_factor) * 100, 1),
                'speed_impact': round((1 - speed_factor) * 100, 1),
                'elevation_impact': round((1 - elevation_factor) * 100, 1)
            },
            'optimization_suggestions': self._get_optimization_suggestions(
                weather_factor, traffic_factor, cargo_factor, speed_factor
            )
        }
    
    def _get_base_mpg(self, route_data: Dict, vehicle_data: Dict) -> float:
        """
        Get base MPG based on route type
        """
        distance = route_data.get('distance_miles', 50)
        city_percentage = route_data.get('city_driving_percentage', 50) / 100
        
        city_mpg = vehicle_data.get('mpg_city', 18)
        highway_mpg = vehicle_data.get('mpg_highway', 25)
        
        # Weighted average based on route composition
        return (city_mpg * city_percentage) + (highway_mpg * (1 - city_percentage))
    
    def _calculate_weather_impact(self, weather_data: Dict) -> float:
        """
        Calculate fuel impact from weather conditions
        """
        condition = weather_data.get('conditions', 'clear').lower()
        base_factor = self.WEATHER_IMPACT.get(condition, 1.0)
        
        # Additional factors
        wind_speed = weather_data.get('wind_speed_mph', 0)
        if wind_speed > 20:
            base_factor *= 1.05  # 5% additional for strong winds
        
        temperature = weather_data.get('temperature_f', 70)
        if temperature < 32:  # Cold weather
            base_factor *= 1.08  # 8% increase for cold engine
        elif temperature > 95:  # Hot weather
            base_factor *= 1.04  # 4% increase for AC use
        
        return 1 / base_factor  # Invert because we multiply MPG
    
    def _calculate_traffic_impact(self, traffic_data: Dict) -> float:
        """
        Calculate fuel impact from traffic conditions
        """
        congestion = traffic_data.get('congestion_level', 'light').lower()
        base_factor = self.TRAFFIC_IMPACT.get(congestion, 1.0)
        
        # Consider number of stops
        stop_count = traffic_data.get('estimated_stops', 0)
        if stop_count > 20:
            base_factor *= 1.10  # Additional 10% for frequent stops
        
        return 1 / base_factor
    
    def _calculate_cargo_impact(self, cargo_weight_lbs: int) -> float:
        """
        Calculate fuel impact from cargo weight
        """
        weight_factor = 1 + (cargo_weight_lbs / 1000) * self.CARGO_WEIGHT_IMPACT['fuel_increase_per_1000_lbs']
        return 1 / weight_factor
    
    def _calculate_speed_impact(self, average_speed_mph: float) -> float:
        """
        Calculate fuel efficiency based on speed
        """
        if average_speed_mph < 25:
            return self.SPEED_EFFICIENCY['under_25']
        elif average_speed_mph < 45:
            return self.SPEED_EFFICIENCY['25_45']
        elif average_speed_mph < 55:
            return self.SPEED_EFFICIENCY['45_55']
        elif average_speed_mph < 65:
            return self.SPEED_EFFICIENCY['55_65']
        elif average_speed_mph < 75:
            return self.SPEED_EFFICIENCY['65_75']
        else:
            return self.SPEED_EFFICIENCY['over_75']
    
    def _calculate_elevation_impact(self, elevation_gain_ft: float) -> float:
        """
        Calculate impact of elevation changes
        """
        # Rough estimate: 1% fuel increase per 100ft of climbing
        if elevation_gain_ft > 0:
            return 1 / (1 + elevation_gain_ft / 10000)
        return 1.0
    
    def _get_optimization_suggestions(self, weather_f: float, traffic_f: float, 
                                     cargo_f: float, speed_f: float) -> List[str]:
        """
        Generate specific suggestions to improve fuel efficiency
        """
        suggestions = []
        
        if weather_f < 0.92:
            suggestions.append("Consider delaying trip for better weather conditions if possible")
        
        if traffic_f < 0.85:
            suggestions.append("Route through heavy traffic - consider alternative times or routes")
        
        if cargo_f < 0.90:
            suggestions.append("Heavy cargo load - ensure proper tire pressure and consider load distribution")
        
        if speed_f < 0.90:
            suggestions.append("Maintain speeds between 45-65 mph for optimal fuel efficiency")
        elif speed_f > 1.0:
            suggestions.append("Current speed range is optimal for fuel efficiency")
        
        if not suggestions:
            suggestions.append("Route is well-optimized for fuel efficiency")
        
        return suggestions
    
    def compare_routes_fuel_efficiency(self, routes: List[Dict], vehicle_data: Dict) -> List[Dict]:
        """
        Compare multiple routes for fuel efficiency
        """
        results = []
        
        for route in routes:
            fuel_calc = self.calculate_fuel_consumption(route, vehicle_data)
            results.append({
                'route_id': route.get('route_id'),
                'route_name': route.get('name', 'Unknown'),
                'distance_miles': route.get('distance_miles'),
                'fuel_gallons': fuel_calc['fuel_gallons_needed'],
                'fuel_cost': fuel_calc['fuel_cost_usd'],
                'co2_emissions_kg': fuel_calc['co2_emissions_kg'],
                'efficiency_score': round(100 / fuel_calc['fuel_gallons_needed'] if fuel_calc['fuel_gallons_needed'] > 0 else 0, 1)
            })
        
        # Sort by efficiency
        results.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        # Add ranking
        for i, result in enumerate(results):
            result['efficiency_rank'] = i + 1
            if i == 0:
                result['savings_vs_worst'] = round(
                    results[-1]['fuel_cost'] - result['fuel_cost'], 2
                ) if len(results) > 1 else 0
        
        return results
    
    def calculate_fleet_metrics(self, vehicles: List[Dict], routes: List[Dict]) -> Dict:
        """
        Calculate aggregated fleet fuel metrics
        """
        total_fuel = 0
        total_cost = 0
        total_emissions = 0
        total_distance = 0
        
        for vehicle in vehicles:
            if vehicle.get('status') != 'active':
                continue
            
            # Get vehicle's assigned route
            route = next((r for r in routes if r.get('vehicle_id') == vehicle.get('vehicle_id')), None)
            if route:
                fuel_data = self.calculate_fuel_consumption(route, vehicle)
                total_fuel += fuel_data['fuel_gallons_needed']
                total_cost += fuel_data['fuel_cost_usd']
                total_emissions += fuel_data['co2_emissions_kg']
                total_distance += route.get('distance_miles', 0)
        
        return {
            'total_fuel_gallons': round(total_fuel, 2),
            'total_fuel_cost': round(total_cost, 2),
            'total_co2_emissions_kg': round(total_emissions, 2),
            'total_distance_miles': round(total_distance, 2),
            'average_mpg': round(total_distance / total_fuel if total_fuel > 0 else 0, 2),
            'cost_per_mile': round(total_cost / total_distance if total_distance > 0 else 0, 3)
        }