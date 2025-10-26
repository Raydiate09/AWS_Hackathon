import { useState } from "react";
import { Button } from "@/components/ui/button";
import { LocationInput } from "@/components/ui/location-input";
import { apiService, type OptimizeRouteResponse, type Location } from "@/services/api";

interface RouteOptimizationFormProps {
  onRouteOptimized?: (route: {
    origin: Location;
    destination: Location;
    stops: Location[];
    routeCoordinates?: [number, number][];
  }) => void;
}

export function RouteOptimizationForm({ onRouteOptimized }: RouteOptimizationFormProps) {
  const [loading, setLoading] = useState(false);
  const [tomtomLoading, setTomtomLoading] = useState(false);
  const [sunlightLoading, setSunlightLoading] = useState(false);
  const [result, setResult] = useState<OptimizeRouteResponse | null>(null);
  const [tomtomResult, setTomtomResult] = useState<any>(null);
  const [sunlightResult, setSunlightResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Form inputs using Location objects
  const [origin, setOrigin] = useState<Location>({
    address: "San Francisco International Airport, CA",
    coordinates: { lat: 37.6213, lng: -122.3790 }
  });
  
  const [destination, setDestination] = useState<Location>({
    address: "Santa Clara University, Santa Clara, CA",
    coordinates: { lat: 37.3496, lng: -121.9390 }
  });
  
  const [stops, setStops] = useState<Location[]>([]);
  const [newStop, setNewStop] = useState<Location>({
    address: "",
    coordinates: { lat: 0, lng: 0 }
  });
  
  // Professional Driver Schedule
  const [preferredStartTime, setPreferredStartTime] = useState<string>("");
  const [preferredArrivalTime, setPreferredArrivalTime] = useState<string>("");

  // Clear error and optionally clear arrival time if it was an insufficient delivery time error
  const handleDismissError = () => {
    setError(null);
  };

  const addStop = () => {
    if (newStop.address && newStop.coordinates.lat !== 0 && newStop.coordinates.lng !== 0) {
      setStops([...stops, newStop]);
      setNewStop({
        address: "",
        coordinates: { lat: 0, lng: 0 }
      });
    }
  };

  const removeStop = (index: number) => {
    setStops(stops.filter((_, i) => i !== index));
  };

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.optimizeRoute({
        userId: "demo-user",
        route: {
          origin,
          destination,
          stops
        },
        deliveryWindow: {
          startDate: new Date().toISOString(),
          endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        }
      });

      setResult(response);
      
      // Notify parent component to update map
      if (onRouteOptimized && response.success) {
        onRouteOptimized({
          origin: response.data.optimizedRoute.origin,
          destination: response.data.optimizedRoute.destination,
          stops: response.data.optimizedRoute.stops || []
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to optimize route");
      console.error("Optimization error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTomTomOptimize = async () => {
    setTomtomLoading(true);
    setError(null);

    try {
      // Only send times if they have actual values
      const startTime = preferredStartTime ? preferredStartTime : undefined;
      const arrivalTime = preferredArrivalTime ? preferredArrivalTime : undefined;
      
      console.log('Sending times:', { startTime, arrivalTime });
      
      const response = await apiService.getTomTomRoute(
        {
          origin,
          destination,
          stops
        },
        startTime,
        arrivalTime
      );

      // Check for errors
      if (!response.success) {
        setError(response.error || response.message || "Failed to get TomTom route");
        setTomtomLoading(false);
        return;
      }

      setTomtomResult(response);
      
      // Validate arrival time AFTER getting the route
      if (preferredArrivalTime && response.summary?.arrivalTime) {
        const estimatedArrival = new Date(response.summary.arrivalTime);
        const requiredArrival = new Date(preferredArrivalTime);
        
        console.log('Arrival validation:', {
          estimated: estimatedArrival,
          required: requiredArrival,
          isLate: estimatedArrival > requiredArrival
        });
        
        if (estimatedArrival > requiredArrival) {
          // Show alert and clear the arrival time
          const errorMsg = `⚠️ Insufficient delivery time: Route will arrive at ${estimatedArrival.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            timeZoneName: 'short'
          })}, but you required arrival by ${requiredArrival.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
          })}`;
          
          setError(errorMsg);
          setPreferredArrivalTime(""); // Clear the invalid arrival time
          setTomtomLoading(false);
          return;
        }
      }
      
      // Fetch sunlight risk analysis if route was successful
      if (response.success && response.coordinates) {
        // Use preferred start time or current time for sunlight analysis
        const departureTime = preferredStartTime 
          ? new Date(preferredStartTime).toISOString() 
          : new Date().toISOString();
        
        fetchSunlightRisk(origin, destination, response.coordinates, departureTime);
      }
      
      // Notify parent component to update map with TomTom route
      if (onRouteOptimized && response.success) {
        onRouteOptimized({
          origin,
          destination,
          stops,
          routeCoordinates: response.coordinates
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get TomTom route");
      console.error("TomTom error:", err);
    } finally {
      setTomtomLoading(false);
    }
  };

  const fetchSunlightRisk = async (
    origin: Location,
    destination: Location,
    routeCoordinates?: [number, number][],
    departureTime?: string
  ) => {
    setSunlightLoading(true);
    try {
      const response = await apiService.getSunlightRisk({
        origin: origin.coordinates,
        destination: destination.coordinates,
        departure_time: departureTime || new Date().toISOString(),
        route_coordinates: routeCoordinates
      });

      if (response.success) {
        setSunlightResult(response.data);
      }
    } catch (err) {
      console.error("Sunlight risk error:", err);
      // Don't show error to user, sunlight is optional enhancement
    } finally {
      setSunlightLoading(false);
    }
  };

  return (
    <div className="p-6 border rounded-lg space-y-4">
      <h2 className="text-2xl font-bold">Route Optimization</h2>
      
      {/* Origin Input */}
      <LocationInput
        label="Origin"
        value={origin}
        onChange={setOrigin}
        placeholder="Search for origin location (e.g., San Francisco Airport)"
      />

      {/* Destination Input */}
      <LocationInput
        label="Destination"
        value={destination}
        onChange={setDestination}
        placeholder="Search for destination (e.g., Santa Clara University)"
      />

      {/* Professional Driver Schedule */}
      <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h3 className="text-sm font-semibold text-blue-900">📅 Professional Driver Schedule</h3>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-medium text-blue-800 block mb-1">
              Preferred Start Time (Optional)
            </label>
            <input
              type="datetime-local"
              value={preferredStartTime}
              onChange={(e) => setPreferredStartTime(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-blue-600 mt-1">Used for sunlight analysis</p>
          </div>
          
          <div>
            <label className="text-xs font-medium text-blue-800 block mb-1">
              Required Arrival Time (Optional)
            </label>
            <input
              type="datetime-local"
              value={preferredArrivalTime}
              onChange={(e) => setPreferredArrivalTime(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-blue-600 mt-1">Must arrive before this time</p>
          </div>
        </div>
        
        <p className="text-xs text-blue-700 italic">
          💡 Times are in your <strong>local timezone</strong>. The system automatically adjusts for timezone differences between origin and destination (e.g., EST ↔ PST).
        </p>
      </div>

      {/* Stops */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Stops ({stops.length})</label>
        {stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
            <div className="flex-1 text-sm">
              <div className="font-medium">{stop.address}</div>
              <div className="text-xs text-muted-foreground">
                📍 {stop.coordinates.lat.toFixed(4)}, {stop.coordinates.lng.toFixed(4)}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => removeStop(index)}
            >
              Remove
            </Button>
          </div>
        ))}
        
        {/* Add Stop Form */}
        <div className="space-y-2 pt-2 border-t">
          <LocationInput
            label="Add a Stop"
            value={newStop}
            onChange={setNewStop}
            placeholder="Search for a stop location"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={addStop}
            disabled={!newStop.address || newStop.coordinates.lat === 0}
            className="w-full"
          >
            Add Stop
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        <Button 
          onClick={handleTomTomOptimize} 
          disabled={tomtomLoading || loading || !origin.address || !destination.address}
          className="w-full"
          variant="default"
        >
          {tomtomLoading ? "Loading Route..." : "Show Route on Map"}
        </Button>
        
        <Button 
          onClick={handleOptimize} 
          disabled={loading || tomtomLoading || !origin.address || !destination.address}
          className="w-full"
          variant="outline"
        >
          {loading ? "Analyzing..." : "Get AI Recommendations"}
        </Button>
      </div>

      {/* Info Banner - Now with autocomplete! */}
      <div className="p-4 bg-blue-50 border border-blue-300 rounded-md">
        <p className="text-sm font-semibold text-blue-900 mb-2">
          🔍 Smart Location Search
        </p>
        <p className="text-xs text-blue-800">
          Just start typing a location name (like "san" or "university") and we'll show you matching places. 
          No need to know exact addresses or coordinates - we'll fill those in automatically!
        </p>
      </div>

      {!result && !tomtomResult && !error && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-md">
          <p className="text-sm font-semibold text-amber-900 mb-2">
            � Click "Show Route on Map" to display the real driving route
          </p>
          <p className="text-xs text-amber-800">
            Route will follow actual roads and highways, accounting for real-time traffic conditions. 
            No straight-line paths - only realistic driving routes!
          </p>
        </div>
      )}

      {error && (
        <div className={`p-4 border rounded-md relative ${
          error.includes("Insufficient delivery time") 
            ? "bg-orange-50 border-orange-300" 
            : "bg-red-50 border-red-200"
        }`}>
          <button
            onClick={handleDismissError}
            className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 font-bold text-lg"
            aria-label="Dismiss error"
          >
            ×
          </button>
          <p className={`text-sm font-semibold mb-2 pr-6 ${
            error.includes("Insufficient delivery time")
              ? "text-orange-800"
              : "text-red-800"
          }`}>
            {error.includes("Insufficient delivery time") ? "⏰ Timing Constraint Violation" : "⚠️ Unable to load route"}
          </p>
          <p className={`text-xs mb-2 font-medium ${
            error.includes("Insufficient delivery time")
              ? "text-orange-700"
              : "text-red-700"
          }`}>
            {error}
          </p>
          {!error.includes("Insufficient delivery time") && (
            <p className="text-red-600 text-xs">
              This may be due to missing TomTom API key. Check backend/.env file and ensure TOMTOM_API_KEY is set.
            </p>
          )}
          {error.includes("Insufficient delivery time") && (
            <p className="text-orange-600 text-xs mt-2">
              💡 Suggestion: Either start earlier, or adjust your required arrival time to allow more travel time.
            </p>
          )}
        </div>
      )}

      {result && result.success && (
        <div className="space-y-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <h3 className="font-semibold text-green-900">Optimization Complete!</h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium">Request ID:</p>
              <p className="text-xs text-muted-foreground">{result.data.requestId}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Distance:</p>
              <p className="text-xs">{result.data.metrics.distance} miles</p>
            </div>
            <div>
              <p className="text-sm font-medium">Estimated Time:</p>
              <p className="text-xs">{result.data.metrics.estimatedTime}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Overall Score:</p>
              <p className="text-xs">{result.data.metrics.scores.overall}/100</p>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium mb-2">AI Recommendations:</p>
            <div className="text-xs text-muted-foreground max-h-40 overflow-y-auto">
              {result.data.recommendations.map((rec, idx) => (
                <p key={idx} className="mb-2">{rec}</p>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-4 gap-2">
            <div className="text-center p-2 bg-white rounded">
              <p className="text-xs font-medium">Weather</p>
              <p className="text-lg">{result.data.metrics.scores.weather}</p>
            </div>
            <div className="text-center p-2 bg-white rounded">
              <p className="text-xs font-medium">Traffic</p>
              <p className="text-lg">{result.data.metrics.scores.traffic}</p>
            </div>
            <div className="text-center p-2 bg-white rounded">
              <p className="text-xs font-medium">Sunlight</p>
              <p className="text-lg">{result.data.metrics.scores.sunlight}</p>
            </div>
            <div className="text-center p-2 bg-white rounded">
              <p className="text-xs font-medium">Overall</p>
              <p className="text-lg">{result.data.metrics.scores.overall}</p>
            </div>
          </div>
        </div>
      )}

      {tomtomResult && tomtomResult.success && (
        <div className="space-y-4 p-4 bg-green-50 border border-green-300 rounded-md">
          <h3 className="font-semibold text-green-900">✅ Real Driving Route Displayed</h3>
          
          <p className="text-sm text-green-800">
            Green line on map shows the actual road network route with real-time traffic data
          </p>
          
          {tomtomResult.summary && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium">Driving Distance:</p>
                <p className="text-xs">{(tomtomResult.summary.lengthInMeters * 0.000621371).toFixed(2)} miles</p>
              </div>
              <div>
                <p className="text-sm font-medium">Travel Time:</p>
                <p className="text-xs">{Math.round(tomtomResult.summary.travelTimeInSeconds / 60)} minutes ({(tomtomResult.summary.travelTimeInSeconds / 3600).toFixed(1)} hours)</p>
              </div>
              <div>
                <p className="text-sm font-medium">Traffic Delay:</p>
                <p className="text-xs text-orange-600 font-medium">+{Math.round(tomtomResult.summary.trafficDelayInSeconds / 60)} min</p>
              </div>
              <div>
                <p className="text-sm font-medium">Estimated Arrival:</p>
                <p className="text-xs">
                  {tomtomResult.summary.arrivalTime 
                    ? new Date(tomtomResult.summary.arrivalTime).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: 'numeric',
                        minute: '2-digit',
                        timeZoneName: 'short'
                      })
                    : 'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* Sunlight Risk Analysis */}
          {sunlightResult && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-300 rounded">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">☀️</span>
                <h4 className="font-semibold text-yellow-900">Sunlight Risk Analysis</h4>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-xs font-medium text-yellow-800">Risk Level:</p>
                  <p className={`text-sm font-bold ${
                    sunlightResult.overall_risk_level === 'Critical' ? 'text-red-600' :
                    sunlightResult.overall_risk_level === 'High' ? 'text-orange-600' :
                    sunlightResult.overall_risk_level === 'Moderate' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {sunlightResult.overall_risk_level}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium text-yellow-800">Risk Score:</p>
                  <p className="text-sm font-bold text-yellow-900">
                    {sunlightResult.overall_risk_score}/100
                  </p>
                </div>
              </div>

              {sunlightResult.recommendations && sunlightResult.recommendations.length > 0 && (
                <div className="space-y-1">
                  {sunlightResult.recommendations.map((rec: string, idx: number) => (
                    <p key={idx} className="text-xs text-yellow-800">
                      {rec}
                    </p>
                  ))}
                </div>
              )}

              {sunlightResult.segments && sunlightResult.segments.length > 1 && (
                <details className="mt-2">
                  <summary className="text-xs font-medium text-yellow-800 cursor-pointer hover:underline">
                    View Segment Details ({sunlightResult.segment_count} segments)
                  </summary>
                  <div className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                    {sunlightResult.segments.map((seg: any, idx: number) => (
                      <div key={idx} className="text-xs p-2 bg-white rounded border border-yellow-200">
                        <div className="font-medium">{seg.segment_name}</div>
                        <div className="text-yellow-700">
                          Risk: {seg.risk_score}/100 ({seg.risk_level})
                        </div>
                        <div className="text-yellow-600 italic">
                          {seg.explanation}
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          )}

          {sunlightLoading && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-300 rounded">
              <p className="text-xs text-yellow-800">☀️ Analyzing sunlight conditions...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
