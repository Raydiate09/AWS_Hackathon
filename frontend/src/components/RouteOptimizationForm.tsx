import { useState } from "react";
import { Button } from "@/components/ui/button";
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
  const [result, setResult] = useState<OptimizeRouteResponse | null>(null);
  const [tomtomResult, setTomtomResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Form inputs
  const [originAddress, setOriginAddress] = useState("San Francisco International Airport, CA");
  const [originLat, setOriginLat] = useState("37.6213");
  const [originLng, setOriginLng] = useState("-122.3790");
  
  const [destAddress, setDestAddress] = useState("Santa Clara University, Santa Clara, CA");
  const [destLat, setDestLat] = useState("37.3496");
  const [destLng, setDestLng] = useState("-121.9390");
  
  const [stops, setStops] = useState<Location[]>([]);
  const [newStopAddress, setNewStopAddress] = useState("");
  const [newStopLat, setNewStopLat] = useState("");
  const [newStopLng, setNewStopLng] = useState("");

  const addStop = () => {
    if (newStopAddress && newStopLat && newStopLng) {
      const newStop: Location = {
        address: newStopAddress,
        coordinates: {
          lat: parseFloat(newStopLat),
          lng: parseFloat(newStopLng)
        }
      };
      setStops([...stops, newStop]);
      setNewStopAddress("");
      setNewStopLat("");
      setNewStopLng("");
    }
  };

  const removeStop = (index: number) => {
    setStops(stops.filter((_, i) => i !== index));
  };

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);

    try {
      const origin: Location = {
        address: originAddress,
        coordinates: { lat: parseFloat(originLat), lng: parseFloat(originLng) }
      };
      
      const destination: Location = {
        address: destAddress,
        coordinates: { lat: parseFloat(destLat), lng: parseFloat(destLng) }
      };

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
      const origin: Location = {
        address: originAddress,
        coordinates: { lat: parseFloat(originLat), lng: parseFloat(originLng) }
      };
      
      const destination: Location = {
        address: destAddress,
        coordinates: { lat: parseFloat(destLat), lng: parseFloat(destLng) }
      };

      const response = await apiService.getTomTomRoute({
        origin,
        destination,
        stops
      });

      setTomtomResult(response);
      
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

  return (
    <div className="p-6 border rounded-lg space-y-4">
      <h2 className="text-2xl font-bold">Route Optimization</h2>
      
      {/* Origin Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Origin</label>
        <input
          type="text"
          value={originAddress}
          onChange={(e) => setOriginAddress(e.target.value)}
          placeholder="Address"
          className="w-full p-2 border rounded"
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            value={originLat}
            onChange={(e) => setOriginLat(e.target.value)}
            placeholder="Latitude"
            step="0.0001"
            className="p-2 border rounded text-sm"
          />
          <input
            type="number"
            value={originLng}
            onChange={(e) => setOriginLng(e.target.value)}
            placeholder="Longitude"
            step="0.0001"
            className="p-2 border rounded text-sm"
          />
        </div>
      </div>

      {/* Destination Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Destination</label>
        <input
          type="text"
          value={destAddress}
          onChange={(e) => setDestAddress(e.target.value)}
          placeholder="Address"
          className="w-full p-2 border rounded"
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            value={destLat}
            onChange={(e) => setDestLat(e.target.value)}
            placeholder="Latitude"
            step="0.0001"
            className="p-2 border rounded text-sm"
          />
          <input
            type="number"
            value={destLng}
            onChange={(e) => setDestLng(e.target.value)}
            placeholder="Longitude"
            step="0.0001"
            className="p-2 border rounded text-sm"
          />
        </div>
      </div>

      {/* Stops */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Stops ({stops.length})</label>
        {stops.map((stop, index) => (
          <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
            <div className="flex-1 text-sm">
              <div className="font-medium">{stop.address}</div>
              <div className="text-xs text-muted-foreground">
                {stop.coordinates.lat}, {stop.coordinates.lng}
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
          <input
            type="text"
            value={newStopAddress}
            onChange={(e) => setNewStopAddress(e.target.value)}
            placeholder="Stop address"
            className="w-full p-2 border rounded text-sm"
          />
          <div className="grid grid-cols-3 gap-2">
            <input
              type="number"
              value={newStopLat}
              onChange={(e) => setNewStopLat(e.target.value)}
              placeholder="Lat"
              step="0.0001"
              className="p-2 border rounded text-sm"
            />
            <input
              type="number"
              value={newStopLng}
              onChange={(e) => setNewStopLng(e.target.value)}
              placeholder="Lng"
              step="0.0001"
              className="p-2 border rounded text-sm"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={addStop}
              disabled={!newStopAddress || !newStopLat || !newStopLng}
            >
              Add Stop
            </Button>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2">
        <Button 
          onClick={handleTomTomOptimize} 
          disabled={tomtomLoading || loading}
          className="w-full"
          variant="default"
        >
          {tomtomLoading ? "Loading Route..." : "Show Route on Map"}
        </Button>
        
        <Button 
          onClick={handleOptimize} 
          disabled={loading || tomtomLoading}
          className="w-full"
          variant="outline"
        >
          {loading ? "Analyzing..." : "Get AI Recommendations"}
        </Button>
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
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800 text-sm font-semibold mb-2">⚠️ Unable to load route</p>
          <p className="text-red-700 text-xs mb-2">{error}</p>
          <p className="text-red-600 text-xs">
            This may be due to missing TomTom API key. Check backend/.env file and ensure TOMTOM_API_KEY is set.
          </p>
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
              <p className="text-xs">{result.data.metrics.distance} km</p>
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
                <p className="text-xs">{(tomtomResult.summary.lengthInMeters / 1000).toFixed(2)} km</p>
              </div>
              <div>
                <p className="text-sm font-medium">Travel Time:</p>
                <p className="text-xs">{Math.round(tomtomResult.summary.travelTimeInSeconds / 60)} minutes</p>
              </div>
              <div>
                <p className="text-sm font-medium">Traffic Delay:</p>
                <p className="text-xs text-orange-600 font-medium">+{Math.round(tomtomResult.summary.trafficDelayInSeconds / 60)} min</p>
              </div>
              <div>
                <p className="text-sm font-medium">Estimated Arrival:</p>
                <p className="text-xs">{new Date(tomtomResult.summary.arrivalTime).toLocaleTimeString()}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
