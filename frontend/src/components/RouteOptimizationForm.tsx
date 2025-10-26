import { useMemo, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { LocationInput } from "@/components/ui/location-input";
import { apiService, type OptimizeRouteResponse, type Location } from "@/services/api";

interface RouteOptimizationFormProps {
  onRouteOptimized?: (route: {
    origin: Location;
    destination: Location;
    stops: Location[];
    routeCoordinates?: [number, number][];
    legs?: GoogleRouteLeg[];
    segments?: GoogleRouteSegment[];
  }) => void;
}

interface GoogleRouteSummary {
  distance_meters: number;
  duration_seconds: number;
  duration_in_traffic_seconds?: number;
  waypoint_order?: number[];
}

interface GoogleRouteLeg {
  leg_index: number;
  start_address: string;
  end_address: string;
  start_location: { lat: number; lng: number };
  end_location: { lat: number; lng: number };
  distance_meters: number;
  duration_seconds: number;
  duration_in_traffic_seconds?: number;
  steps_count: number;
  coordinates: [number, number][];
}

interface SegmentWeather {
  description?: string;
  temperature?: number;
  feels_like?: number;
  humidity?: number;
  wind_speed?: number;
  icon?: string;
  timestamp?: number;
}

interface GoogleRouteSegment {
  leg_index: number;
  step_index: number;
  coordinates: [number, number][];
  distance_meters: number;
  duration_seconds: number;
  duration_in_traffic_seconds?: number;
  instruction: string;
  travel_mode: string;
  weather?: SegmentWeather | null;
}

interface GoogleRouteResponse {
  success: boolean;
  coordinates: [number, number][];
  summary?: GoogleRouteSummary;
  error?: string;
  message?: string;
  segments?: GoogleRouteSegment[];
  legs?: GoogleRouteLeg[];
}

interface SunlightSegment {
  segment_name: string;
  risk_score: number;
  risk_level: string;
  explanation: string;
}

interface SunlightRiskResult {
  overall_risk_level: string;
  overall_risk_score: number;
  segment_count?: number;
  segments?: SunlightSegment[];
  recommendations?: string[];
}

export function RouteOptimizationForm({ onRouteOptimized }: RouteOptimizationFormProps) {
  const [loading, setLoading] = useState(false);
  const [routeLoading, setRouteLoading] = useState(false);
  const [sunlightLoading, setSunlightLoading] = useState(false);
  const [result, setResult] = useState<OptimizeRouteResponse | null>(null);
  const [routeResult, setRouteResult] = useState<GoogleRouteResponse | null>(null);
  const [sunlightResult, setSunlightResult] = useState<SunlightRiskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [destinationTimezone, setDestinationTimezone] = useState<string | null>(null);

  const travelSeconds = useMemo(() => {
    if (!routeResult?.summary) {
      return 0;
    }
    const durationWithTraffic = routeResult.summary.duration_in_traffic_seconds;
    const baseDuration = routeResult.summary.duration_seconds;
    return (durationWithTraffic ?? baseDuration ?? 0);
  }, [routeResult]);

  const hasSegmentWeather = useMemo(() => {
    return Boolean(routeResult?.segments?.some((segment) => segment?.weather));
  }, [routeResult?.segments]);
  
  // Form inputs using Location objects
  const [origin, setOrigin] = useState<Location>({
    address: "San Jose State University, San Jose, CA",
    coordinates: { lat: 37.3352, lng: -121.8811 }
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

  const departureTimeForWeather = useMemo(() => {
    if (!preferredStartTime) {
      return new Date();
    }

    const parsed = new Date(preferredStartTime);
    if (Number.isNaN(parsed.getTime())) {
      return new Date();
    }

    return parsed;
  }, [preferredStartTime]);

  const formatTemperature = (temp?: number | null) => {
    if (typeof temp !== "number" || Number.isNaN(temp)) {
      return "—";
    }
    const fahrenheit = (temp * 9) / 5 + 32;
    return `${temp.toFixed(1)}°C / ${fahrenheit.toFixed(1)}°F`;
  };

  const formatWind = (speed?: number | null) => {
    if (typeof speed !== "number" || Number.isNaN(speed)) {
      return "—";
    }
    const mph = speed * 2.23694;
    return `${speed.toFixed(1)} m/s (${mph.toFixed(1)} mph)`;
  };

  const formatSegmentWindow = (start: Date, end: Date) => {
    const formatter = new Intl.DateTimeFormat(undefined, {
      hour: "numeric",
      minute: "2-digit"
    });
    return `${formatter.format(start)} – ${formatter.format(end)}`;
  };

  const formatForecastTimestamp = (timestamp?: number) => {
    if (!timestamp) {
      return "Forecast time unavailable";
    }
    const dt = new Date(timestamp * 1000);
    return dt.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  };

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
        setSunlightResult(response.data as SunlightRiskResult);
      }
    } catch (err) {
      console.error("Sunlight risk error:", err);
      // Don't show error to user, sunlight is optional enhancement
    } finally {
      setSunlightLoading(false);
    }
  };

  const handleGoogleMapsRoute = async () => {
    setRouteLoading(true);
    setError(null);
  setRouteResult(null);
    setSunlightResult(null);

    try {
      // Fetch destination timezone for accurate arrival time display
      try {
        const tzResponse = await apiService.getTimezone(
          destination.coordinates.lat,
          destination.coordinates.lng
        );
        if (tzResponse.success) {
          setDestinationTimezone(tzResponse.timezone);
        }
      } catch (tzErr) {
        console.warn('Could not fetch timezone:', tzErr);
        // Continue without timezone, will use default
      }

      // Only send times if they have actual values
      const startTime = preferredStartTime ? preferredStartTime : undefined;
      const arrivalTime = preferredArrivalTime ? preferredArrivalTime : undefined;
      
      console.log('Sending times:', { startTime, arrivalTime });
      
      const response = await apiService.getGoogleMapsRoute(
        {
          origin,
          destination,
          stops
        },
        startTime,
        arrivalTime
      ) as GoogleRouteResponse;

      // Check for errors
      if (!response.success) {
        setError(response.error || response.message || "Failed to get Google route");
        return;
      }

      setRouteResult(response);
      
      // Validate arrival time AFTER getting the route if we have enough info
      if (preferredArrivalTime) {
        const requiredArrival = new Date(preferredArrivalTime);
        const responseTravelSeconds = response.summary?.duration_in_traffic_seconds ?? response.summary?.duration_seconds;
        
        // Get departure time for validation (use provided or auto-generated current time)
        let departureForValidation: Date | null = null;
        if (preferredStartTime) {
          departureForValidation = new Date(preferredStartTime);
        } else {
          // Use current time for validation when not explicitly provided
          departureForValidation = new Date();
        }

        if (responseTravelSeconds && departureForValidation) {
          const estimatedArrival = new Date(departureForValidation.getTime() + responseTravelSeconds * 1000);

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
            setRouteLoading(false);
            return;
          }
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
      
      // Notify parent component to update map with Google route
      if (onRouteOptimized && response.success) {
        onRouteOptimized({
          origin,
          destination,
          stops,
          routeCoordinates: response.coordinates,
          legs: response.legs,
          segments: response.segments
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get Google route");
      console.error("Google Maps error:", err);
    } finally {
      setRouteLoading(false);
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
          onClick={handleGoogleMapsRoute} 
          disabled={routeLoading || loading || !origin.address || !destination.address}
          className="w-full"
          variant="default"
        >
          {routeLoading ? "Loading Route..." : "Show Route on Map"}
        </Button>
        
        <Button 
          onClick={handleOptimize} 
          disabled={loading || routeLoading || !origin.address || !destination.address}
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

      {!result && !routeResult && !error && (
        <div className="p-4 bg-amber-50 border border-amber-300 rounded-md">
          <p className="text-sm font-semibold text-amber-900 mb-2">
            🚗 Click "Show Route on Map" to display the real driving route
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
              This may be due to missing Google Maps API key. Check backend/.env file and ensure GOOGLE_MAPS_API_KEY is set.
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

      {routeResult && routeResult.success && (
        <div className="space-y-4 p-4 bg-green-50 border border-green-300 rounded-md">
          <h3 className="font-semibold text-green-900">✅ Real Driving Route Displayed</h3>
          
          <p className="text-sm text-green-800">
            Green line on map shows the actual road network route with real-time traffic data
          </p>
          
          {routeResult.summary && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium">Driving Distance:</p>
                <p className="text-xs">{(routeResult.summary.distance_meters * 0.000621371).toFixed(2)} miles</p>
              </div>
              <div>
                <p className="text-sm font-medium">Travel Time:</p>
                <p className="text-xs">{Math.round(travelSeconds / 60)} minutes ({(travelSeconds / 3600).toFixed(1)} hours)</p>
              </div>
              <div>
                <p className="text-sm font-medium">Estimated Arrival (at destination):</p>
                <p className="text-xs">
                  {travelSeconds
                    ? (() => {
                        // Use preferred start time if provided, otherwise use current time
                        const startDateTime = preferredStartTime
                          ? new Date(preferredStartTime)
                          : new Date();
                        const arrivalTime = new Date(startDateTime.getTime() + (travelSeconds * 1000));
                        
                        // Use fetched destination timezone, fallback to America/New_York for coast-to-coast
                        const tz = destinationTimezone || 'America/New_York';
                        
                        // Format in destination timezone using Intl API
                        const formatter = new Intl.DateTimeFormat('en-US', {
                          timeZone: tz,
                          month: 'short',
                          day: 'numeric',
                          hour: 'numeric',
                          minute: '2-digit',
                          second: '2-digit',
                          timeZoneName: 'short'
                        });
                        return formatter.format(arrivalTime);
                      })()
                    : 'Load route to estimate arrival'}
                </p>
              </div>
            </div>
          )}

          {hasSegmentWeather && routeResult.segments && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg" role="img" aria-label="weather">🌦️</span>
                <h4 className="font-semibold text-blue-900">Segment Weather Forecasts</h4>
              </div>
              <p className="text-xs text-blue-800 mb-3">
                Conditions reflect the expected weather as you enter each segment based on your current departure time.
              </p>
              <div className="space-y-3">
                {(() => {
                  const segments = routeResult.segments ?? [];
                  const cards: ReactNode[] = [];
                  let accumulatedSeconds = 0;

                  segments.forEach((segment, idx) => {
                    const segmentDuration = segment.duration_seconds ?? 0;
                    const segmentStart = new Date(departureTimeForWeather.getTime() + accumulatedSeconds * 1000);
                    const segmentEnd = new Date(segmentStart.getTime() + segmentDuration * 1000);
                    const weather = segment.weather;

                    if (weather) {
                      const key = `segment-weather-${segment.leg_index}-${segment.step_index}`;
                      cards.push(
                        <div
                          key={key}
                          className="p-3 bg-white border border-blue-100 rounded-md shadow-sm"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="text-sm font-semibold text-blue-900">Segment {idx + 1}</p>
                              {segment.instruction && (
                                <p
                                  className="text-xs text-blue-700 mt-1"
                                  dangerouslySetInnerHTML={{ __html: segment.instruction }}
                                />
                              )}
                            </div>
                            <div className="flex flex-col items-end text-xs text-blue-700">
                              <p>{formatSegmentWindow(segmentStart, segmentEnd)}</p>
                              <p>
                                {(segmentDuration / 60) >= 1
                                  ? `${Math.round(segmentDuration / 60)} min`
                                  : '< 1 min'}
                              </p>
                            </div>
                            {weather.icon && (
                              <img
                                src={`https://openweathermap.org/img/wn/${weather.icon}@2x.png`}
                                alt={weather.description ?? 'segment weather icon'}
                                className="w-12 h-12"
                              />
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-3 mt-3 text-xs text-blue-900">
                            <div>
                              <p className="font-medium">Conditions</p>
                              <p className="capitalize">{weather.description ?? 'Not available'}</p>
                            </div>
                            <div>
                              <p className="font-medium">Forecast Issued</p>
                              <p>{formatForecastTimestamp(weather.timestamp)}</p>
                            </div>
                            <div>
                              <p className="font-medium">Temperature</p>
                              <p>{formatTemperature(weather.temperature)}</p>
                            </div>
                            <div>
                              <p className="font-medium">Feels Like</p>
                              <p>{formatTemperature(weather.feels_like)}</p>
                            </div>
                            <div>
                              <p className="font-medium">Humidity</p>
                              <p>{typeof weather.humidity === 'number' ? `${weather.humidity}%` : '—'}</p>
                            </div>
                            <div>
                              <p className="font-medium">Wind</p>
                              <p>{formatWind(weather.wind_speed)}</p>
                            </div>
                          </div>
                        </div>
                      );
                    }

                    accumulatedSeconds += segmentDuration;
                  });

                  if (cards.length === 0) {
                    return (
                      <p className="text-xs text-blue-700">
                        Weather data is unavailable for this route at the moment.
                      </p>
                    );
                  }

                  return cards;
                })()}
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
                    {sunlightResult.segments.map((seg: SunlightSegment, idx: number) => (
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
