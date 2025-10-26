import { useState, useEffect, useRef } from "react";
import { type Location } from "@/services/api";

interface LocationInputProps {
  label: string;
  value: Location;
  onChange: (location: Location) => void;
  placeholder?: string;
}

interface MapboxFeature {
  id: string;
  place_name: string;
  center: [number, number]; // [lng, lat]
  text: string;
}

const MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';

export function LocationInput({ label, value, onChange, placeholder = "Search for a location..." }: LocationInputProps) {
  const [query, setQuery] = useState(value.address || "");
  const [suggestions, setSuggestions] = useState<MapboxFeature[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounce geocoding search
  useEffect(() => {
    if (!query || query.length < 3) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${MAPBOX_TOKEN}&autocomplete=true&limit=5`
        );
        const data = await response.json();
        setSuggestions(data.features || []);
        setIsOpen(true);
      } catch (error) {
        console.error("Geocoding error:", error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (feature: MapboxFeature) => {
    const [lng, lat] = feature.center;
    onChange({
      address: feature.place_name,
      coordinates: { lat, lng }
    });
    setQuery(feature.place_name);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    setQuery(newQuery);
    
    // Clear location if user clears the input
    if (!newQuery) {
      onChange({
        address: "",
        coordinates: { lat: 0, lng: 0 }
      });
    }
  };

  return (
    <div className="space-y-2" ref={wrapperRef}>
      <label className="text-sm font-medium">{label}</label>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => suggestions.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
          </div>
        )}

        {isOpen && suggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border rounded-md shadow-lg max-h-60 overflow-auto">
            {suggestions.map((feature) => (
              <button
                key={feature.id}
                onClick={() => handleSelect(feature)}
                className="w-full text-left px-4 py-2 hover:bg-blue-50 border-b last:border-b-0 focus:bg-blue-50 focus:outline-none transition-colors"
              >
                <div className="font-medium text-sm">{feature.text}</div>
                <div className="text-xs text-gray-500">{feature.place_name}</div>
              </button>
            ))}
          </div>
        )}
      </div>
      
      {value.coordinates.lat !== 0 && value.coordinates.lng !== 0 && (
        <div className="text-xs text-gray-500 flex gap-2">
          <span>📍 {value.coordinates.lat.toFixed(4)}, {value.coordinates.lng.toFixed(4)}</span>
        </div>
      )}
    </div>
  );
}
