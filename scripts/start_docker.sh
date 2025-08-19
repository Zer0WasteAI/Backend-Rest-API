#!/bin/bash
# Quick Docker Services Startup for ZeroWasteAI API

echo "🐳 Starting ZeroWasteAI Docker Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

echo "🚀 Starting services..."
docker-compose up -d --build

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ Services are starting up!"
echo "🌐 API: http://localhost:3000"
echo "📚 API Docs: http://localhost:3000/apidocs"
echo "🔴 Redis: localhost:6379"
echo "📊 MySQL: localhost:3306"
echo ""
echo "💡 To run tests: python3 quick_test.py [unit|integration|functional|all]"
echo "💡 To stop: docker-compose down"
