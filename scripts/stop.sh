#!/bin/bash

echo "🛑 Stopping Ticketmaster Monitor..."

# Stop and remove containers
docker-compose down

echo "✅ Services stopped."
