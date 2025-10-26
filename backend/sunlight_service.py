"""
Sunlight Risk Analysis Service
Calculates risk based on sun position, driving direction, and time of day
"""
import math
from datetime import datetime, timezone
from typing import Dict, Tuple


def calculate_sun_position(latitude: float, longitude: float, dt: datetime) -> Dict[str, float]:
    """
    Calculate sun's azimuth and altitude angles for a given location and time.
    
    Args:
        latitude: Location latitude in degrees
        longitude: Location longitude in degrees
        dt: DateTime object (should be timezone-aware)
    
    Returns:
        Dictionary with 'azimuth' (0-360°, 0=North) and 'altitude' (0-90°) of sun
    """
    # Convert datetime to UTC if not already
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    # Calculate Julian Day
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    
    if month <= 2:
        year -= 1
        month += 12
    
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    
    JD = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    JD += hour / 24.0
    
    # Calculate Julian centuries from J2000.0
    T = (JD - 2451545.0) / 36525.0
    
    # Sun's mean longitude (degrees)
    L0 = (280.46646 + 36000.76983 * T + 0.0003032 * T * T) % 360
    
    # Sun's mean anomaly (degrees)
    M = (357.52911 + 35999.05029 * T - 0.0001537 * T * T) % 360
    M_rad = math.radians(M)
    
    # Sun's equation of center
    C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M_rad)
    C += (0.019993 - 0.000101 * T) * math.sin(2 * M_rad)
    C += 0.000289 * math.sin(3 * M_rad)
    
    # Sun's true longitude
    true_long = L0 + C
    
    # Sun's apparent longitude
    omega = 125.04 - 1934.136 * T
    lambda_sun = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    
    # Obliquity of ecliptic
    epsilon = 23.439291 - 0.0130042 * T - 0.00000164 * T * T + 0.000000504 * T * T * T
    epsilon_rad = math.radians(epsilon)
    lambda_rad = math.radians(lambda_sun)
    
    # Sun's declination
    delta = math.asin(math.sin(epsilon_rad) * math.sin(lambda_rad))
    
    # Greenwich Mean Sidereal Time
    GMST = (280.46061837 + 360.98564736629 * (JD - 2451545.0) + 
            0.000387933 * T * T - T * T * T / 38710000.0) % 360
    
    # Local Sidereal Time
    LST = (GMST + longitude) % 360
    
    # Hour angle
    alpha = math.atan2(math.cos(epsilon_rad) * math.sin(lambda_rad), math.cos(lambda_rad))
    alpha_deg = math.degrees(alpha)
    H = (LST - alpha_deg) % 360
    H_rad = math.radians(H)
    
    # Convert to radians for calculation
    lat_rad = math.radians(latitude)
    
    # Calculate altitude (elevation angle)
    sin_alt = (math.sin(lat_rad) * math.sin(delta) + 
               math.cos(lat_rad) * math.cos(delta) * math.cos(H_rad))
    altitude = math.degrees(math.asin(max(-1, min(1, sin_alt))))
    
    # Calculate azimuth
    cos_az = (math.sin(delta) - math.sin(lat_rad) * math.sin(math.radians(altitude))) / \
             (math.cos(lat_rad) * math.cos(math.radians(altitude)))
    cos_az = max(-1, min(1, cos_az))  # Clamp to valid range
    
    azimuth = math.degrees(math.acos(cos_az))
    
    # Adjust azimuth based on hour angle
    if math.sin(H_rad) > 0:
        azimuth = 360 - azimuth
    
    return {
        'azimuth': azimuth,  # 0° = North, 90° = East, 180° = South, 270° = West
        'altitude': altitude  # 0° = horizon, 90° = directly overhead
    }


