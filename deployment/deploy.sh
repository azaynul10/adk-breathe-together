
PROJECT_ID=${PROJECT_ID:-"my-aqms-project"}
IMAGE_NAME="transnational-aqms"
REGION_BD="asia-southeast1"  
REGION_IN="asia-south1"     
REGION_OR="asia-southeast1" 

if [ -d .git ] && git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    
    TAG=$(git rev-parse HEAD)
else
    
    TAG=$(date +%Y%m%d-%H%M%S)
fi


IMAGE="gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"

echo "🏗️ Building container image with tag: $IMAGE"
gcloud builds submit --tag "$IMAGE" .

echo "🚀 Deploying Bangladesh service"
gcloud run deploy aqms-bangladesh \
    --image "$IMAGE" \
    --region "$REGION_BD" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars COUNTRY_CODE=BD,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300

echo "🚀 Deploying India service"
gcloud run deploy aqms-india \
    --image "$IMAGE" \
    --region "$REGION_IN" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars COUNTRY_CODE=IN,ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300

echo "🚀 Deploying Orchestrator service"
gcloud run deploy aqms-orchestrator \
    --image "$IMAGE" \
    --region "$REGION_OR" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 5 \
    --min-instances 1 \
    --timeout 300

echo "✅ Deployment completed"