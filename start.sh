#!/bin/bash

echo "🎥 Video Profile Management System - Khởi động"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Build and start containers
echo "📦 Building and starting containers..."
docker compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker compose exec -T web python manage.py makemigrations
docker compose exec -T web python manage.py migrate

echo ""
echo "✅ Setup completed!"
echo ""
echo "📍 Access points:"
echo "   - Website: http://localhost:8000"
echo "   - Admin: http://localhost:8000/admin"
echo "   - Minio Console: http://localhost:9001"
echo ""
echo "📝 Next steps:"
echo "   1. Create superuser: docker compose exec web python manage.py createsuperuser"
echo "   2. Access the website at http://localhost:8000"
echo ""
echo "🛑 To stop: docker compose down"
echo "📋 To view logs: docker compose logs -f web"