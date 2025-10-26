import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()


class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.enabled = bool(self.api_key)
        if not self.enabled:
            print("OpenWeather API key missing; segment weather is disabled.")

    def get_weather_forecast(self, lat, lon, timestamp=None):
        """
        Get weather forecast for a specific location and time
        :param lat: Latitude
        :param lon: Longitude
        :param timestamp: Unix timestamp for forecast time (optional)
        :return: Weather forecast data
        """
        if not self.enabled:
            return None

        if lat is None or lon is None:
            return None

        try:
            # If no timestamp provided, use current time
            if timestamp is None:
                url = f"{self.base_url}/weather"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.api_key,
                    'units': 'metric'  # Use metric units
                }
            else:
                url = f"{self.base_url}/forecast"
                params = {
                    'lat': lat,
                    'lon': lon,
                    'appid': self.api_key,
                    'units': 'metric'
                }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if timestamp and 'list' in data:
                # Find the closest forecast time
                forecasts = data['list']
                closest_forecast = min(
                    forecasts,
                    key=lambda x: abs(x['dt'] - timestamp)
                )
                return self._format_weather_data(closest_forecast)
            else:
                return self._format_weather_data(data)

        except requests.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None

    def _format_weather_data(self, data):
        """
        Format the weather data response
        """
        if not data:
            return None

        weather = data.get('weather', [{}])[0]
        main = data.get('main', {})

        return {
            'description': weather.get('description', ''),
            'temperature': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'humidity': main.get('humidity'),
            'wind_speed': data.get('wind', {}).get('speed'),
            'icon': weather.get('icon'),
            'timestamp': data.get('dt')
        }

    def get_route_segment_weather(self, segments: List[Dict[str, Any]]):
        """
        Get weather forecasts for each segment of the route
        :param segments: List of route segments with coordinates and timing
        :return: List of segments with weather data
        """
        if not segments:
            return []

        if not self.enabled:
            return [
                {**segment, "weather": None}
                for segment in segments
            ]

        result = []
        current_time = datetime.now()
        accumulated_time = 0

        for segment in segments:
            # Get coordinates from the first point in the segment
            coordinates = segment.get("coordinates") or []
            if not isinstance(coordinates, list) or not coordinates:
                segment_with_weather = segment.copy()
                segment_with_weather['weather'] = None
                result.append(segment_with_weather)
                accumulated_time += segment.get('duration_seconds', 0)
                continue

            first_point = coordinates[0]
            if not isinstance(first_point, (list, tuple)) or len(first_point) < 2:
                segment_with_weather = segment.copy()
                segment_with_weather['weather'] = None
                result.append(segment_with_weather)
                accumulated_time += segment.get('duration_seconds', 0)
                continue

            lon, lat = first_point[0], first_point[1]
            
            # Calculate the time when we'll be at this segment
            segment_time = current_time + timedelta(seconds=accumulated_time)
            timestamp = int(segment_time.timestamp())

            # Get weather forecast for this segment
            weather = self.get_weather_forecast(lat, lon, timestamp)
            
            # Add weather data to segment
            segment_with_weather = segment.copy()
            segment_with_weather['weather'] = weather
            
            result.append(segment_with_weather)
            
            # Add this segment's duration to accumulated time
            accumulated_time += segment.get('duration_seconds', 0)

        return result