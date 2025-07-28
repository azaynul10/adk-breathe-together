# Deployment Manual for Transnational Air Quality Management System

## Prerequisites

Before deploying the Transnational Air Quality Management System, ensure you have the following prerequisites:

### Required Software
- Google Cloud SDK (gcloud) version 400.0.0 or later
- Docker version 20.10.0 or later
- Python 3.11 or later
- Git version 2.30.0 or later

### Google Cloud Platform Setup
- Active GCP project with billing enabled
- Project owner or editor permissions
- Enabled APIs: Cloud Run, Cloud Build, Container Registry

### Authentication
- Google Cloud account with appropriate permissions
- Local authentication configured

## Quick Start Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/azaynul10/adk-breathe-together
cd transnational-aqms
```

### 2. Configure Environment

```bash
# Set your project ID
export PROJECT_ID="my-aqms-project"

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 3. Run Deployment Script

```bash
cd deployment
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:
- Build and push container images to Google Container Registry
- Deploy services to Cloud Run in different regions
- Configure environment variables for each service
- Set up basic monitoring and alerting

### 4. Verify Deployment

After deployment completes, test the services:

```bash
# Test Bangladesh service
curl https://aqms-bangladesh-[PROJECT_ID]-[REGION].run.app/health

# Test India service
curl https://aqms-india-[PROJECT_ID]-[REGION].run.app/health

# Test orchestrator
curl https://aqms-orchestrator-[PROJECT_ID]-[REGION].run.app/health
```

## Detailed Deployment Steps

### Step 1: Environment Preparation

Create and configure the Google Cloud project:

```bash
# Create project (if needed)
gcloud projects create $PROJECT_ID --name="Transnational AQMS"

# Set project
gcloud config set project $PROJECT_ID

# Enable billing (replace BILLING_ACCOUNT_ID)
gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

Enable required APIs:

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com
```

### Step 2: Container Image Build

Build the container image using Cloud Build:

```bash
# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/transnational-aqms .
```

### Step 3: Cloud Run Deployment

Deploy the Bangladesh service:

```bash
gcloud run deploy aqms-bangladesh \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars COUNTRY_CODE=BD,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300
```

Deploy the India service:

```bash
gcloud run deploy aqms-india \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-south1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars COUNTRY_CODE=IN,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300
```

Deploy the Regional Orchestrator:

```bash
gcloud run deploy aqms-orchestrator \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300
```

### Step 4: Google Maps API Configuration

Set up Google Maps API for the interactive demo:

```bash
# Set Google Maps API key as environment variable
gcloud run services update aqms-bangladesh \
    --region asia-southeast1 \
    --set-env-vars GOOGLE_MAPS_API_KEY=YOUR_API_KEY
```

### Step 5: Monitoring Setup (Optional)

Create monitoring alert policies:

```bash
# Create alert policy for high PM2.5 levels
gcloud alpha monitoring policies create \
    --policy-from-file=deployment/monitoring/alert_policy.json
```

## Configuration Management

### Environment Variables

Each service uses environment variables for configuration:

**Bangladesh Service:**
- `COUNTRY_CODE=BD`
- `ENVIRONMENT=production`
- `GOOGLE_MAPS_API_KEY=your_api_key`

**India Service:**
- `COUNTRY_CODE=IN`
- `ENVIRONMENT=production`

**Regional Orchestrator:**
- `ENVIRONMENT=production`

### Container Configuration

The system uses a multi-stage Docker build:

```dockerfile
# Builder stage
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
EXPOSE 8080
ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Dependencies

The system requires the following Python packages:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.27.2
requests>=2.25.0
python-dotenv
```

## Scaling Configuration

### Automatic Scaling

Cloud Run services are configured with automatic scaling:

- **Min instances:** 1-2 (depending on service)
- **Max instances:** 5-10 (depending on service)
- **CPU:** 1-2 cores per service
- **Memory:** 1-2 Gi per service
- **Timeout:** 300-600 seconds

### Manual Scaling

Adjust scaling parameters as needed:

```bash
gcloud run services update aqms-bangladesh \
    --region asia-southeast1 \
    --min-instances 2 \
    --max-instances 10
```

## Service URLs and Endpoints

### Service URLs

After deployment, services will be available at:

- **Bangladesh Service:** `https://aqms-bangladesh-[PROJECT_ID]-[REGION].run.app`
- **India Service:** `https://aqms-india-[PROJECT_ID]-[REGION].run.app`
- **Orchestrator Service:** `https://aqms-orchestrator-[PROJECT_ID]-[REGION].run.app`

### API Endpoints

Each service provides the following endpoints:

```bash
# Health check
GET /health

# Air quality data
GET /api/air-quality/dhaka
GET /api/air-quality/kolkata
GET /api/air-quality/comparison

# Agent operations
POST /collect
POST /orchestrate

# Interactive demo
GET /demo
```

## Troubleshooting

### Common Issues

