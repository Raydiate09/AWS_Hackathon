import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';

import 'mapbox-gl/dist/mapbox-gl.css';

const MapboxExample = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-122.3816, 37.6191], // starting position [lng, lat]
      zoom: 9 // starting zoom
    });

    // Add route once map loads
    mapRef.current.on('load', () => {
      if (!mapRef.current) return;

      // Define route coordinates (example route around San Francisco/SFO area)
      // Format: [longitude, latitude] - longitude first (-180 to 180), latitude second (-90 to 90)
      const routeCoordinates: [number, number][] = [
        [-122.375, 37.6189],  // SFO Airport (San Francisco International Airport)
        [-122.4, 37.65],      // Waypoint near Burlingame
        [-122.42, 37.7],      // Waypoint near San Mateo
        [-122.45, 37.75],     // Waypoint near Pacifica
        [-122.48, 37.78],     // Waypoint near Daly City
        [-122.5, 37.8],       // Waypoint near Colma
        [-122.52, 37.82],     // Waypoint near South SF
        [-122.45, 37.78],     // Back towards SF
        [-122.42, 37.78],     // Inner Sunset area
        [-122.4, 37.78],      // Golden Gate Park area
        [-122.38, 37.78],     // Haight-Ashbury district
        [-122.36, 37.78],     // Mission District
        [-122.34, 37.78],     // SoMa (South of Market)
        [-122.32, 37.78],     // Financial District
        [-122.3, 37.78],      // Embarcadero waterfront
      ];

      // Add GeoJSON source
      mapRef.current.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: routeCoordinates
          }
        }
      });

      // Add line layer to visualize the route
      mapRef.current.addLayer({
        id: 'route',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#3887be',
          'line-width': 5,
          'line-opacity': 0.75
        }
      });

      // Optional: Add markers at start and end points
      new mapboxgl.Marker({ color: '#3bb2d0' })
        .setLngLat(routeCoordinates[0])
        .addTo(mapRef.current);

      new mapboxgl.Marker({ color: '#f30' })
        .setLngLat(routeCoordinates[routeCoordinates.length - 1])
        .addTo(mapRef.current);
    });

    return () => {
      mapRef.current?.remove();
    };
  }, []);

  return (
    <div
      style={{ height: '100%' }}
      ref={mapContainerRef}
      className="map-container"
    />
  );
};

export default MapboxExample;
