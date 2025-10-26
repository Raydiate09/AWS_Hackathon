# Sunlight Risk Analysis Feature

## Overview
The sunlight risk analysis calculates delivery risk based on sun position, driving direction, and time of day. This helps identify potentially dangerous driving conditions caused by sun glare or low-light visibility.

## How It Works

### Sun Position Calculation
Uses astronomical algorithms to calculate the sun's exact position for any location, date, and time:
- **Azimuth**: Direction of the sun (0° = North, 90° = East, 180° = South, 270° = West)
- **Altitude**: Height of sun above horizon (0° = horizon, 90° = directly overhead, negative = nighttime)

### Risk Factors

#### Daytime Risks (Sun Above Horizon)
1. **Critical Risk (80-100)**: Driving directly into low sun (sunrise/sunset glare)
   - Sun altitude < 15° and driving toward sun (within 30° angle)
   - Maximum glare, severely reduced visibility
   
2. **High Risk (60-80)**: Sun at low angle with moderate glare
   - Sun altitude < 30° and driving toward or near sun
   - Significant visibility reduction

3. **Moderate Risk (40-60)**: Sun overhead but still affects visibility
   - Sun altitude < 30° but not directly in path
   - Some glare possible from side angles

4. **Low Risk (20-40)**: High sun with minimal impact
   - Sun altitude > 30°
   - Optimal lighting conditions, sun behind driver

#### Nighttime Risks (Sun Below Horizon)
1. **High Risk (75)**: Full nighttime driving
   - Sun > 12° below horizon
   - Visibility dependent on street lighting and vehicle lights

2. **Moderate-High Risk (60)**: Nautical twilight
   - Sun 6-12° below horizon
   - Significantly reduced but some ambient light

3. **Moderate Risk (45)**: Civil twilight (dusk/dawn)
   - Sun 0-6° below horizon
   - Reduced visibility but some natural light remains

### Driving Direction Impact
The system calculates the angle between:
- **Driving bearing**: Direction of travel from one point to another
- **Sun azimuth**: Direction to the sun

**Maximum risk** occurs when driving directly toward the sun (angle difference < 30°)
**Minimum risk** occurs when sun is behind or perpendicular to driving direction

## Route Analysis
For multi-segment routes, the system:
1. Samples route coordinates to create segments
2. Calculates sun position for each segment based on arrival time
3. Determines driving direction for each segment
4. Computes risk score for each segment
5. Provides overall risk score and recommendations

## API Endpoint

### POST `/api/sunlight-risk`

**Request Body:**
```json
{
  "origin": {
    "lat": 37.6213,
    "lng": -122.3790
  },
  "destination": {
    "lat": 37.3496,
    "lng": -121.9390
  },
  "departure_time": "2025-10-25T15:00:00Z",
  "route_coordinates": [[lng, lat], ...] 
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_risk_score": 45.2,
    "overall_risk_level": "Moderate",
    "departure_time": "2025-10-25T15:00:00+00:00",
    "segment_count": 10,
    "segments": [
      {
        "segment_index": 0,
        "segment_name": "Segment 1",
        "start_time": "2025-10-25T15:00:00+00:00",
        "risk_score": 65.3,
        "risk_level": "Moderate-High",
        "sun_altitude": 25.4,
        "sun_azimuth": 245.6,
        "driving_bearing": 240.2,
        "is_daytime": true,
        "explanation": "Moderate sun glare - driving toward sun (altitude: 25.4°)"
      }
    ],
    "recommendations": [
      "🌅 2 segment(s) with severe sun glare. Ensure sun visors are functional and consider sunglasses.",
      "✅ Consider sunglasses and functional sun visors"
    ]
  }
}
```

## Risk Levels

| Score Range | Level | Description | Recommendations |
|------------|-------|-------------|-----------------|
| 80-100 | Critical | Severe sun glare, driving into low sun | Delay departure if possible, use sun visor, wear polarized sunglasses |
| 60-79 | High | Significant glare or nighttime driving | Sunglasses for daytime, ensure lights work for night |
| 40-59 | Moderate | Some glare or twilight conditions | Standard precautions, be aware of sun position |
| 20-39 | Low | Minimal sun impact | Optimal conditions |
| 0-19 | Very Low | Excellent lighting | No special precautions needed |

## Real-World Examples

### Example 1: Morning Commute (High Risk)
**Route**: East-bound at 7:00 AM
- Driving directly into rising sun
- Sun altitude: 10° (low on horizon)
- Risk Score: 90/100 (Critical)
- **Recommendation**: Leave 1 hour later to avoid severe glare

### Example 2: Midday Delivery (Low Risk)
**Route**: North-bound at 12:00 PM
- Sun high overhead (altitude: 60°)
- Risk Score: 25/100 (Low)
- **Recommendation**: Optimal time for this route

### Example 3: Night Delivery (High Risk)
**Route**: Any direction at 10:00 PM
- Sun below horizon (altitude: -45°)
- Risk Score: 75/100 (High)
- **Recommendation**: Ensure all vehicle lights operational, reduce speed in low-light areas

### Example 4: Sunset Drive (Critical Risk)
**Route**: West-bound at 6:00 PM
- Driving into setting sun
- Sun altitude: 5° (very low)
- Risk Score: 95/100 (Critical)
- **Recommendation**: Severe glare hazard, consider alternative time or route

## Technical Implementation

### Astronomical Calculations
- **Julian Day**: Converts datetime to astronomical time scale
- **Solar Declination**: Sun's position relative to Earth's equator
- **Hour Angle**: Local solar time
- **Altitude/Azimuth**: Horizontal coordinate system for sun position

### Accuracy
- Position calculations accurate to ±0.5° for dates 1900-2100
- Accounts for:
  - Earth's axial tilt (obliquity)
  - Elliptical orbit (equation of time)
  - Geographic location
  - Local time zone

### Performance
- Single segment calculation: < 10ms
- 10-segment route analysis: < 50ms
- No external API calls required (pure calculation)

## Integration with Route Optimization

When users get a TomTom route:
1. Route coordinates automatically sent to sunlight analysis
2. Analysis displayed in route results
3. Segment-by-segment breakdown available
4. Recommendations provided based on risk level

## Future Enhancements
- [ ] Time-of-day optimization (suggest best departure time)
- [ ] Weather integration (cloud cover reduces glare risk)
- [ ] Route alternative suggestions to avoid high-glare segments
- [ ] Historical sun data for seasonal patterns
- [ ] Integration with vehicle specs (windshield tint, visor quality)
- [ ] Driver preference settings (sun sensitivity)
