# DTS - Delivery Time Slot Optimization

An intelligent delivery route optimization system that combines real-time traffic data with AI-powered recommendations to help delivery services choose optimal routes and departure times.

## 🚀 Features

### 🗺️ Real Road-Based Routing
- **TomTom Integration**: Routes follow actual road networks, highways, and streets
- **Real-Time Traffic**: Current traffic conditions included in route calculations
- **Smart Waypoint Optimization**: Automatically reorders stops for the shortest route
- **Accurate Estimates**: Real driving distance, travel time, and traffic delays

### 🤖 AI-Powered Recommendations
- **AWS Bedrock Claude AI**: Intelligent route and timing analysis
- **Multi-Factor Optimization**: Considers weather, traffic patterns, and sunlight conditions
- **Departure Time Suggestions**: Recommends optimal times to start delivery
- **Contextual Advice**: Provides actionable insights for delivery planning

### 📊 Interactive Dashboard
- **Mapbox Visualization**: Interactive map with real route display
- **Delivery Calendar**: Select delivery time windows
- **Progress Tracking**: Real-time delivery status with stepper component
- **Metrics Dashboard**: Distance, time, traffic delays, and scores

## 🛠️ Tech Stack

### Backend
- **Python 3.x** - Core language
- **Flask 3.0.0** - Web framework
- **AWS Bedrock** - Claude AI integration (model: anthropic.claude-haiku-4-5)
- **AWS DynamoDB** - Data persistence (table: optimizedRoute)
- **TomTom Routing API** - Traffic-aware routing
- **boto3 1.40.55** - AWS SDK

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite 7.1.12** - Build tool & dev server
- **Mapbox GL 3.16.0** - Interactive maps
- **shadcn/ui** - UI components
- **Tailwind CSS** - Styling

## 📁 Project Structure

```
DTS/
├── backend/
│   ├── app.py                 # Flask application with all API endpoints
│   ├── tomtom_service.py      # TomTom API integration
│   ├── aws_s3.py              # S3 utilities
│   ├── aws_dynamo.py          # DynamoDB operations
│   ├── test_api.py            # API testing script
│   └── .env                   # Environment variables (not in git)
├── frontend/
│   ├── src/
│   │   ├── App.tsx            # Main application
│   │   ├── components/
│   │   │   ├── MapboxExample.tsx           # Map with TomTom routes
│   │   │   ├── RouteOptimizationForm.tsx   # Input form
│   │   │   └── ui/                         # shadcn components
│   │   └── services/
│   │       └── api.ts         # Backend API service
│   ├── package.json           # Node dependencies
│   └── vite.config.ts         # Vite configuration
├── requirements.txt           # Unified Python dependencies
├── venv/                      # Python virtual environment
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Setup Instructions

### 1. Install Python Dependencies

From the project root:

```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `backend/.env` and add your credentials:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"

