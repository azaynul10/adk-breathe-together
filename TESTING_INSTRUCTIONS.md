# Testing Instructions for Transnational AQMS

## Overview
This document provides comprehensive testing instructions for the Transnational Air Quality Management System (TAQMS) built using Google's Agent Development Kit (ADK). The system implements Sequential, Parallel, and Loop agents for cross-border environmental coordination between Bangladesh and India.

##  Quick Start Testing

### Prerequisites
- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker Desktop (optional, for local testing)
- Python 3.11+ (for local development)

### 1. Live System Testing (Recommended)

The system is already deployed and running. Test the live services:

```bash
# Test Bangladesh Sequential Agent
curl -X GET "https://aqms-bangladesh-r5hed7gtca-uc.a.run.app/health"
curl -X POST "https://aqms-bangladesh-r5hed7gtca-uc.a.run.app/collect" \
  -H "Content-Type: application/json" \
  -d '{}'

# Test India Parallel Agent  
curl -X GET "https://aqms-india-r5hed7gtca-uc.a.run.app/health"
curl -X POST "https://aqms-india-r5hed7gtca-uc.a.run.app/collect" \
  -H "Content-Type: application/json" \
  -d '{}'

# Test Regional Loop Agent
curl -X GET "https://aqms-orchestrator-r5hed7gtca-uc.a.run.app/health"
curl -X POST "https://aqms-orchestrator-r5hed7gtca-uc.a.run.app/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 2. Interactive Demo Testing

Visit the interactive demo: `https://aqms-interactive-demo-r5hed7gtca-uc.a.run.app`

**Test Scenarios:**
1. **Agent Testing**: Click each agent button to test individual ADK agents
2. **Emergency Simulation**: Trigger emergency scenario to test cross-border coordination
3. **Metrics Display**: View real-time impact metrics and system performance
4. **Cross-Border Sync**: Test A2A protocol communication between countries

## 🔧 Local Development Testing

### Setup Local Environment

```bash
# Clone the repository
git clone https://github.com/your-username/transnational-aqms.git
cd transnational-aqms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROJECT_ID="your-project-id"
export COUNTRY_CODE="BD"  # or "IN"
export SERVICE_TYPE="agent"  # or "orchestrator"
```

### Run Local Tests

```bash
# Run unit tests
python -m pytest tests/ -v

# Run integration tests
python -m pytest tests/test_integration.py -v

# Run performance tests
python tests/test_performance.py

# Test individual agents
python -m pytest tests/test_agents.py::TestDhakaAgent -v
python -m pytest tests/test_agents.py::TestKolkataAgent -v
python -m pytest tests/test_agents.py::TestOrchestrator -v
```

### Local Server Testing

```bash
# Start local server
uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Test endpoints
curl http://localhost:8080/health
curl -X POST http://localhost:8080/collect
curl -X POST http://localhost:8080/orchestrate
curl http://localhost:8080/demo/metrics
```

## 🌐 Cloud Deployment Testing

### Deploy to Your Own Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable monitoring.googleapis.com

# Deploy Bangladesh service
gcloud run deploy aqms-bangladesh \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars COUNTRY_CODE=BD

# Deploy India service
gcloud run deploy aqms-india \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars COUNTRY_CODE=IN

# Deploy Orchestrator
gcloud run deploy aqms-orchestrator \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SERVICE_TYPE=orchestrator
```

### Verify Deployment

```bash
# Get service URLs
gcloud run services list --region us-central1

# Test health endpoints
for service in aqms-bangladesh aqms-india aqms-orchestrator; do
  URL=$(gcloud run services describe $service --region us-central1 --format="value(status.url)")
  echo "Testing $service at $URL"
  curl "$URL/health"
done
```

## 🧪 Comprehensive Test Suite

### ADK Agent Testing

```python
# Test Sequential Agent (Bangladesh)
def test_sequential_agent():
    """Test Dhaka PM2.5 Sequential Agent"""
    agent = DhakaAgent()
    result = await agent.run()
    
    assert result['status'] == 'success'
    assert result['agent_type'] == 'Sequential'
    assert 'simulated_data' in result
    assert result['simulated_data']['pm25'] > 0
    assert result['collection_time_ms'] < 1000

# Test Parallel Agent (India)  
def test_parallel_agent():
    """Test Kolkata Meteorological Parallel Agent"""
    agent = KolkataAgent()
    result = await agent.run()
    
    assert result['status'] == 'success'
    assert result['agent_type'] == 'Parallel'
    assert 'weather_analysis' in result
    assert result['processing_time_ms'] < 1000

# Test Loop Agent (Regional)
def test_loop_agent():
    """Test Regional Orchestrator Loop Agent"""
    orchestrator = RegionalOrchestrator()
    context = {
        'dhaka_data': {'pm25': 139.0, 'country_code': 'BD'},
        'kolkata_data': {'pm25': 45.6, 'country_code': 'IN'}
    }
    result = await orchestrator.run(context)
    
    assert result['status'] == 'success'
    assert result['agent_type'] == 'Loop'
    assert 'coordinated_actions' in result
    assert len(result['alerts']['alerts']) >= 0
```

### A2A Protocol Testing

```python
def test_a2a_protocol():
    """Test Agent-to-Agent communication protocol"""
    protocol = A2AProtocol()
    
    # Test message creation
    message = protocol.create_message(
        data={'pm25': 139.0},
        source_country='BD',
        target_country='IN',
        message_type='data_sharing'
    )
    
    assert message['source_country'] == 'BD'
    assert message['target_country'] == 'IN'
    assert message['encrypted'] == True
    assert message['timestamp'] is not None

