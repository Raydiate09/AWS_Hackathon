# Location Autocomplete Feature

## Overview
The route optimization form now includes **smart location search** using Mapbox's geocoding API. Users no longer need to manually enter latitude and longitude coordinates - they can simply search for locations by name.

## How It Works

### User Experience
1. **Start Typing**: User begins typing a location name (e.g., "san", "university", "airport")
2. **See Suggestions**: After 3+ characters, a dropdown appears with matching locations
3. **Select Location**: User clicks on their desired location from the dropdown
4. **Auto-Fill**: The full address and coordinates are automatically filled in

### Technical Implementation

#### Components
- **`LocationInput.tsx`**: New reusable component for location search
  - Provides autocomplete dropdown
  - Integrates with Mapbox Geocoding API
  - Handles debounced search (300ms delay)
  - Shows loading spinner during search
  - Displays coordinates below input when location is selected

#### API Integration
- **Geocoding Service**: Mapbox Geocoding API v5
- **Endpoint**: `https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json`
- **Parameters**:
  - `access_token`: Mapbox API token
  - `autocomplete=true`: Enable real-time suggestions
  - `limit=5`: Show top 5 results

#### Features
- **Debouncing**: 300ms delay to reduce API calls while typing
- **Minimum Characters**: Requires 3+ characters before searching
- **Click Outside**: Dropdown closes when clicking outside
- **Loading State**: Visual spinner during API calls
- **Coordinate Display**: Shows lat/lng below input after selection

## Usage

### Origin and Destination
```tsx
<LocationInput
  label="Origin"
  value={origin}
  onChange={setOrigin}
  placeholder="Search for origin location (e.g., San Francisco Airport)"
/>
```

### Stops
```tsx
<LocationInput
  label="Add a Stop"
  value={newStop}
  onChange={setNewStop}
  placeholder="Search for a stop location"
/>
```

## Example Searches
- **Airports**: "SFO", "San Francisco Airport", "LAX"
- **Universities**: "Stanford", "UC Berkeley", "Santa Clara University"
- **Cities**: "San Jose", "Palo Alto", "Mountain View"
- **Landmarks**: "Golden Gate Bridge", "Fisherman's Wharf"
- **Addresses**: "123 Main St", "1600 Pennsylvania Ave"

## Data Structure

### Location Object
```typescript
interface Location {
  address: string;           // Full place name (e.g., "San Francisco International Airport, CA")
  coordinates: {
    lat: number;            // Latitude (e.g., 37.6213)
    lng: number;            // Longitude (e.g., -122.3790)
  };
}
```

### Mapbox Response
```typescript
interface MapboxFeature {
  id: string;               // Unique feature ID
  place_name: string;       // Full formatted address
  center: [number, number]; // [longitude, latitude]
  text: string;             // Short name/title
}
```

## Benefits
1. **User-Friendly**: No need to look up coordinates
2. **Fast**: Real-time suggestions as you type
3. **Accurate**: Uses Mapbox's global geocoding database
4. **Professional**: Clean UI with loading states and dropdown
5. **Error Prevention**: Validates locations before enabling route buttons

## Configuration
The Mapbox token is stored in the component:
```typescript
const MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';
```

For production, consider moving this to environment variables.

## Future Enhancements
- [ ] Current location detection (geolocation API)
- [ ] Recent searches history
- [ ] Favorite/saved locations
- [ ] Map click to select location
- [ ] Reverse geocoding (click map → get address)
- [ ] Filter by location type (airports, restaurants, etc.)
- [ ] Multi-language support