# TomTom API Key (get from https://developer.tomtom.com/)
TOMTOM_API_KEY="your_tomtom_api_key"
```

**Important**: Never commit `.env` to version control!

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 🚀 Running the Application

### Start Backend (Terminal 1)

```bash
# From project root
source venv/bin/activate
cd backend
python app.py
```

Backend runs on: **http://localhost:5001**

### Start Frontend (Terminal 2)

```bash
# From project root
cd frontend
npm run dev
```

Frontend runs on: **http://localhost:5173** (or next available port)

## 📖 Usage Guide

### 1. Enter Route Details

**Origin** (default: SFO Airport)
- Address: San Francisco International Airport, CA
- Coordinates: Lat 37.6213, Lng -122.3790

**Destination** (default: Santa Clara University)
- Address: Santa Clara University, Santa Clara, CA
- Coordinates: Lat 37.3496, Lng -121.9390

**Add Stops** (optional)
- Click "Add Stop" to include waypoints
- Reordered automatically for optimal route

### 2. View Real Route on Map

Click **"Show Route on Map"**:
- ✅ Fetches real driving route from TomTom
- ✅ Green line follows actual roads with traffic
- ✅ Shows driving distance, travel time, traffic delays
- ✅ Displays estimated arrival time

### 3. Get AI Recommendations

Click **"Get AI Recommendations"**:
- ✅ Claude AI analyzes route with weather/traffic/sunlight
- ✅ Provides optimal departure time
- ✅ Offers contextual delivery advice

### 4. Track Progress

Use the delivery progress stepper to monitor:
- Current delivery status
- Completed stops
- Upcoming waypoints

## 🎨 Visual Legend

| Symbol | Meaning |
|--------|---------|
| 🟢 Green Line | Real road route with traffic data |
| 🟢 Green Marker | Origin/Start point |
| 🔵 Blue Markers | Intermediate stops |
| � Red Marker | Destination/End point |

## 🔑 API Endpoints

### TomTom Route
```
POST /api/tomtom-route
Body: { "route": { "origin": {...}, "destination": {...}, "stops": [...] }}
Response: { "success": true, "coordinates": [[lng,lat],...], "summary": {...} }
```

### AI Optimization
```
POST /api/optimize-route
Body: { "userId": "...", "route": {...}, "deliveryWindow": {...} }
Response: { "success": true, "data": { "optimizedRoute": {...}, "metrics": {...} }}
```

### Health Check
```
GET /api/health
Response: { "status": "healthy", "timestamp": "..." }
```

### Validate Route
```
POST /api/validate-route
Body: { "route": {...} }
Response: { "valid": true, "message": "..." }
```

## 🧪 Testing

### Test Backend API

```bash
# From backend directory with venv activated
cd backend
python test_api.py
```

### Manual Testing
1. Start both servers (backend + frontend)
2. Open http://localhost:5173 in browser
3. Click "Show Route on Map" with default values
4. Verify green route appears on map
5. Check distance and time metrics

## 🐛 Troubleshooting

### Backend Issues

**Port 5001 already in use**
```bash
lsof -ti:5001 | xargs kill -9
```

**Module not found errors**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**TomTom route not loading**
- Check `TOMTOM_API_KEY` is set in `backend/.env`
- Verify backend terminal for API errors
- Test API key on TomTom developer portal

### Frontend Issues

**Map not displaying**
- Check Mapbox access token in `MapboxExample.tsx`
- Verify internet connection
- Check browser console for errors

**Route not showing**
- Ensure backend is running on port 5001
- Check browser Network tab for failed API calls
- Verify coordinates are valid numbers

## 📊 AWS Services Used

### AWS Bedrock
- **Model**: anthropic.claude-haiku-4-5-20251001-v1:0
- **Purpose**: Route optimization AI recommendations
- **Region**: us-east-1

### AWS DynamoDB
- **Table**: optimizedRoute
- **Purpose**: Store optimization requests/results
- **Key Schema**: userId (partition), requestId (sort)

## 🔒 Security Notes

- Never commit `.env` files to version control
- Use different credentials for dev/production
- Rotate API keys regularly
- Use IAM roles with minimal permissions
- Monitor AWS usage in CloudWatch

## 🔮 Future Enhancements

- [ ] Multi-vehicle route optimization
- [ ] Historical traffic pattern analysis
- [ ] Real-time weather API integration
- [ ] Mobile app for delivery drivers
- [ ] Customer notification system
- [ ] Proof of delivery with photos
- [ ] Route replay and analytics
- [ ] Integration with logistics platforms

## 📄 License

This project is part of AWS Hackathon 2025.

## 🙏 Acknowledgments

- AWS Bedrock for AI services
- TomTom for routing APIs
- Mapbox for map visualization
- shadcn/ui for UI components

---

**Built with ❤️ for AWS Hackathon 2025**

For detailed integration docs, see `/TOMTOM_INTEGRATION.md`
