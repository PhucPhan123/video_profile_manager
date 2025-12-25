# 🚀 Deployment Guide

Hướng dẫn chi tiết để deploy Video Profile Management System

## Yêu cầu hệ thống

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB (khuyến nghị 8GB cho video processing)
- **Disk**: 20GB free space
- **OS**: 
  - Windows 10/11 with WSL 2
  - Ubuntu 20.04+ (WSL hoặc native)
  - macOS with Docker Desktop

### Software Requirements
- Docker Desktop 4.0+
- Docker Compose 2.0+
- Git

## Deployment trên WSL (Windows)

### 1. Cài đặt WSL 2

```powershell
# Mở PowerShell với quyền Admin
wsl --install

# Hoặc nếu đã cài WSL 1, upgrade lên WSL 2
wsl --set-default-version 2
wsl --set-version Ubuntu 2
```

### 2. Cài đặt Docker Desktop

1. Download Docker Desktop từ https://www.docker.com/products/docker-desktop
2. Cài đặt và khởi động Docker Desktop
3. Trong Settings → Resources → WSL Integration:
   - Enable integration with default WSL distro
   - Enable cho Ubuntu distribution

### 3. Clone và Setup Project

```bash
# Mở WSL terminal (Ubuntu)
cd ~
mkdir projects
cd projects

# Clone project
git clone https://github.com/PhucPhan123/video_profile_manager.git
cd video_profile_manager

# Kiểm tra file .env (đã có sẵn)
cat .env

# Chỉnh sửa nếu cần
nano .env
```

### 4. Build và Deploy

#### Option 1: Sử dụng script tự động

```bash
chmod +x start.sh
./start.sh
```

#### Option 2: Manual deployment

```bash
# Build và start containers
docker-compose up --build -d

# Kiểm tra status
docker-compose ps

# Chờ database sẵn sàng
sleep 10

# Run migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 5. Verify Deployment

```bash
# Check logs
docker-compose logs -f web

# Test website
curl http://localhost:8000

# Access admin
# http://localhost:8000/admin
```

## Deployment trên Linux (Native)

### 1. Cài đặt Docker

```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Deploy

```bash
# Clone project
git clone https://github.com/PhucPhan123/video_profile_manager.git
cd video_profile_manager

# Run deployment script
chmod +x start.sh
./start.sh
```

## Production Deployment Checklist

### Security

- [ ] Thay đổi `SECRET_KEY` trong `.env`
- [ ] Thay đổi database password
- [ ] Thay đổi Minio credentials
- [ ] Set `DEBUG=False` trong `.env`
- [ ] Cấu hình `ALLOWED_HOSTS` đúng domain
- [ ] Setup HTTPS/SSL certificate
- [ ] Enable firewall và chỉ mở các port cần thiết

### Performance

- [ ] Cấu hình resource limits trong `docker-compose.yml`
- [ ] Setup Redis/Memcached cho caching
- [ ] Configure Nginx reverse proxy
- [ ] Enable Gzip compression
- [ ] Setup CDN cho static files

### Monitoring

- [ ] Setup logging (ELK stack hoặc alternatives)
- [ ] Configure health checks
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Configure backup strategy
- [ ] Setup alerting

### Backup Strategy

```bash
# Backup database
docker-compose exec db pg_dump -U admin videoprofile_db > backup_$(date +%Y%m%d).sql

# Backup Minio data
docker-compose exec minio mc mirror /data /backup

# Backup script (cron job)
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/backups/video_profile_manager
mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T db pg_dump -U admin videoprofile_db | gzip > $BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz

# Minio backup
docker-compose exec minio mc mirror /data $BACKUP_DIR/minio_$(date +%Y%m%d)

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

## Nginx Reverse Proxy (Production)

```nginx
# /etc/nginx/sites-available/video-profile-manager

upstream django {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/project/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /path/to/project/mediafiles/;
        expires 30d;
    }
}
```

## Environment Variables for Production

```env
# .env.production

# Django
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_NAME=videoprofile_db
DB_USER=admin
DB_PASSWORD=strong-password-here
DB_HOST=db
DB_PORT=5432

# Minio
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_BUCKET=video-profiles
MINIO_USE_SSL=False

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Docker Compose for Production

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: videoprofile_db
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - video_network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  minio:
    image: minio/minio:latest
    container_name: videoprofile_minio
    restart: always
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    networks:
      - video_network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

  web:
    build: .
    container_name: videoprofile_web
    restart: always
    command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/mediafiles
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      - db
      - minio
    networks:
      - video_network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

networks:
  video_network:
    driver: bridge

volumes:
  postgres_data:
  minio_data:
  static_volume:
  media_volume:
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml

services:
  web:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
```

### Load Balancing with Nginx

```nginx
upstream django_cluster {
    least_conn;
    server web_1:8000;
    server web_2:8000;
    server web_3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://django_cluster;
    }
}
```

## Troubleshooting

### Container không start

```bash
# Check logs
docker-compose logs -f

# Check resource usage
docker stats

# Restart specific service
docker-compose restart web
```

### Database migration errors

```bash
# Reset migrations (CAUTION: Deletes data)
docker-compose exec web python manage.py migrate --fake app_name zero
docker-compose exec web python manage.py migrate app_name
```

### Minio bucket errors

```bash
# Access Minio container
docker-compose exec minio sh

# Create bucket manually
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/video-profiles
```

## Maintenance

### Update Docker images

```bash
docker-compose pull
docker-compose up -d
```

### Clean up Docker

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

## Support

- GitHub Issues: https://github.com/PhucPhan123/video_profile_manager/issues
- Documentation: https://github.com/PhucPhan123/video_profile_manager/wiki