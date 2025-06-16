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
- Enabled APIs: Cloud Run, Cloud Build, BigQuery, Monitoring, Logging

### Authentication
- Service account with appropriate permissions
- Authentication key file downloaded locally

## Quick Start Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/azaynul10/transnational-aqms.git
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
- Enable required Google Cloud APIs
- Build and push container images
- Deploy services to Cloud Run
- Create BigQuery datasets
- Set up monitoring and alerting

### 4. Verify Deployment

After deployment completes, test the services:

```bash
# Test Bangladesh service
curl https://aqms-bangladesh-r5hed7gtca-uc.a.run.app/health

# Test India service
curl https://aqms-india-r5hed7gtca-uc.a.run.app/health

# Test orchestrator
curl https://aqms-orchestrator-r5hed7gtca-uc.a.run.app/health
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
    containerregistry.googleapis.com \
    bigquery.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com
```

### Step 2: Service Account Configuration

Create service accounts for each component:

```bash
# Bangladesh agent service account
gcloud iam service-accounts create aqms-bangladesh \
    --display-name="AQMS Bangladesh Agent"

# India agent service account
gcloud iam service-accounts create aqms-india \
    --display-name="AQMS India Agent"

# Regional orchestrator service account
gcloud iam service-accounts create aqms-orchestrator \
    --display-name="AQMS Regional Orchestrator"
```

Assign IAM roles:

```bash
# Bangladesh agent permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-bangladesh@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-bangladesh@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

# India agent permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-india@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-india@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.metricWriter"

# Orchestrator permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-orchestrator@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:aqms-orchestrator@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/monitoring.admin"
```

### Step 3: Container Image Build

Build the container image using Cloud Build:

```bash
cd deployment
gcloud builds submit --tag gcr.io/$PROJECT_ID/transnational-aqms .
```

### Step 4: BigQuery Setup

Create datasets for each country:

```bash
# Bangladesh dataset
bq mk --dataset \
    --location=asia-southeast1 \
    --description="Air quality data for Bangladesh" \
    $PROJECT_ID:bangladesh_air_2025

# India dataset
bq mk --dataset \
    --location=asia-south1 \
    --description="Air quality data for India" \
    $PROJECT_ID:india_air_2025

# Coordination dataset
bq mk --dataset \
    --location=asia-southeast1 \
    --description="Cross-border coordination data" \
    $PROJECT_ID:transnational_coordination
```

Create tables with appropriate schemas:

```bash
# Air quality measurements table
bq mk --table \
    $PROJECT_ID:bangladesh_air_2025.measurements \
    schemas/air_quality_table.json

bq mk --table \
    $PROJECT_ID:india_air_2025.measurements \
    schemas/air_quality_table.json

# Policy actions table
bq mk --table \
    $PROJECT_ID:transnational_coordination.policy_actions \
    schemas/policy_actions_table.json
```

### Step 5: Cloud Run Deployment

Deploy the Bangladesh service:

```bash
gcloud run deploy aqms-bangladesh \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account aqms-bangladesh@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars COUNTRY_CODE=BD,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 100 \
    --min-instances 5 \
    --timeout 300
```

Deploy the India service:

```bash
gcloud run deploy aqms-india \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-south1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account aqms-india@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars COUNTRY_CODE=IN,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 100 \
    --min-instances 5 \
    --timeout 300
```

Deploy the Regional Orchestrator:

```bash
gcloud run deploy aqms-orchestrator \
    --image gcr.io/$PROJECT_ID/transnational-aqms \
    --region asia-southeast1 \
    --platform managed \
    --allow-unauthenticated \
    --service-account aqms-orchestrator@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars SERVICE_TYPE=orchestrator,ENVIRONMENT=production \
    --memory 4Gi \
    --cpu 4 \
    --max-instances 50 \
    --min-instances 2 \
    --timeout 600
```

### Step 6: Monitoring Setup

