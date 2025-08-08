#!/bin/bash

# Multi-tenant Code Conversion Service Setup Script

set -e

echo "🚀 Setting up Multi-tenant Code Conversion Service..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    
    # Generate encryption key
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s/your_32_byte_encryption_key_here/$ENCRYPTION_KEY/g" .env
    
    echo "⚠️  Please edit .env file and add your:"
    echo "   - OPENAI_API_KEY"
    echo "   - POSTGRES_PASSWORD"
    echo "   - Update ALLOWED_ORIGINS if needed"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec app python -c "
from src.models.database import create_tables
create_tables()
print('✅ Database tables created successfully!')
"

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
else
    echo "❌ Service health check failed. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📊 Service URLs:"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Database: localhost:5432"
echo ""
echo "📖 Next steps:"
echo "   1. Open http://localhost:8000/docs to explore the API"
echo "   2. Use the frontend example: open frontend-example.html"
echo "   3. Register users via POST /auth/register"
echo "   4. Start conversions via POST /convert"
echo ""
echo "🔧 Management commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo "   Update: git pull && docker-compose up -d --build"
