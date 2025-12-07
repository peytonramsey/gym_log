# Docker Setup Guide for FitGlyph

This guide explains how to run FitGlyph using Docker and Docker Compose.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker and Docker Compose)
- Git (to clone the repository)

## Quick Start (Recommended)

### 1. Clone the repository (if you haven't already)
```bash
git clone <your-repo-url>
cd gymlog
```

### 2. Create environment file (optional)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env if you want to customize settings
# Default values work fine for local development
```

### 3. Start the application
```bash
docker-compose up -d
```

This command will:
- Download the necessary Docker images
- Build your Flask application
- Start PostgreSQL database
- Start the Flask web server
- Create the database tables automatically
- Create an admin user

### 4. Access the application
Open your browser and go to:
- **Main app**: http://localhost:5000
- **Demo mode**: http://localhost:5000/demo

### 5. Login credentials
- **Username**: `admin` (or whatever you set in ADMIN_USERNAME)
- **Password**: `admin123` (or whatever you set in ADMIN_PASSWORD)

## Common Commands

### Start the application
```bash
docker-compose up -d
```
The `-d` flag runs containers in the background (detached mode).

### Stop the application
```bash
docker-compose down
```

### Stop and remove all data (fresh start)
```bash
docker-compose down -v
```
**Warning**: This deletes all database data!

### View logs
```bash
# All services
docker-compose logs -f

# Just the web app
docker-compose logs -f web

# Just the database
docker-compose logs -f db
```

### Restart after code changes
```bash
docker-compose restart web
```

### Rebuild after dependency changes
```bash
docker-compose up -d --build
```

## Development vs Production

### Development Mode (Current Setup)
The current `docker-compose.yml` is configured for development:
- Code is mounted as a volume (changes reflect immediately)
- PostgreSQL database for realistic testing
- Hot-reloading enabled

### Production Deployment
For production deployment to platforms like Render, Railway, or AWS:

1. The platform will use the `Dockerfile` directly
2. Set environment variables on the platform:
   - `DATABASE_URL` (provided by platform)
   - `SECRET_KEY` (generate a secure random key)
   - `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
   - `USDA_API_KEY` (optional)

## Troubleshooting

### Port 5000 already in use
If you get an error about port 5000 being in use:

**Option 1**: Stop the process using port 5000
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:5000 | xargs kill -9
```

**Option 2**: Change the port in `docker-compose.yml`
```yaml
services:
  web:
    ports:
      - "8080:5000"  # Access at localhost:8080 instead
```

### Database connection errors
```bash
# Check if database is healthy
docker-compose ps

# View database logs
docker-compose logs db

# Restart the database
docker-compose restart db
```

### Reset everything and start fresh
```bash
# Stop and remove all containers, volumes, and networks
docker-compose down -v

# Remove the built image
docker-compose rm -f

# Start fresh
docker-compose up -d --build
```

### Check if containers are running
```bash
docker-compose ps
```

### Access the database directly
```bash
docker-compose exec db psql -U fitglyph_user -d fitglyph_db
```

## File Structure

```
gymlog/
├── Dockerfile              # Instructions to build the app container
├── docker-compose.yml      # Orchestrates app + database
├── .dockerignore          # Files to exclude from Docker build
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── app.py                # Flask application
```

## Benefits of Using Docker

1. **Consistent Environment**: Same setup on any machine
2. **Easy Onboarding**: New developers just run `docker-compose up`
3. **Database Included**: PostgreSQL runs automatically
4. **Production-Ready**: Same setup as production deployment
5. **Clean Isolation**: Doesn't affect your system Python or other projects

## Next Steps

- Visit http://localhost:5000/demo to see the app with sample data
- Try creating your own account via http://localhost:5000/register
- Check out the main README.md for feature documentation
- Ready to deploy? Check out deployment guides for Render, Railway, or AWS

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
