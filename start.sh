#!/bin/bash

# Quick start script for DTS project
# This script starts both backend and frontend

echo "🚀 Starting DTS Application..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found. Please add your AWS credentials."
    echo ""
fi

# Start backend in background
echo "📡 Starting Flask backend on port 5001..."
source venv/bin/activate
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🎨 Starting React frontend on port 5173..."
cd frontend
npm run dev

# Cleanup on exit
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