Create monitoring alert policies:

```bash
gcloud alpha monitoring policies create \
    --policy-from-file=monitoring/alert_policy.json
```

Set up custom dashboards:

```bash
gcloud monitoring dashboards create \
    --config-from-file=monitoring/dashboard.json
```

## Configuration Management

### Environment Variables

Each service uses environment variables for configuration:

**Bangladesh Service:**
- `COUNTRY_CODE=BD`
- `ENVIRONMENT=production`
- `BIGQUERY_DATASET=bangladesh_air_2025`

**India Service:**
- `COUNTRY_CODE=IN`
- `ENVIRONMENT=production`
- `BIGQUERY_DATASET=india_air_2025`

**Regional Orchestrator:**
- `SERVICE_TYPE=orchestrator`
- `ENVIRONMENT=production`
- `COORDINATION_DATASET=transnational_coordination`

### Secret Management

Store sensitive configuration in Secret Manager:

```bash
# API keys
gcloud secrets create api-keys --data-file=secrets/api-keys.json

# Authentication tokens
gcloud secrets create auth-tokens --data-file=secrets/auth-tokens.json

# Database credentials
gcloud secrets create db-credentials --data-file=secrets/db-credentials.json
```

Grant access to secrets:

```bash
gcloud secrets add-iam-policy-binding api-keys \
    --member="serviceAccount:aqms-bangladesh@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Scaling Configuration

### Automatic Scaling

Cloud Run services are configured with automatic scaling:

- **Min instances:** 2-5 (depending on service)
- **Max instances:** 50-100 (depending on service)
- **CPU utilization target:** 70%
- **Memory utilization target:** 80%

### Manual Scaling

Adjust scaling parameters as needed:

```bash
gcloud run services update aqms-bangladesh \
    --region asia-southeast1 \
    --min-instances 10 \
    --max-instances 200
```

## Backup and Recovery

### Database Backup

BigQuery datasets are automatically backed up. Configure additional backup policies:

```bash
# Create backup policy
bq mk --transfer_config \
    --project_id=$PROJECT_ID \
    --data_source=scheduled_query \
    --display_name="Daily Backup" \
    --target_dataset=backup_dataset \
    --schedule="every day 02:00"
```

### Configuration Backup

Backup deployment configurations:

```bash
# Export Cloud Run configurations
gcloud run services describe aqms-bangladesh \
    --region asia-southeast1 \
    --format export > backup/bangladesh-service.yaml

gcloud run services describe aqms-india \
    --region asia-south1 \
    --format export > backup/india-service.yaml

gcloud run services describe aqms-orchestrator \
    --region asia-southeast1 \
    --format export > backup/orchestrator-service.yaml
```

## Troubleshooting

### Common Issues

**Service not responding:**
1. Check service logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Verify service status: `gcloud run services describe SERVICE_NAME`
3. Check resource limits and scaling settings

**Authentication errors:**
1. Verify service account permissions
2. Check secret manager access
3. Validate API key configuration

**Data synchronization issues:**
1. Check cross-border communication logs
2. Verify network connectivity
3. Validate data schema compatibility

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
curl -f https://aqms-bangladesh-[hash]-uc.a.run.app/health || echo "Service unhealthy"
curl -f https://aqms-india-[hash]-uc.a.run.app/health || echo "Service unhealthy"
curl -f https://aqms-orchestrator-[hash]-uc.a.run.app/health || echo "Service unhealthy"
```

### Security Updates

Regular security maintenance:

1. Update base container images monthly
2. Rotate service account keys quarterly
3. Review and update IAM permissions annually
4. Update API keys and tokens as needed

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

## Support and Maintenance

### Contact Information

- **Technical Support:** azaynul3@gmail.com

### Maintenance Schedule

- **Regular maintenance:** not yet updated
- **Emergency maintenance:** As needed with 24-hour notice
- **Security updates:** Applied immediately upon availability from Google Cloud

