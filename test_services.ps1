# Get service URLs
$services = @("aqms-bangladesh", "aqms-india", "aqms-orchestrator")
$region = "us-central1"

foreach ($service in $services) {
    Write-Host "Testing $service..." -ForegroundColor Green
    
    try {
        $url = gcloud run services describe $service --region $region --format="value(status.url)" 2>$null
        
        if ($url) {
            Write-Host "  URL: $url"
            
            # Test health endpoint
            $health = Invoke-RestMethod -Uri "$url/health" -Method GET -TimeoutSec 10
            Write-Host "  Health: $($health.status)" -ForegroundColor Green
            
            # Test main endpoint
            $main = Invoke-RestMethod -Uri "$url/" -Method GET -TimeoutSec 10
            Write-Host "  Service: $($main.service)" -ForegroundColor Green
            
        } else {
            Write-Host "  Service not found or not deployed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}
