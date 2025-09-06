#!/bin/bash

# Smart Health System Startup Script
# Starts both backend and frontend services

set -e

echo "🚀 Starting Smart Health System"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the ha-part2 root directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check backend port
if check_port 8001; then
    print_warning "Backend port 8001 is already in use"
    echo "Existing backend process found. Continuing..."
else
    print_status "Starting backend server..."
    
    # Check if backend dependencies are installed
    if [ ! -f "backend/requirements.txt" ]; then
        print_error "Backend requirements.txt not found"
        exit 1
    fi
    
    # Start backend in background
    cd backend
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    print_status "Starting FastAPI server on port 8001..."
    uvicorn app.main:app --reload --port 8001 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
            print_success "Backend started successfully!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start within 30 seconds"
            print_error "Check backend.log for details"
            exit 1
        fi
        sleep 1
    done
fi

# Check frontend port
if check_port 8501; then
    print_warning "Frontend port 8501 is already in use"
    echo "Existing frontend process found. You can access it at http://localhost:8501"
else
    print_status "Starting frontend server..."
    
    # Check if frontend dependencies are installed
    if [ ! -f "frontend/requirements.txt" ]; then
        print_error "Frontend requirements.txt not found"
        exit 1
    fi
    
    # Start frontend
    cd frontend
    print_status "Installing frontend dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    print_status "Testing backend connection..."
    if python3 test_connection.py > /dev/null 2>&1; then
        print_success "Backend connection test passed!"
    else
        print_warning "Backend connection test failed, but continuing..."
    fi
    
    print_status "Starting Streamlit server on port 8501..."
    streamlit run streamlit_app.py > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    print_status "Waiting for frontend to start..."
    for i in {1..20}; do
        if curl -s http://localhost:8501 > /dev/null 2>&1; then
            print_success "Frontend started successfully!"
            break
        fi
        if [ $i -eq 20 ]; then
            print_error "Frontend failed to start within 20 seconds"
            print_error "Check frontend.log for details"
            exit 1
        fi
        sleep 1
    done
fi

echo ""
echo "🎉 Smart Health System is now running!"
echo "======================================"
echo ""
echo "📊 Backend API:"
echo "   URL: http://127.0.0.1:8001"
echo "   Docs: http://127.0.0.1:8001/docs"
echo "   Health: http://127.0.0.1:8001/health"
echo ""
echo "🖥️  Frontend App:"
echo "   URL: http://localhost:8501"
echo ""
echo "📝 Logs:"
echo "   Backend: backend.log"
echo "   Frontend: frontend.log"
echo ""
echo "🛑 To stop the services:"
echo "   Press Ctrl+C or run: pkill -f 'uvicorn\\|streamlit'"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "Services stopped"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Keep script running and show logs
print_status "System is running. Press Ctrl+C to stop."
print_status "Showing live logs (Ctrl+C to stop)..."
echo ""

# Show logs from both services
tail -f backend.log frontend.log 2>/dev/null || {
    print_warning "Could not show logs. Services are running in background."
    print_status "Check backend.log and frontend.log for details."
    
    # Just wait for user interrupt
    while true; do
        sleep 1
    done
}
