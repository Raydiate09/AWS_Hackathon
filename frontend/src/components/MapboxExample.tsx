import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';

import 'mapbox-gl/dist/mapbox-gl.css';

interface Location {
  address: string;
  coordinates: {
    lat: number;
    lng: number;
  };
}

interface MapboxExampleProps {
  origin?: Location;
  destination?: Location;
  stops?: Location[];
  routeCoordinates?: [number, number][]; // TomTom optimized route
}

const MapboxExample = ({ origin, destination, stops = [], routeCoordinates }: MapboxExampleProps) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const mapLoadedRef = useRef(false);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-122.3816, 37.6191],
      zoom: 9
    });

    mapRef.current.on('load', () => {
      mapLoadedRef.current = true;
    });

    return () => {
      mapRef.current?.remove();
    };
  }, []);

  // Update route when data changes
  useEffect(() => {
    if (!mapRef.current || !mapLoadedRef.current) return;

    const map = mapRef.current;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // ONLY use TomTom route coordinates - no straight lines!
    // Cars must follow real roads, not fly in straight lines
    if (!routeCoordinates || routeCoordinates.length === 0) {
      // No route data - just show markers without connecting lines
      if (origin) {
        const originMarker = new mapboxgl.Marker({ color: '#22c55e' })
          .setLngLat([origin.coordinates.lng, origin.coordinates.lat])
          .setPopup(new mapboxgl.Popup().setHTML(`<strong>Origin</strong><br/>${origin.address}`))
          .addTo(map);
        markersRef.current.push(originMarker);
      }

      if (destination) {
        const destMarker = new mapboxgl.Marker({ color: '#ef4444' })
          .setLngLat([destination.coordinates.lng, destination.coordinates.lat])
          .setPopup(new mapboxgl.Popup().setHTML(`<strong>Destination</strong><br/>${destination.address}`))
          .addTo(map);
        markersRef.current.push(destMarker);
      }

      stops.forEach((stop, index) => {
        const stopMarker = new mapboxgl.Marker({ color: '#3b82f6' })
          .setLngLat([stop.coordinates.lng, stop.coordinates.lat])
          .setPopup(new mapboxgl.Popup().setHTML(`<strong>Stop ${index + 1}</strong><br/>${stop.address}`))
          .addTo(map);
        markersRef.current.push(stopMarker);
      });

      // Fit map to show all markers if we have locations
      if (origin && destination) {
        const bounds = new mapboxgl.LngLatBounds();
        bounds.extend([origin.coordinates.lng, origin.coordinates.lat]);
        bounds.extend([destination.coordinates.lng, destination.coordinates.lat]);
        stops.forEach(stop => bounds.extend([stop.coordinates.lng, stop.coordinates.lat]));
        map.fitBounds(bounds, { padding: 100 });
      }
      
      return; // Don't draw route lines without TomTom data
    }

    const coordinates = routeCoordinates;

    // Remove existing route if any
    if (map.getSource('route')) {
      if (map.getLayer('route')) {
        map.removeLayer('route');
      }
      map.removeSource('route');
    }

    // Add new route
    map.addSource('route', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: coordinates
        }
      }
    });

    map.addLayer({
      id: 'route',
      type: 'line',
      source: 'route',
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': '#10b981', // Green for real road routes
        'line-width': 5,
        'line-opacity': 0.75
      }
    });

    // Add markers only if we have origin/destination (not just coordinates)
    if (origin && destination) {
      const originMarker = new mapboxgl.Marker({ color: '#22c55e' })
        .setLngLat([origin.coordinates.lng, origin.coordinates.lat])
        .setPopup(new mapboxgl.Popup().setHTML(`<strong>Origin</strong><br/>${origin.address}`))
        .addTo(map);
      markersRef.current.push(originMarker);

      stops.forEach((stop, index) => {
        const stopMarker = new mapboxgl.Marker({ color: '#3b82f6' })
          .setLngLat([stop.coordinates.lng, stop.coordinates.lat])
          .setPopup(new mapboxgl.Popup().setHTML(`<strong>Stop ${index + 1}</strong><br/>${stop.address}`))
          .addTo(map);
        markersRef.current.push(stopMarker);
      });

      const destMarker = new mapboxgl.Marker({ color: '#ef4444' })
        .setLngLat([destination.coordinates.lng, destination.coordinates.lat])
        .setPopup(new mapboxgl.Popup().setHTML(`<strong>Destination</strong><br/>${destination.address}`))
        .addTo(map);
      markersRef.current.push(destMarker);
    } else if (coordinates.length > 0) {
      // Just show start/end markers for TomTom route
      const startMarker = new mapboxgl.Marker({ color: '#22c55e' })
        .setLngLat(coordinates[0])
        .addTo(map);
      markersRef.current.push(startMarker);

      if (coordinates.length > 1) {
        const endMarker = new mapboxgl.Marker({ color: '#ef4444' })
          .setLngLat(coordinates[coordinates.length - 1])
          .addTo(map);
        markersRef.current.push(endMarker);
      }
    }

    // Fit map to show all points
    const bounds = new mapboxgl.LngLatBounds();
    coordinates.forEach(coord => bounds.extend(coord as [number, number]));
    map.fitBounds(bounds, { padding: 50 });

  }, [origin, destination, stops, routeCoordinates]);

  return (
    <div
      style={{ height: '100%' }}
      ref={mapContainerRef}
      className="map-container"
    />
  );
};

export default MapboxExample;
