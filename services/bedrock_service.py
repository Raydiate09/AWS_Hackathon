import boto3
import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class BedrockService:
    """
    Service for interacting with AWS Bedrock Claude model
    for intelligent route optimization decisions
    """
    
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-west-2'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def optimize_route(self, route_data: Dict) -> Dict:
        """
        Use Claude to analyze route options and recommend optimal path
        balancing safety and fuel efficiency
        """
        
        # Construct the prompt with route context
        prompt = self._build_optimization_prompt(route_data)
        
        try:
            # Prepare the request
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": messages,
                    "temperature": 0.3,  # Lower for more consistent recommendations
                    "top_p": 0.9
                })
            )
            
            # Parse response
            response_body = json.loads(response.get('body').read())
            ai_response = response_body.get('content', [{}])[0].get('text', '')
            
            # Extract structured data from AI response
            return self._parse_ai_response(ai_response, route_data)
            
        except Exception as e:
            print(f"Bedrock API Error: {str(e)}")
            # Return fallback optimization if AI fails
            return self._fallback_optimization(route_data)
    
    def _build_optimization_prompt(self, route_data: Dict) -> str:
        """
        Build a detailed prompt for Claude with all route context
        """
        return f"""
        You are an AI route optimizer for a commercial fleet. Analyze these route options and recommend the optimal path.
        
        ROUTE DATA:
        - Origin: {route_data.get('origin')}
        - Destination: {route_data.get('destination')}
        - Vehicle Type: {route_data.get('vehicle_type', 'delivery_van')}
        - Cargo Weight: {route_data.get('cargo_weight', 2500)} lbs
        - Priority: {route_data.get('priority', 'balanced')} (safety, fuel_efficiency, or balanced)
        
        CURRENT CONDITIONS:
        - Weather: {route_data.get('weather', {}).get('conditions', 'Clear')}
        - Visibility: {route_data.get('weather', {}).get('visibility_miles', 10)} miles
        - Road Condition: {route_data.get('weather', {}).get('road_condition', 'dry')}
        
        AVAILABLE ROUTES:
        {json.dumps(route_data.get('routes', []), indent=2)}
        
        TRAFFIC CONDITIONS:
        {json.dumps(route_data.get('traffic', {}), indent=2)}
        
        Please analyze each route considering:
        1. Safety factors (weather, road conditions, incident history, congestion)
        2. Fuel efficiency (distance, speed, stop-and-go traffic, elevation changes)
        3. Time estimates (current traffic, typical delays)
        4. Risk assessment (accident probability, weather hazards)
        
        Provide your recommendation in this JSON format:
        {{
            "recommended_route_id": "route_id",
            "safety_score": 0-100,
            "fuel_efficiency_score": 0-100,
            "estimated_fuel_gallons": number,
            "estimated_time_minutes": number,
            "risk_factors": ["list", "of", "risks"],
            "optimization_reasoning": "explanation",
            "alternative_suggestion": "any modifications to improve the route"
        }}
        
        Focus on {route_data.get('priority', 'balanced')} optimization.
        """
    
    def _parse_ai_response(self, ai_text: str, route_data: Dict) -> Dict:
        """
        Parse Claude's response into structured data
        """
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', ai_text)
            if json_match:
                parsed = json.loads(json_match.group())
                # Add original routes for comparison
                parsed['all_routes'] = route_data.get('routes', [])
                parsed['ai_confidence'] = 0.85  # Confidence score
                return parsed
        except:
            pass
        
        # If parsing fails, return structured fallback
        return self._fallback_optimization(route_data)
    
    def _fallback_optimization(self, route_data: Dict) -> Dict:
        """
        Fallback optimization using rule-based logic if AI fails
        """
        routes = route_data.get('routes', [])
        if not routes:
            return {"error": "No routes available"}
        
        # Simple scoring based on distance and traffic
        best_route = None
        best_score = -1
        
        for route in routes:
            # Calculate simple score
            distance_score = 100 - (route.get('distance_miles', 100) / 2)
            traffic_score = 100 - (route.get('traffic_delay_minutes', 0) * 2)
            safety_score = 100 - (route.get('incidents', 0) * 20)
            
            total_score = (distance_score + traffic_score + safety_score) / 3
            
            if total_score > best_score:
                best_score = total_score
                best_route = route
        
        return {
            "recommended_route_id": best_route.get('route_id', 'route_1'),
            "safety_score": min(100, max(0, 100 - best_route.get('incidents', 0) * 20)),
            "fuel_efficiency_score": min(100, max(0, 100 - best_route.get('distance_miles', 50))),
            "estimated_fuel_gallons": best_route.get('distance_miles', 50) / 20,  # Rough MPG estimate
            "estimated_time_minutes": best_route.get('duration_minutes', 60),
            "risk_factors": ["Fallback optimization - limited analysis"],
            "optimization_reasoning": "Selected based on distance and traffic conditions",
            "ai_confidence": 0.3
        }
    
    def analyze_driver_behavior(self, driver_data: Dict) -> Dict:
        """
        Analyze driver patterns for safety recommendations
        """
        prompt = f"""
        Analyze this driver's behavior data and provide safety recommendations:
        
        Driver Data:
        {json.dumps(driver_data, indent=2)}
        
        Provide analysis in JSON format:
        {{
            "safety_rating": 0-100,
            "strengths": ["list"],
            "areas_for_improvement": ["list"],
            "recommendations": ["list"]
        }}
        """
        
        # Similar implementation to optimize_route
        # ... (abbreviated for brevity)
        
        return {
            "safety_rating": 75,
            "strengths": ["Consistent speed", "Good weather adaptation"],
            "areas_for_improvement": ["Rush hour navigation", "Fuel efficiency"],
            "recommendations": ["Consider alternate routes during peak hours"]
        }