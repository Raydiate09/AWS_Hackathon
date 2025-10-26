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
  async getTomTomRoute(route: RouteDetails) {
    const response = await fetch(`${API_BASE_URL}/tomtom-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ route }),
    });
    return response.json();
  },
};
