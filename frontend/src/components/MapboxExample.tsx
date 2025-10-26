import { useEffect, useRef, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import type { Feature, FeatureCollection, Point } from 'geojson';

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
  routeCoordinates?: [number, number][];
}

type CrashRecord = {
  Latitude?: string | null;
  Longitude?: string | null;
  CrashFactId?: string | null;
  Name?: string | null;
  [key: string]: string | null | undefined;
};

type CrashFeature = Feature<Point, {
  crashFactId: string;
  name: string;
}>;

const MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';
const CRASH_DATA_URL = 'http://localhost:5001/api/crash-data';
const CRASH_SOURCE_ID = 'crash-data';
const CRASH_LAYER_ID = 'crash-data-circles';
const ROUTE_SOURCE_ID = 'route';
const ROUTE_LAYER_ID = 'route';

const MapboxExample = ({ origin, destination, stops = [], routeCoordinates }: MapboxExampleProps) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const mapLoadedRef = useRef(false);

  const addCrashLayer = useCallback(async (mapInstance: mapboxgl.Map) => {
    try {
      const response = await fetch(CRASH_DATA_URL);
      const result = await response.json();

      if (!result.success || !Array.isArray(result.data)) {
        console.error('Unexpected crash data response', result);
        return;
      }

      const features: CrashFeature[] = (result.data as CrashRecord[])
        .map((record) => {
          const lat = parseFloat(record.Latitude ?? '');
          const lng = parseFloat(record.Longitude ?? '');

          if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            return null;
          }

          return {
            type: 'Feature',
            properties: {
              crashFactId: record.CrashFactId ?? '',
              name: record.Name ?? ''
            },
            geometry: {
              type: 'Point',
              coordinates: [lng, lat]
            }
          } as CrashFeature;
        })
        .filter((feature): feature is CrashFeature => feature !== null);

      const featureCollection: FeatureCollection<Point> = {
        type: 'FeatureCollection',
        features
      };

      const existingSource = mapInstance.getSource(CRASH_SOURCE_ID) as mapboxgl.GeoJSONSource | undefined;

      if (existingSource) {
        existingSource.setData(featureCollection);
      } else {
        mapInstance.addSource(CRASH_SOURCE_ID, {
          type: 'geojson',
          data: featureCollection
        });

        mapInstance.addLayer({
          id: CRASH_LAYER_ID,
          type: 'circle',
          source: CRASH_SOURCE_ID,
          paint: {
            'circle-radius': 6,
            'circle-color': '#ff5722',
            'circle-opacity': 0.6,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 1
          }
        });
      }

      if (features.length > 0 && !mapInstance.getSource(ROUTE_SOURCE_ID)) {
        const bounds = features.reduce((acc, feature) => {
          return acc.extend(feature.geometry.coordinates as [number, number]);
        }, new mapboxgl.LngLatBounds(
          features[0].geometry.coordinates as [number, number],
          features[0].geometry.coordinates as [number, number]
        ));

        mapInstance.fitBounds(bounds, { padding: 48, maxZoom: 13 });
      }
    } catch (error) {
      console.error('Failed to load crash data', error);
    }
  }, []);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-122.3816, 37.6191],
      zoom: 9
    });

    mapRef.current = map;

    const handleLoad = () => {
      mapLoadedRef.current = true;
      void addCrashLayer(map);
    };

    map.on('load', handleLoad);

    return () => {
      map.off('load', handleLoad);
      map.remove();
      markersRef.current.forEach(marker => marker.remove());
      markersRef.current = [];
    };
  }, [addCrashLayer]);

  useEffect(() => {
    if (!mapRef.current || !mapLoadedRef.current) return;

    const map = mapRef.current;
    const hasRoute = Array.isArray(routeCoordinates) && routeCoordinates.length > 1;

    if (map.getLayer(ROUTE_LAYER_ID)) {
      map.removeLayer(ROUTE_LAYER_ID);
    }

    if (map.getSource(ROUTE_SOURCE_ID)) {
      map.removeSource(ROUTE_SOURCE_ID);
    }

    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    const addMarker = (lng: number, lat: number, color: string, label: string) => {
      const marker = new mapboxgl.Marker({ color })
        .setLngLat([lng, lat])
        .setPopup(new mapboxgl.Popup().setHTML(label))
        .addTo(map);
      markersRef.current.push(marker);
    };

    const extendBounds = (bounds: mapboxgl.LngLatBoundsLike | null, lng: number, lat: number) => {
      const point: [number, number] = [lng, lat];
      if (bounds) {
        (bounds as mapboxgl.LngLatBounds).extend(point);
        return bounds;
      }
      return new mapboxgl.LngLatBounds(point, point);
    };

    let bounds: mapboxgl.LngLatBoundsLike | null = null;

    if (origin) {
      addMarker(origin.coordinates.lng, origin.coordinates.lat, '#22c55e', `<strong>Origin</strong><br/>${origin.address}`);
      bounds = extendBounds(bounds, origin.coordinates.lng, origin.coordinates.lat);
    }

    stops.forEach((stop, index) => {
      addMarker(stop.coordinates.lng, stop.coordinates.lat, '#3b82f6', `<strong>Stop ${index + 1}</strong><br/>${stop.address}`);
      bounds = extendBounds(bounds, stop.coordinates.lng, stop.coordinates.lat);
    });

    if (destination) {
      addMarker(destination.coordinates.lng, destination.coordinates.lat, '#ef4444', `<strong>Destination</strong><br/>${destination.address}`);
      bounds = extendBounds(bounds, destination.coordinates.lng, destination.coordinates.lat);
    }

    if (!hasRoute) {
      if (bounds) {
        map.fitBounds(bounds, { padding: 80, maxZoom: 13 });
      }
      return;
    }

    map.addSource(ROUTE_SOURCE_ID, {
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

    map.addLayer({
      id: ROUTE_LAYER_ID,
      type: 'line',
      source: ROUTE_SOURCE_ID,
      layout: {
        'line-join': 'round',
        'line-cap': 'round'
      },
      paint: {
        'line-color': '#10b981',
        'line-width': 5,
        'line-opacity': 0.75
      }
    });

    if (!bounds && routeCoordinates.length > 0) {
      const [lng, lat] = routeCoordinates[0];
      bounds = new mapboxgl.LngLatBounds([lng, lat], [lng, lat]);
    }

    routeCoordinates.forEach(([lng, lat]) => {
      bounds = extendBounds(bounds, lng, lat);
    });

    if (bounds) {
      map.fitBounds(bounds, { padding: 60, maxZoom: 13 });
    }
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
