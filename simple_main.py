from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(
    title="Transnational AQMS",
    description="Air Quality Management System",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "service": "Transnational Air Quality Management System",
        "version": "1.0.0",
        "country_code": os.getenv("COUNTRY_CODE", "Unknown"),
        "service_type": os.getenv("SERVICE_TYPE", "agent"),
        "timestamp": datetime.now().isoformat(),
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service_type": os.getenv("SERVICE_TYPE", "agent"),
        "country_code": os.getenv("COUNTRY_CODE"),
        "version": "1.0.0"
    }

@app.post("/collect")
def collect():
    country = os.getenv("COUNTRY_CODE", "Unknown")
    return {
        "status": "success",
        "message": f"Data collection simulated for {country}",
        "timestamp": datetime.now().isoformat(),
        "country_code": country,
        "simulated_data": {
            "pm25": 139.0 if country == "BD" else 45.6,
            "pm10": 180.0 if country == "BD" else 65.2,
            "temperature": 28.5,
            "humidity": 75.0,
            "wind_speed": 3.5,
            "wind_direction": 270
        }
    }

@app.post("/orchestrate")
def orchestrate():
    return {
        "status": "success",
        "message": "Regional orchestration simulated",
        "timestamp": datetime.now().isoformat(),
        "coordinated_actions": [
            "Cross-border data sharing initiated",
            "Policy recommendations generated",
            "Alert system activated"
        ],
        "alerts": {
            "alerts": [],
            "distribution_success": True
        }
    }

@app.get("/status")
def status():
    country_code = os.getenv("COUNTRY_CODE")
    service_type = os.getenv("SERVICE_TYPE", "agent")
    
    return {
        "service_type": service_type,
        "country_code": country_code,
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "agent_status": {
            "total_collections": 1247,
            "successful_collections": 1198,
            "success_rate": 0.96,
            "last_collection_time": datetime.now().isoformat()
        } if service_type == "agent" else {
            "total_orchestrations": 324,
            "successful_orchestrations": 318,
            "success_rate": 0.98,
            "last_orchestration_time": datetime.now().isoformat()
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)