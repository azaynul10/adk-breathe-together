Write-Host "🚀 Performance Testing Transnational AQMS" -ForegroundColor Cyan

$services = @(
    "https://aqms-bangladesh-r5hed7gtca-uc.a.run.app",
    "https://aqms-india-r5hed7gtca-uc.a.run.app",
    "https://aqms-orchestrator-r5hed7gtca-uc.a.run.app"
)

foreach ($service in $services) {
    Write-Host "Testing $service..." -ForegroundColor Yellow
    
    # Measure response time
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = Invoke-RestMethod -Uri "$service/health" -Method GET
        $stopwatch.Stop()
        
        Write-Host "  ✅ Status: $($response.status)" -ForegroundColor Green
        Write-Host "  ⏱️  Response Time: $($stopwatch.ElapsedMilliseconds)ms" -ForegroundColor Cyan
        Write-Host "  🏷️  Service: $($response.country_code)" -ForegroundColor Magenta
    }
    catch {
        $stopwatch.Stop()
        Write-Host "  ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}
