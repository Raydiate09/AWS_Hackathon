# Smart Break Scheduling with High-Risk Period Optimization

## Overview
The Driver Schedule Optimizer now intelligently schedules mandatory HOS breaks and rest periods to overlap with high sunlight risk time zones, maximizing safety and efficiency.

## Key Features

### 1. **Proactive Break Scheduling**
- System looks ahead up to 4 hours to detect upcoming high-risk driving periods
- If a mandatory break is needed within 2 hours AND high-risk conditions are detected ahead, the system:
  - Drives to the high-risk time period
  - Takes the break during dangerous conditions
  - Resumes driving when conditions are safer

### 2. **Optimized Rest Periods**
- 10-hour rest periods are scheduled to maximize overlap with high-risk times
- If high-risk conditions are detected within 2 hours, the rest period starts early to cover them
- Drivers avoid driving during dangerous sun glare by resting through it

### 3. **Strategic Break Timing**
- 30-minute breaks are aligned with high sunlight risk periods when possible
- Breaks scheduled within 1 hour of high-risk conditions are delayed to overlap
- Reduces wasted time by combining mandatory breaks with unsafe driving conditions

## How It Works

### Risk Detection
```python
# System looks ahead through route segments
upcoming_high_risk = _find_upcoming_high_risk_period(
    route_segments,
    current_segment,
    current_time
)
```

### Break Optimization Logic
1. **Check HOS Requirements**: Is a break or rest needed?
2. **Look Ahead**: Are there high-risk conditions in the next 1-4 hours?
3. **Calculate Optimal Time**: 
   - If high risk is soon (< 1 hour for breaks, < 2 hours for rest)
   - Delay the stop to overlap with high-risk period
4. **Execute**: Drive to the high-risk time, then take the break/rest

### Example Scenario
```
Current Time: 10:00 AM
- Driver needs 30-min break by 12:00 PM (after 8 hours driving)
- High sunlight risk detected at 11:30 AM - 12:30 PM (sun angle)
- Decision: Drive until 11:30 AM, take break 11:30-12:00 PM
- Result: Break overlaps with high-risk period, resume at safer time
```

## Benefits

### Safety
- ✅ Drivers avoid sun glare during peak danger times
- ✅ Mandatory breaks align with when driving is most risky
- ✅ Reduced eye strain and accident risk

### Efficiency
- ✅ No wasted time - breaks serve dual purpose
- ✅ Less total elapsed time compared to separate breaks and safety waits
- ✅ Better arrival time predictions

### Compliance
- ✅ All FMCSA HOS regulations still enforced
- ✅ 30-minute breaks after 8 hours
- ✅ 11-hour driving limit
- ✅ 14-hour on-duty window
- ✅ 10-hour rest periods

## UI Indicators

### Optimized Stops Display
Breaks and rests that are optimized for high-risk periods show:
- **Purple background** instead of white
- **⭐ Optimized** or **⭐ Strategic** badge
- Enhanced reason text explaining the optimization
- Sunlight risk score when applicable

### Example Display
```
☕ Rest Stop                    ⭐ Strategic
11:30 AM - 30 min
Strategic break during high-risk period (risk: 75)
```

## Configuration

### Optimizer Settings
```python
self.high_risk_threshold = 70  # Risk score to trigger optimization
self.look_ahead_hours = 4      # How far to look for high-risk periods
self.prefer_break_during_high_risk = True  # Enable optimization
```

### Tunable Parameters
- **High Risk Threshold** (default: 70): Sunlight risk score that triggers avoidance
- **Look Ahead Window** (default: 4 hours): How far to scan for upcoming risks
- **Break Delay Tolerance** (default: 1 hour for breaks, 2 hours for rest): Max time to delay a stop

## Technical Implementation

### Key Functions

#### `_find_upcoming_high_risk_period()`
Scans upcoming route segments to detect high-risk driving conditions
- Returns: segment index, time until risk, risk score
- Considers: sun position, driving bearing, time of day

#### `_find_optimal_break_time()`
Calculates best time to start a 30-minute break
- Delays break up to 1 hour if high risk is ahead
- Ensures HOS compliance maintained

#### `_find_optimal_rest_time()`
Calculates best time to start a 10-hour rest period
- Delays rest up to 2 hours to maximize overlap with high-risk times
- Prioritizes covering peak danger periods

## API Response Format

### Optimized Stop Object
```json
{
  "type": "30_min_break",
  "location": "Rest Stop",
  "start_time": "2025-10-25T11:30:00",
  "duration_minutes": 30,
  "reason": "Strategic break during high-risk period (risk: 75)",
  "optimized": true,
  "coordinates": {"lat": 37.7749, "lng": -122.4194}
}
```

### Schedule Response
```json
{
  "departure_time": "2025-10-25T08:00:00",
  "estimated_arrival": "2025-10-25T18:30:00",
  "total_driving_time": 480,
  "total_elapsed_time": 630,
  "safety_score": 92.5,
  "hos_compliant": true,
  "breaks": [...],
  "rest_stops": [...],
  "warnings": [
    "10-hour rest required at Rest Area",
    "Break optimized for high-risk period at 11:30 AM"
  ]
}
```

## Future Enhancements

### Potential Improvements
1. **Multi-Risk Optimization**: Consider weather, traffic, and crash data together
2. **Rest Area Database**: Find actual rest stops with amenities
3. **Driver Preferences**: Allow customization of break timing preferences
4. **Historical Analysis**: Learn from past routes to improve predictions
5. **Real-time Adjustments**: Update schedule based on actual progress

### Advanced Features
- **Team Driving**: Optimize for driver swaps during high-risk periods
- **Route Alternatives**: Suggest different routes if HOS delays are significant
- **Cost Analysis**: Calculate fuel savings from optimized scheduling
- **Fatigue Modeling**: Incorporate circadian rhythm and sleep science

## Usage Example

```typescript
// Frontend - Request optimized schedule
const scheduleResult = await apiService.optimizeDriverSchedule({
  route_coordinates: coordinates,
  total_duration_seconds: duration,
  departure_time: "2025-10-25T08:00:00",
  preferred_arrival: "2025-10-25T18:00:00"
});

// Check for optimized breaks
scheduleResult.breaks.forEach(brk => {
  if (brk.optimized) {
    console.log(`Strategic break at ${brk.start_time}`);
    console.log(`Reason: ${brk.reason}`);
  }
});
```

## Testing Recommendations

### Test Cases
1. **Long Haul Route**: 12+ hour trip requiring multiple breaks and rest
2. **Morning Start**: Departure at 6 AM to test sunrise optimization
3. **Evening Drive**: Departure at 4 PM to test sunset optimization
4. **East-West Route**: Maximum sun exposure during drive
5. **Short Route**: Verify no unnecessary optimization on brief trips

### Expected Behaviors
- Breaks should align with peak sun risk (dawn/dusk, direct exposure)
- Rest periods should cover highest risk hours
- Total elapsed time should be <= separate breaks + safety waits
- All HOS regulations must remain enforced
- Safety score should improve with optimization

## Conclusion
Smart break scheduling represents a significant advancement in driver safety and operational efficiency. By intelligently combining mandatory HOS compliance with sunlight risk management, the system ensures drivers rest when conditions are most dangerous, maximizing both safety and productivity.
