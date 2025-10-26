import { useEffect, useRef } from 'react';
import type { Feature, LineString } from 'geojson';
import mapboxgl from 'mapbox-gl';

import 'mapbox-gl/dist/mapbox-gl.css';

type MapboxExampleProps = {
  coordinates: [number, number][];
};

const ACCESS_TOKEN = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';
const ROUTE_SOURCE_ID = 'route';

const MapboxExample = ({ coordinates }: MapboxExampleProps) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const mapLoadedRef = useRef(false);
  const pendingRouteRef = useRef<[number, number][]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = ACCESS_TOKEN;

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-122.3816, 37.6191],
      zoom: 9,
    });

    mapRef.current.on('load', () => {
      mapLoadedRef.current = true;

      if (pendingRouteRef.current.length) {
        drawRoute(pendingRouteRef.current);
      }
    });

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      mapRef.current?.remove();
    };
  }, []);

  useEffect(() => {
    pendingRouteRef.current = coordinates;

    if (!mapLoadedRef.current) {
      return;
    }

    if (!coordinates.length) {
      clearRoute();
      return;
    }

    drawRoute(coordinates);
  }, [coordinates]);

  const drawRoute = (routeCoordinates: [number, number][]) => {
    if (!mapRef.current) return;

    const map = mapRef.current;

    const data: Feature<LineString> = {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: routeCoordinates,
      },
    };

    const existingSource = map.getSource(ROUTE_SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;

    if (existingSource) {
      existingSource.setData(data);
    } else {
      map.addSource(ROUTE_SOURCE_ID, {
        type: 'geojson',
        data,
      });

      map.addLayer({
        id: ROUTE_SOURCE_ID,
        type: 'line',
        source: ROUTE_SOURCE_ID,
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#3887be',
          'line-width': 5,
          'line-opacity': 0.75,
        },
      });
    }

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    if (routeCoordinates.length) {
      markersRef.current.push(
        new mapboxgl.Marker({ color: '#3bb2d0' }).setLngLat(routeCoordinates[0]).addTo(map),
      );
      if (routeCoordinates.length > 1) {
        markersRef.current.push(
          new mapboxgl.Marker({ color: '#f30' })
            .setLngLat(routeCoordinates[routeCoordinates.length - 1])
            .addTo(map),
        );
      }
    }

    const bounds = routeCoordinates.reduce(
      (acc, coord) => acc.extend(coord as [number, number]),
      new mapboxgl.LngLatBounds(routeCoordinates[0], routeCoordinates[0]),
    );

    map.fitBounds(bounds, { padding: 40, duration: 1000 });
  };

  const clearRoute = () => {
    if (!mapRef.current) return;

    const map = mapRef.current;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    if (map.getLayer(ROUTE_SOURCE_ID)) {
      map.removeLayer(ROUTE_SOURCE_ID);
    }

    if (map.getSource(ROUTE_SOURCE_ID)) {
      map.removeSource(ROUTE_SOURCE_ID);
    }
  };

  return <div style={{ height: '100%' }} ref={mapContainerRef} className="map-container" />;
};

export default MapboxExample;