def test_cross_border_sync():
    """Test cross-border synchronization"""
    sync_time = measure_sync_time('BD', 'IN')
    assert sync_time < 60  # Less than 1 minute
```

### Performance Testing

```python
def test_system_performance():
    """Test system performance under load"""
    import asyncio
    import time
    
    async def load_test():
        tasks = []
        for i in range(100):  # 100 concurrent requests
            task = asyncio.create_task(test_health_endpoint())
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All requests should succeed
        assert all(r['status'] == 'healthy' for r in results)
        
        # Average response time should be < 1 second
        avg_response_time = (end_time - start_time) / len(results)
        assert avg_response_time < 1.0
        
        return results
    
    asyncio.run(load_test())
```

## 📊 Monitoring and Observability Testing

### Test Custom Metrics

```bash
# Create custom metrics
python create_metrics.py

# Verify metrics creation
gcloud alpha monitoring metrics list --filter="metric.type:custom.googleapis.com/pm25_level"

# Test metric ingestion
python test_metrics_ingestion.py
```

### Test Alerting

```bash
# Create alert policies
gcloud alpha monitoring policies create \
  --display-name="AQMS High PM2.5" \
  --condition-filter="resource.type=\"cloud_run_revision\"" \
  --combiner="OR"

# Test alert triggering
python trigger_test_alert.py
```

### Test Dashboards

```bash
# Create monitoring dashboard
gcloud monitoring dashboards create --config-from-file=dashboard_config.json

# Verify dashboard creation
gcloud monitoring dashboards list
```

## 🔍 Data Quality Testing

### Test Data Harmonization

```python
def test_data_harmonization():
    """Test cross-border data harmonization"""
    harmonizer = DataHarmonizer()
    
    # Test Bangladesh data format
    bd_data = {
        'pm25': 139.0,
        'timestamp': '2025-06-08T06:07:10.324763',
        'station_id': 'BD_DHAKA_001',
        'country_code': 'BD'
    }
    
    # Test India data format
    in_data = {
        'pm25': 45.6,
        'timestamp': '2025-06-08T06:07:10.324763',
        'station_id': 'IN_KOLKATA_001',
        'country_code': 'IN'
    }
    
    # Harmonize data
    harmonized = harmonizer.harmonize([bd_data, in_data])
    
    assert len(harmonized) == 2
    assert all('unified_timestamp' in d for d in harmonized)
    assert all('quality_score' in d for d in harmonized)
```

### Test Data Validation

```python
def test_data_validation():
    """Test data quality validation"""
    validator = DataValidator()
    
    # Test valid data
    valid_data = {'pm25': 45.6, 'temperature': 28.5}
    assert validator.validate(valid_data) == True
    
    # Test invalid data
    invalid_data = {'pm25': -10.0, 'temperature': 100.0}
    assert validator.validate(invalid_data) == False
```

## 🚨 Emergency Scenario Testing

### Test Emergency Response

```python
def test_emergency_response():
    """Test emergency response coordination"""
    emergency = EmergencyScenario()
    
    # Simulate high pollution event
    scenario = emergency.create_scenario(
        location='Dhaka',
        pm25_level=300.0,  # Hazardous level
        wind_direction=270,  # Towards India
        severity='high'
    )
    
    # Test response coordination
    response = emergency.coordinate_response(scenario)
    
    assert response['alert_level'] == 'red'
    assert response['cross_border_notification'] == True
    assert response['estimated_response_time'] < 3600  # < 1 hour
    assert len(response['policy_actions']) > 0
```

## 📈 Impact Metrics Testing

### Test Impact Calculation

```python
def test_impact_metrics():
    """Test impact metrics calculation"""
    calculator = ImpactCalculator()
    
    # Test population impact
    population_impact = calculator.calculate_population_impact(
        affected_area='indo_gangetic_plain',
        pm25_reduction=50.0
    )
    
    assert population_impact['people_protected'] >= 58_000_000
    assert population_impact['health_improvement'] > 0
    
    # Test response time improvement
    time_improvement = calculator.calculate_response_improvement(
        legacy_time=14*24*3600,  # 14 days in seconds
        new_time=3600  # 1 hour in seconds
    )
    
    assert time_improvement['improvement_percentage'] >= 97
```

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **CORS Errors in Interactive Demo**
   ```bash
   # Ensure CORS is enabled in main.py
   app.add_middleware(CORSMiddleware, allow_origins=["*"])
   ```

2. **Authentication Errors**
   ```bash
   # Re-authenticate with Google Cloud
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Service Deployment Failures**
   ```bash
   # Check build logs
   gcloud logging read "resource.type=cloud_build"
   
   # Verify service configuration
   gcloud run services describe SERVICE_NAME --region us-central1
   ```

4. **Performance Issues**
   ```bash
   # Check service metrics
   gcloud monitoring metrics list
   
   # Scale service if needed
   gcloud run services update SERVICE_NAME --max-instances=10
   ```

## 📞 Support

For testing support or issues:
- **GitHub Issues**: [Repository Issues](https://github.com/azaynul10/transnational-aqms/issues)
- **Documentation**: [Full Documentation](./docs/)
- **Live Demo**: [Interactive Demo](https://aqms-interactive-demo-r5hed7gtca-uc.a.run.app)


