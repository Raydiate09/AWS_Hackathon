# TomTom API Integration

## Overview
Successfully integrated TomTom Routing API for real-time, traffic-aware route optimization alongside the existing Claude AI recommendations.

## Backend Changes

### 1. TomTom Service Layer (`backend/tomtom_service.py`)
Created service module with `get_tomtom_route()` function:
- Accepts origin, destination, and waypoints
- Calls TomTom calculateRoute API with:
  - `traffic=true` for real-time traffic consideration
  - `computeBestOrder=true` for automatic waypoint optimization
- Returns route coordinates and summary (distance, time, traffic delay)

### 2. Flask Endpoint (`backend/app.py`)
Added `/api/tomtom-route` POST endpoint:
- Accepts JSON with route data (origin, destination, stops)
- Extracts coordinates and calls TomTom service
- Returns optimized route coordinates and summary

## Frontend Changes

### 1. MapboxExample Component
Updated to support both route types:
- **Manual Route**: Blue line from user-provided points
- **TomTom Route**: Green line from TomTom optimized coordinates
- Automatically fits map bounds to show full route
- Smart marker placement for both modes

### 2. API Service (`frontend/src/services/api.ts`)
Added `getTomTomRoute()` function:
- Calls `/api/tomtom-route` endpoint
- Returns coordinates and route summary

### 3. RouteOptimizationForm Component
Enhanced with dual optimization:
- **Claude AI Button**: Gets AI-powered recommendations (weather, traffic, sunlight analysis)
- **TomTom Route Button**: Gets traffic-aware, optimized routing
- Displays results for both independently
- Shows TomTom metrics: distance, travel time, traffic delay, ETA

### 4. App Component
Updated state management:
- Added `routeCoordinates` to route data state
- Passes TomTom coordinates to map when available
- Supports switching between manual/AI/TomTom routes

## Configuration Required

### Environment Variables
Add to `backend/.env`:
```bash
TOMTOM_API_KEY=your_tomtom_api_key_here
```

Get your API key from: https://developer.tomtom.com/

## Usage

1. **Start Backend**:
   ```bash
   cd /Users/ruizhao/Desktop/Hackathon/DTS
   source venv/bin/activate
   cd backend
   python app.py
   ```

2. **Start Frontend**:
   ```bash
   # In new terminal
   cd /Users/ruizhao/Desktop/Hackathon/DTS/frontend
   npm run dev
   ```

3. **Using TomTom Route**:
   - Fill in origin, destination, and optional stops
   - Click "Get TomTom Route" button
   - Map displays green line with optimized route
   - View distance, time, and traffic metrics

4. **Using Claude AI**:
   - Same inputs as TomTom
   - Click "Optimize with Claude AI" button
   - Get AI recommendations for best departure time
   - See weather, traffic, and sunlight scores

## Features

### TomTom Routing Advantages
- ✅ Real-time traffic data
- ✅ Automatic waypoint reordering for shortest route
- ✅ Traffic delay estimation
- ✅ Accurate arrival time predictions
- ✅ Turn-by-turn coordinates for precise map rendering

### Claude AI Advantages
- ✅ Multi-factor analysis (weather, traffic, sunlight)
- ✅ Optimal departure time recommendations
- ✅ Contextual advice for delivery planning
- ✅ Historical pattern recognition

## API Response Format

### TomTom Response
```json
{
  "success": true,
  "coordinates": [[lng, lat], [lng, lat], ...],
  "summary": {
    "lengthInMeters": 45320,
    "travelTimeInSeconds": 2156,
    "trafficDelayInSeconds": 234,
    "departureTime": "2024-01-15T10:00:00Z",
    "arrivalTime": "2024-01-15T10:35:56Z"
  }
}
```

### Claude AI Response
```json
{
  "success": true,
  "data": {
    "requestId": "uuid",
    "optimizedRoute": {...},
    "metrics": {
      "distance": 45.32,
      "estimatedTime": "35 minutes",
      "scores": {
        "weather": 85,
        "traffic": 72,
        "sunlight": 90,
        "overall": 82
      }
    },
    "recommendations": ["...", "..."]
  }
}
```

## Visual Indicators

- 🟢 **Green Route**: TomTom optimized with traffic
- 🔵 **Blue Route**: Manual or Claude AI suggested
- 🟢 **Green Marker**: Origin/Start point
- 🔵 **Blue Markers**: Intermediate stops
- 🔴 **Red Marker**: Destination/End point

## Next Steps

1. Add TOMTOM_API_KEY to `.env` file
2. Test with real coordinates
3. Consider combining both APIs:
   - Use TomTom for routing
   - Use Claude for timing/scheduling recommendations
4. Add route comparison view to show both options side-by-side
