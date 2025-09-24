#!/bin/bash

echo "🧪 Running Ticketmaster Monitor tests..."

# Run monitoring once
echo "1. Testing single monitoring cycle..."
docker-compose exec ticketmaster-monitor python -m app.main --once --dry-run

echo ""
echo "2. Testing SMS simulation..."
docker-compose exec ticketmaster-monitor python -m app.main --simulate-delta --dry-run

echo ""
echo "3. Checking health endpoint..."
curl -s http://localhost:8000/healthz | python -m json.tool

echo ""
echo "4. Checking metrics endpoint..."
curl -s http://localhost:8000/metrics | python -m json.tool

echo ""
echo "✅ Tests completed!"
