// API Service for connecting to Flask backend

const API_BASE_URL = 'http://localhost:5001/api';

export interface Location {
  address: string;
  coordinates: {
    lat: number;
    lng: number;
  };
}

export interface RouteDetails {
  origin: Location;
  destination: Location;
  stops: Location[];
}

export interface OptimizeRouteRequest {
  userId: string;
  route: RouteDetails;
  deliveryWindow: {
    startDate: string;
    endDate: string;
  };
}

export interface OptimizeRouteResponse {
  success: boolean;
  data: {
    requestId: string;
    optimizedRoute: RouteDetails & {
      recommendedDepartureTime: string;
      estimatedArrivalTime: string;
    };
    metrics: {
      distance: number;
      estimatedTime: string;
      scores: {
        weather: number;
        traffic: number;
        sunlight: number;
        overall: number;
      };
    };
    recommendations: string[];
    departureTime: string;
    arrivalTime: string;
  };
}

export const apiService = {
  // Health check
  async healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  // Optimize route
  async optimizeRoute(data: OptimizeRouteRequest): Promise<OptimizeRouteResponse> {
    const response = await fetch(`${API_BASE_URL}/optimize-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // Get request by ID
  async getRequest(requestId: string) {
    const response = await fetch(`${API_BASE_URL}/request/${requestId}`);
    return response.json();
  },

  // Get user requests
  async getUserRequests(userId: string, limit = 20) {
    const response = await fetch(`${API_BASE_URL}/user/${userId}/requests?limit=${limit}`);
    return response.json();
  },

  // Validate route
  async validateRoute(route: RouteDetails) {
    const response = await fetch(`${API_BASE_URL}/validate-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ route }),
    });
    return response.json();
  },

  // TomTom route optimization
  async getTomTomRoute(route: RouteDetails, preferredStartTime?: string, preferredArrivalTime?: string) {
    const payload = { 
      route,
      preferred_start_time: preferredStartTime,
      preferred_arrival_time: preferredArrivalTime
    };
    
    console.log('TomTom API Request:', payload);
    
    const response = await fetch(`${API_BASE_URL}/tomtom-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    // Parse the JSON response regardless of status code
    const data = await response.json();
    
    console.log('TomTom API Response:', { status: response.status, ok: response.ok, data });
    
    // If the response is not ok (400, 500, etc.), return the error data
    if (!response.ok) {
      return data;
    }
    
    return data;
  },

  // Google Maps route optimization
  async getGoogleMapsRoute(route: RouteDetails, preferredStartTime?: string, preferredArrivalTime?: string) {
    const payload = {
      route,
      preferred_start_time: preferredStartTime,
      preferred_arrival_time: preferredArrivalTime
    };

    console.log('Google Maps API Request:', payload);

    const response = await fetch(`${API_BASE_URL}/google-maps-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    console.log('Google Maps API Response:', { status: response.status, ok: response.ok, data });

    if (!response.ok) {
      return data;
    }

    return data;
  },

  // Get timezone for a location
  async getTimezone(lat: number, lng: number) {
    const response = await fetch(`${API_BASE_URL}/timezone`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ lat, lng }),
    });
    return response.json();
  },

  // Sunlight risk analysis
  async getSunlightRisk(data: {
    origin: { lat: number; lng: number };
    destination: { lat: number; lng: number };
    departure_time?: string;
    route_coordinates?: [number, number][];
  }) {
    const response = await fetch(`${API_BASE_URL}/sunlight-risk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async analyzeCrashProximity(data: {
    segments: Array<{
      leg_index?: number;
      step_index?: number;
      coordinates: [number, number][];
      distance_meters?: number;
      duration_seconds?: number;
      duration_in_traffic_seconds?: number;
      instruction?: string;
      travel_mode?: string;
    }>;
    threshold_meters?: number;
    max_crashes_per_segment?: number;
  }) {
    const response = await fetch(`${API_BASE_URL}/crash-proximity`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },
};
