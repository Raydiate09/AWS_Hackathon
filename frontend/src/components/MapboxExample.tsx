import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import type { Feature, FeatureCollection, Point } from 'geojson';

import 'mapbox-gl/dist/mapbox-gl.css';

const MAPBOX_TOKEN = 'pk.eyJ1IjoiYW5ndXllbjIxIiwiYSI6ImNtaDZvcXA5eDBlamwycXByOXhvM2d0MnIifQ.jUQ01FBNkQHHZp3for7Pvw';
const CRASH_DATA_URL = 'http://localhost:5001/api/crash-data';
const CRASH_SOURCE_ID = 'crash-data';
const CRASH_LAYER_ID = 'crash-data-circles';

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

const MapboxExample = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      center: [-122.3816, 37.6191],
      zoom: 9
    });

    mapRef.current = map;

    const initializeMap = async (mapInstance: mapboxgl.Map) => {
      const routeCoordinates: [number, number][] = [
        [-122.375, 37.6189],
        [-122.4, 37.65],
        [-122.42, 37.7],
        [-122.45, 37.75],
        [-122.48, 37.78],
        [-122.5, 37.8],
        [-122.52, 37.82],
        [-122.45, 37.78],
        [-122.42, 37.78],
        [-122.4, 37.78],
        [-122.38, 37.78],
        [-122.36, 37.78],
        [-122.34, 37.78],
        [-122.32, 37.78],
        [-122.3, 37.78],
      ];

      if (!mapInstance.getSource('route')) {
        mapInstance.addSource('route', {
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
      }

      if (!mapInstance.getLayer('route')) {
        mapInstance.addLayer({
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
      }

      new mapboxgl.Marker({ color: '#3bb2d0' })
        .setLngLat(routeCoordinates[0])
        .addTo(mapInstance);

      new mapboxgl.Marker({ color: '#f30' })
        .setLngLat(routeCoordinates[routeCoordinates.length - 1])
        .addTo(mapInstance);

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

            const crashFactId = record.CrashFactId ?? '';
            const name = record.Name ?? '';

            return {
              type: 'Feature',
              properties: {
                crashFactId,
                name
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

        if (features.length > 0) {
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
    };

    const handleLoad = () => {
      if (!mapRef.current) return;
      void initializeMap(mapRef.current);
    };

    map.on('load', handleLoad);

    return () => {
      map.off('load', handleLoad);
      map.remove();
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
