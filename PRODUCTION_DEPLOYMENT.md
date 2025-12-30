# Production Deployment Guide

This guide covers deploying the Financial Reconciliation system to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Environment Configuration](#environment-configuration)
4. [Security Considerations](#security-considerations)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Scaling](#scaling)
8. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (for LLM features)
- Minimum 4GB RAM
- Minimum 20GB disk space

## Docker Deployment

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Financial-Reconcilation
   ```

2. **Set environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and start services**
   ```bash
   docker-compose up -d --build
   ```

4. **Verify deployment**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:3000
   ```

### Production Docker Compose

For production, use the provided `docker-compose.yml` with the following considerations:

- **Resource Limits**: Add resource limits to prevent resource exhaustion
- **Restart Policies**: Already configured with `unless-stopped`
- **Health Checks**: Already configured for all services
- **Volumes**: Persistent volumes for data storage

### Customizing Docker Configuration

Edit `docker-compose.yml` to:
- Add resource limits
- Configure networking
- Set up SSL/TLS termination
- Add additional services (monitoring, logging)

## Environment Configuration

### Required Environment Variables

```bash
# OpenAI API (required for LLM features)
OPENAI_API_KEY=sk-...

# API Configuration
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE_MB=50
RATE_LIMIT_PER_MINUTE=60

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Optional Environment Variables

```bash
# Redis (for distributed caching)
REDIS_URL=redis://redis:6379/0

# Production Settings
NODE_ENV=production
PYTHON_ENV=production
```

## Security Considerations

### 1. API Security

- **CORS**: Configure `CORS_ORIGINS` to only allow your frontend domain
- **Rate Limiting**: Already implemented (configurable via `RATE_LIMIT_PER_MINUTE`)
- **File Upload Limits**: Configured via `MAX_UPLOAD_SIZE_MB`
- **Input Validation**: All endpoints validate input

### 2. Network Security

- Use reverse proxy (nginx/traefik) for SSL/TLS termination
- Configure firewall rules
- Use VPN or private networks for internal communication

### 3. Secrets Management

- Never commit `.env` files
- Use secrets management (Docker secrets, Kubernetes secrets, etc.)
- Rotate API keys regularly

### 4. File Security

- Uploaded files are stored in `uploads/` directory
- Implement file cleanup policies
- Scan uploaded files for malware (consider adding ClamAV)

## Performance Optimization

### 1. Caching

The system includes in-memory caching. For production:

- **Use Redis**: Set `REDIS_URL` environment variable
- **Cache TTL**: Configure via `CACHE_TTL` (default: 3600 seconds)
- **Cache Keys**: Embeddings and LLM responses are cached

### 2. Database (Future Enhancement)

Currently uses in-memory storage. For production:

- Implement PostgreSQL or MongoDB for reconciliation results
- Use connection pooling
- Add database indexes

### 3. Worker Processes

Backend uses 4 workers by default. Adjust based on:

- CPU cores available
- Expected load
- Memory constraints

Edit `Dockerfile`:
```dockerfile
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 4. Frontend Optimization

- Next.js standalone build (already configured)
- Static asset CDN (consider CloudFlare/AWS CloudFront)
- Enable compression (already configured)

## Monitoring and Logging

### Health Checks

All services include health check endpoints:

- **Backend**: `GET /health`
- **Frontend**: `GET /api/health` (if implemented)

### Logging

- **Log Level**: Configure via `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)
- **Log Format**: Structured JSON logging (for production)
- **Log Aggregation**: Use ELK stack, Loki, or CloudWatch

### Metrics

Consider adding:
- Prometheus metrics endpoint
- Request/response time tracking
- Error rate monitoring
- Resource usage monitoring

## Scaling

### Horizontal Scaling

1. **Backend**: Run multiple instances behind load balancer
   ```bash
   docker-compose up -d --scale backend=3
   ```

2. **Frontend**: Stateless, can scale horizontally
   ```bash
   docker-compose up -d --scale frontend=2
   ```

3. **Redis**: Use Redis Cluster for distributed caching

### Vertical Scaling

- Increase Docker resource limits
- Add more CPU/memory to host
- Use more powerful instance types

## Backup and Recovery

### Data to Backup

1. **Uploads Directory**: `uploads/`
2. **Reports Directory**: `reports/`
3. **Redis Data**: If using Redis persistence
4. **Configuration**: `.env` files

### Backup Strategy

```bash
# Backup script example
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf backup_$DATE.tar.gz uploads/ reports/ .env
# Upload to S3, Azure Blob, etc.
```

### Recovery

1. Restore files from backup
2. Restart services: `docker-compose restart`
3. Verify: `curl http://localhost:8000/health`

## Reverse Proxy Setup (Nginx)

Example Nginx configuration:

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## SSL/TLS Configuration

Use Let's Encrypt with Certbot:

```bash
certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

Or use Docker with Traefik for automatic SSL.

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Change port in docker-compose.yml
   ```

2. **Out of Memory**
   ```bash
   # Check memory usage
   docker stats
   # Increase Docker memory limit
   ```

3. **LLM Service Errors**
   - Verify `OPENAI_API_KEY` is set
   - Check API quota/limits
   - Review logs: `docker-compose logs backend`

4. **File Upload Failures**
   - Check `MAX_UPLOAD_SIZE_MB` setting
   - Verify disk space: `df -h`
   - Check file permissions

### Logs

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Production Checklist

- [ ] Environment variables configured
- [ ] CORS origins restricted
- [ ] SSL/TLS enabled
- [ ] Rate limiting configured
- [ ] File upload limits set
- [ ] Health checks verified
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] Resource limits set
- [ ] Logging configured
- [ ] Error handling tested

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review health endpoint: `curl http://localhost:8000/health`
3. Check documentation: `README.md`
4. Open an issue on GitHub

