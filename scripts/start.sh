#!/bin/bash

# Start script for Ticketmaster Monitor

echo "🎫 Starting Ticketmaster Monitor..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your Twilio credentials before running again."
    exit 1
fi

# Create necessary directories
mkdir -p data logs

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start the container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
    echo "🌐 Web interface: http://localhost:8000"
    echo "📊 Status page: http://localhost:8000/status"
    echo "🏥 Health check: http://localhost:8000/healthz"
else
    echo "❌ Service health check failed. Checking logs..."
    docker-compose logs --tail=20
fi

echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop service: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Run once: docker-compose exec ticketmaster-monitor python -m app.main --once"
echo "  Test SMS: docker-compose exec ticketmaster-monitor python -m app.main --simulate-delta"