def calculate_driving_bearing(from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> float:
    """
    Calculate the bearing (direction) from one point to another.
    
    Returns:
        Bearing in degrees (0-360, where 0=North, 90=East, 180=South, 270=West)
    """
    lat1 = math.radians(from_lat)
    lat2 = math.radians(to_lat)
    diff_lng = math.radians(to_lng - from_lng)
    
    x = math.sin(diff_lng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(diff_lng)
    
    bearing = math.atan2(x, y)
    bearing_deg = (math.degrees(bearing) + 360) % 360
    
    return bearing_deg


def calculate_angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate the smallest difference between two angles (0-360°).
    
    Returns:
        Difference in degrees (0-180)
    """
    diff = abs(angle1 - angle2) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


def calculate_sunlight_risk(
    latitude: float,
    longitude: float,
    driving_bearing: float,
    dt: datetime
) -> Dict[str, any]:
    """
    Calculate risk factor based on sun position and driving direction.
    
    Risk Factors:
    - High risk (80-100): Driving directly into sun (sunrise/sunset glare)
    - Medium risk (40-70): Sun at an angle, some glare possible
    - Low risk (20-40): Sun overhead or behind
    - Night risk (60-90): Low visibility, depends on time after sunset
    
    Args:
        latitude: Current location latitude
        longitude: Current location longitude
        driving_bearing: Direction of travel in degrees (0=North, 90=East, etc.)
        dt: Current datetime
    
    Returns:
        Dictionary with risk score, sun position, and explanation
    """
    sun_pos = calculate_sun_position(latitude, longitude, dt)
    sun_azimuth = sun_pos['azimuth']
    sun_altitude = sun_pos['altitude']
    
    # Determine if it's day or night
    is_daytime = sun_altitude > 0
    
    if is_daytime:
        # Calculate angle between driving direction and sun position
        angle_to_sun = calculate_angle_difference(driving_bearing, sun_azimuth)
        
        # Risk calculation for daytime
        if sun_altitude < 15:  # Sun is low (sunrise/sunset)
            # Maximum glare risk when driving toward sun
            if angle_to_sun < 30:  # Driving directly into sun
                risk_score = 95 - (sun_altitude * 1.5)  # Lower sun = higher risk
                risk_level = "Critical"
                explanation = f"Severe sun glare - driving directly into low sun (altitude: {sun_altitude:.1f}°)"
            elif angle_to_sun < 60:
                risk_score = 75 - (sun_altitude * 0.5)
                risk_level = "High"
                explanation = f"Significant sun glare from side (angle: {angle_to_sun:.1f}°)"
            else:
                risk_score = 35
                risk_level = "Low"
                explanation = "Sun at low angle but not in driving direction"
        
        elif sun_altitude < 30:  # Sun is moderately low
            if angle_to_sun < 45:
                risk_score = 70 - (sun_altitude * 0.8)
                risk_level = "Moderate-High"
                explanation = f"Moderate sun glare - driving toward sun (altitude: {sun_altitude:.1f}°)"
            elif angle_to_sun < 90:
                risk_score = 45
                risk_level = "Moderate"
                explanation = f"Some glare possible from side angle"
            else:
                risk_score = 25
                risk_level = "Low"
                explanation = "Sun behind or to the side"
        
        else:  # Sun is high (altitude >= 30°)
            if angle_to_sun < 60:
                risk_score = 35 - (sun_altitude * 0.2)  # Risk decreases as sun gets higher
                risk_level = "Low"
                explanation = f"Minimal glare - high sun (altitude: {sun_altitude:.1f}°)"
            else:
                risk_score = 20
                risk_level = "Very Low"
                explanation = f"Optimal lighting conditions - high sun behind driver"
    
    else:
        # Night time risk calculation
        time_after_sunset = abs(sun_altitude)  # How far below horizon
        
        if time_after_sunset < 6:  # Twilight (civil twilight)
            risk_score = 45
            risk_level = "Moderate"
            explanation = "Twilight - reduced visibility but some natural light"
        elif time_after_sunset < 12:  # Nautical twilight
            risk_score = 60
            risk_level = "Moderate-High"
            explanation = "Dusk/Dawn - significantly reduced visibility"
        else:  # Full night
            risk_score = 75
            risk_level = "High"
            explanation = "Night driving - visibility dependent on street lighting and vehicle lights"
    
    # Ensure risk score is in valid range
    risk_score = max(0, min(100, risk_score))
    
    return {
        'risk_score': round(risk_score, 1),
        'risk_level': risk_level,
        'sun_altitude': round(sun_altitude, 2),
        'sun_azimuth': round(sun_azimuth, 2),
        'driving_bearing': round(driving_bearing, 2),
        'is_daytime': is_daytime,
        'explanation': explanation,
        'time': dt.isoformat()
    }


def analyze_route_sunlight_risk(
    route_segments: list,
    departure_time: datetime
) -> Dict[str, any]:
    """
    Analyze sunlight risk for entire route.
    
    Args:
        route_segments: List of route segments with format:
            [
                {
                    'from_lat': float, 'from_lng': float,
                    'to_lat': float, 'to_lng': float,
                    'duration_seconds': int,
                    'name': str (optional)
                },
                ...
            ]
        departure_time: When the journey starts
    
    Returns:
        Dictionary with overall risk and segment-by-segment analysis
    """
    segment_risks = []
    current_time = departure_time
    total_risk = 0
    
    for i, segment in enumerate(route_segments):
        # Calculate midpoint of segment for sun position
        mid_lat = (segment['from_lat'] + segment['to_lat']) / 2
        mid_lng = (segment['from_lng'] + segment['to_lng']) / 2
        
        # Calculate driving direction
        bearing = calculate_driving_bearing(
            segment['from_lat'], segment['from_lng'],
            segment['to_lat'], segment['to_lng']
        )
        
        # Calculate risk for this segment
        risk = calculate_sunlight_risk(mid_lat, mid_lng, bearing, current_time)
        
        segment_risks.append({
            'segment_index': i,
            'segment_name': segment.get('name', f'Segment {i+1}'),
            'start_time': current_time.isoformat(),
            **risk
        })
        
        total_risk += risk['risk_score']
        
        # Advance time for next segment
        current_time = current_time + timedelta(seconds=segment.get('duration_seconds', 0))
    
    avg_risk = total_risk / len(route_segments) if route_segments else 0
    
    # Categorize overall risk
    if avg_risk < 30:
        overall_level = "Low"
    elif avg_risk < 50:
        overall_level = "Moderate"
    elif avg_risk < 70:
        overall_level = "High"
    else:
        overall_level = "Critical"
    
    return {
        'overall_risk_score': round(avg_risk, 1),
        'overall_risk_level': overall_level,
        'departure_time': departure_time.isoformat(),
        'segment_count': len(route_segments),
        'segments': segment_risks,
        'recommendations': generate_sunlight_recommendations(avg_risk, segment_risks)
    }


def generate_sunlight_recommendations(avg_risk: float, segments: list) -> list:
    """Generate recommendations based on sunlight risk analysis."""
    recommendations = []
    
    if avg_risk > 70:
        recommendations.append("⚠️ High sunlight risk detected. Consider departing at a different time.")
    
    # Check for critical glare segments
    critical_segments = [s for s in segments if s['risk_score'] > 80]
    if critical_segments:
        recommendations.append(
            f"🌅 {len(critical_segments)} segment(s) with severe sun glare. "
            "Ensure sun visors are functional and consider sunglasses."
        )
    
    # Check for night driving
    night_segments = [s for s in segments if not s['is_daytime']]
    if night_segments:
        pct = (len(night_segments) / len(segments)) * 100
        recommendations.append(
            f"🌙 {pct:.0f}% of route during night hours. "
            "Ensure all vehicle lights are operational."
        )
    
    if avg_risk < 30:
        recommendations.append("✅ Excellent lighting conditions for this route and time.")
    
    return recommendations


# Import timedelta for time calculations
from datetime import timedelta
