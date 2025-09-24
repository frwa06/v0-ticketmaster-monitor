#!/bin/bash

echo "🔧 Setting up Ticketmaster Monitor..."

# Make scripts executable
chmod +x scripts/*.sh

# Check system requirements
echo "📋 Checking system requirements..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your Twilio credentials:"
    echo "   - TWILIO_ACCOUNT_SID"
    echo "   - TWILIO_AUTH_TOKEN" 
    echo "   - TWILIO_FROM_NUMBER"
    echo ""
    echo "   You can get these from: https://console.twilio.com/"
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p data logs

echo ""
echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your Twilio credentials"
echo "2. Run: ./scripts/start.sh"
echo "3. Open: http://localhost:8000"
