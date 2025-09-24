#!/bin/bash

echo "📋 Showing Ticketmaster Monitor logs..."
echo "Press Ctrl+C to exit"
echo ""

# Follow logs
docker-compose logs -f