**Service not responding:**
1. Check service logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Verify service status: `gcloud run services describe SERVICE_NAME`
3. Check resource limits and scaling settings

**Google Maps not loading:**
1. Verify Google Maps API key is set correctly
2. Check API key restrictions and billing
3. Ensure the key has Maps JavaScript API enabled

**CORS errors:**
1. Check CORS configuration in main.py
2. Verify allowed origins are correct
3. Test with different browsers/devices

### Log Analysis

View service logs:

```bash
# Bangladesh service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aqms-bangladesh" --limit 100

# India service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aqms-india" --limit 100

# Orchestrator logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aqms-orchestrator" --limit 100
```

### Performance Monitoring

Monitor service performance:

```bash
# CPU utilization
gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/container/cpu/utilizations"

# Memory utilization
gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/container/memory/utilizations"

# Request latency
gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/request_latencies"
```

## Maintenance

### Regular Updates

Update container images:

```bash
# Build new image
gcloud builds submit --tag gcr.io/$PROJECT_ID/transnational-aqms:v1.1.0 .

# Update services
gcloud run services update aqms-bangladesh \
    --image gcr.io/$PROJECT_ID/transnational-aqms:v1.1.0 \
    --region asia-southeast1
```

### Health Checks

Automated health checks are configured for all services. Manual health checks:

```bash
# Check service health
curl -f https://aqms-bangladesh-[PROJECT_ID]-[REGION].run.app/health || echo "Service unhealthy"
curl -f https://aqms-india-[PROJECT_ID]-[REGION].run.app/health || echo "Service unhealthy"
curl -f https://aqms-orchestrator-[PROJECT_ID]-[REGION].run.app/health || echo "Service unhealthy"
```

### Security Updates

Regular security maintenance:

1. Update base container images monthly
2. Review and update environment variables as needed
3. Rotate API keys and tokens as needed
4. Monitor for security vulnerabilities

## Cost Optimization

### Resource Optimization

Monitor and optimize resource usage:

```bash
# View billing reports
gcloud billing budgets list

# Analyze resource usage
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

### Scaling Optimization

Adjust scaling parameters based on usage patterns:

- Reduce min instances during low-traffic periods
- Increase max instances during high-pollution episodes
- Optimize CPU and memory allocations based on monitoring data

## Development and Testing

### Local Development

Run the application locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --host 0.0.0.0 --port 8080

# Set environment variables
export GOOGLE_MAPS_API_KEY=your_api_key
export ENVIRONMENT=development
```

### Testing Endpoints

Test the API endpoints locally:

```bash
# Health check
curl http://localhost:8080/health

# Air quality data
curl http://localhost:8080/api/air-quality/dhaka
curl http://localhost:8080/api/air-quality/kolkata

# Interactive demo
open http://localhost:8080/demo
```

### Cloud Build Testing

Test the Cloud Build configuration:

```bash
# Submit build for testing
gcloud builds submit --tag gcr.io/$PROJECT_ID/transnational-aqms:test .

# Deploy test service
gcloud run deploy aqms-test \
    --image gcr.io/$PROJECT_ID/transnational-aqms:test \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
```

## Support and Maintenance

### Contact Information

- **Technical Support:** azaynul3@gmail.com
- **GitHub Repository:** https://github.com/azaynul10/adk-breathe-together

### Maintenance Schedule

- **Regular maintenance:** Monthly security updates
- **Emergency maintenance:** As needed with 24-hour notice
- **Security updates:** Applied immediately upon availability from Google Cloud

### Documentation

- **Architecture Documentation:** `architecture.md`
- **API Documentation:** Available at `/docs` endpoint when running locally
- **Interactive Demo:** Available at `/demo` endpoint

## Deployment Checklist

Before deploying to production, ensure:

- [ ] Google Cloud project is set up with billing enabled
- [ ] Required APIs are enabled (Cloud Run, Cloud Build, Container Registry)
- [ ] Google Maps API key is configured and has proper restrictions
- [ ] Environment variables are set correctly
- [ ] Container image builds successfully
- [ ] Services deploy without errors
- [ ] Health checks pass for all services
- [ ] Interactive demo loads correctly with Google Maps
- [ ] CORS is configured properly for cross-origin requests
- [ ] Monitoring and alerting are set up (optional)

## Rollback Procedures

If deployment fails or issues arise:

```bash
# List service revisions
gcloud run revisions list --service=aqms-bangladesh --region=asia-southeast1

# Rollback to previous revision
gcloud run services update-traffic aqms-bangladesh \
    --region=asia-southeast1 \
    --to-revisions=REVISION_NAME=100

# Or rollback to specific image
gcloud run services update aqms-bangladesh \
    --region=asia-southeast1 \
    --image=gcr.io/$PROJECT_ID/transnational-aqms:PREVIOUS_TAG
```

This deployment manual provides accurate, step-by-step instructions for deploying the Transnational Air Quality Management System based on the actual implementation.
