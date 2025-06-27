from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import httpx
import asyncio
import random
from datetime import datetime
from typing import Dict, Any, Optional
import requests

app = FastAPI(
    title="Transnational AQMS - Production Ready",
    description="Real-time air quality management with live data integration",
    version="2.0.0"
)

# Production CORS configuration
ALLOWED_ORIGINS = [
    "https://aqms-interactive-demo-r5hed7gtca-uc.a.run.app",
    "https://aqms-bangladesh-r5hed7gtca-uc.a.run.app", 
    "https://aqms-india-r5hed7gtca-uc.a.run.app",
    "https://aqms-orchestrator-r5hed7gtca-uc.a.run.app",
    "http://localhost:8080",  # Development
    "http://127.0.0.1:8080"   # Local testing
]

# Add wildcard for development, specific origins for production
if os.getenv("ENVIRONMENT") == "development":
    ALLOWED_ORIGINS.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add explicit CORS headers for all responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    
    if origin in ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Add security headers for production
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Handle preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Service URLs
SERVICES = {
    "bangladesh": "https://aqms-bangladesh-r5hed7gtca-uc.a.run.app",
    "india": "https://aqms-india-r5hed7gtca-uc.a.run.app",
    "orchestrator": "https://aqms-orchestrator-r5hed7gtca-uc.a.run.app"
}

WAQI_TOKEN = "16c03642e3cda7a368695e1c0b99c512cb7d4bae"

def fetch_waqi_city(city):
    url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get("status") == "ok":
            iaqi = data["data"].get("iaqi", {})
            return {
                "status": "success",
                "city": data["data"]["city"]["name"],
                "aqi": data["data"].get("aqi"),
                "pm25": iaqi.get("pm25", {}).get("v"),
                "pm10": iaqi.get("pm10", {}).get("v"),
                "co": iaqi.get("co", {}).get("v"),
                "so2": iaqi.get("so2", {}).get("v"),
                "no2": iaqi.get("no2", {}).get("v"),
                "o3": iaqi.get("o3", {}).get("v"),
                "temperature": iaqi.get("t", {}).get("v"),
                "humidity": iaqi.get("h", {}).get("v"),
                "pressure": iaqi.get("p", {}).get("v"),
                "wind_speed": iaqi.get("w", {}).get("v"),
                "time": data["data"]["time"]["iso"]
            }
        else:
            return {"status": "error", "error": data.get("data", "Unknown error")}
    except Exception as e:
        return {"status": "error", "error": str(e)}

class DataValidator:
    """Validate real-time air quality data"""
    
    @staticmethod
    def validate_pm25(value: float) -> bool:
        """Validate PM2.5 readings"""
        return 0 <= value <= 1000  # Reasonable range for PM2.5
    
    @staticmethod
    def validate_aqi(value: int) -> bool:
        """Validate AQI readings"""
        return 0 <= value <= 500  # Standard AQI range
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive data validation"""
        validated = data.copy()
        issues = []
        
        # Validate PM2.5
        if not cls.validate_pm25(data.get("pm25", 0)):
            issues.append("Invalid PM2.5 reading")
            validated["pm25"] = max(0, min(1000, data.get("pm25", 0)))
        
        # Validate AQI
        if not cls.validate_aqi(data.get("aqi", 0)):
            issues.append("Invalid AQI reading")
            validated["aqi"] = max(0, min(500, data.get("aqi", 0)))
        
        # Add validation metadata
        validated["validation"] = {
            "passed": len(issues) == 0,
            "issues": issues,
            "validated_at": datetime.now().isoformat()
        }
        
        return validated

class AQIDataProvider:
    """Real-time air quality data from AQI.in"""
    
    def __init__(self):
        self.base_url = "https://api.aqi.in/api/v1"
        self.timeout = 10.0
    
    async def get_dhaka_aqi(self) -> Dict[str, Any]:
        """Get real-time AQI data for Dhaka, Bangladesh"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # AQI.in endpoint for Dhaka
                response = await client.get(
                    f"{self.base_url}/current",
                    params={
                        "city": "Dhaka",
                        "country": "Bangladesh",
                        "format": "json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "source": "AQI.in",
                        "city": "Dhaka",
                        "country": "Bangladesh",
                        "aqi": data.get("aqi", 0),
                        "pm25": data.get("pm25", 0),
                        "pm10": data.get("pm10", 0),
                        "status": data.get("status", "Unknown"),
                        "timestamp": datetime.now().isoformat(),
                        "coordinates": {"lat": 23.8103, "lon": 90.4125}
                    }
                else:
                    return await self._get_fallback_dhaka_data()
                    
        except Exception as e:
            print(f"AQI.in API error: {e}")
            return await self._get_fallback_dhaka_data()
    
    async def _get_fallback_dhaka_data(self) -> Dict[str, Any]:
        """Fallback data based on historical patterns"""
        # Dhaka typically has high pollution levels
        base_pm25 = random.uniform(80, 200)  # Realistic range for Dhaka
        aqi = min(500, int(base_pm25 * 2.5))  # Approximate AQI calculation
        
        return {
            "source": "AQI.in (Simulated)",
            "city": "Dhaka",
            "country": "Bangladesh", 
            "aqi": aqi,
            "pm25": round(base_pm25, 1),
            "pm10": round(base_pm25 * 1.2, 1),
            "status": "Unhealthy" if base_pm25 > 100 else "Moderate",
            "timestamp": datetime.now().isoformat(),
            "coordinates": {"lat": 23.8103, "lon": 90.4125},
            "note": "Fallback data - API unavailable"
        }

class IQAirDataProvider:
    """Real-time air quality data from IQAir"""
    
    def __init__(self):
        self.base_url = "https://api.airvisual.com/v2"
        self.api_key = os.getenv("IQAIR_API_KEY", "demo_key")
        self.timeout = 10.0
    
    async def get_kolkata_aqi(self) -> Dict[str, Any]:
        """Get real-time AQI data for Kolkata, India"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # IQAir endpoint for Kolkata
                response = await client.get(
                    f"{self.base_url}/city",
                    params={
                        "city": "Kolkata",
                        "state": "West Bengal", 
                        "country": "India",
                        "key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current = data.get("data", {}).get("current", {})
                    pollution = current.get("pollution", {})
                    weather = current.get("weather", {})
                    
                    return {
                        "source": "IQAir",
                        "city": "Kolkata",
                        "country": "India",
                        "aqi": pollution.get("aqius", 0),
                        "pm25": pollution.get("p2", {}).get("conc", 0),
                        "status": self._get_aqi_status(pollution.get("aqius", 0)),
                        "temperature": weather.get("tp", 0),
                        "humidity": weather.get("hu", 0),
                        "wind_speed": weather.get("ws", 0),
                        "timestamp": datetime.now().isoformat(),
                        "coordinates": {"lat": 22.5726, "lon": 88.3639}
                    }
                else:
                    return await self._get_fallback_kolkata_data()
                    
        except Exception as e:
            print(f"IQAir API error: {e}")
            return await self._get_fallback_kolkata_data()
    
    def _get_aqi_status(self, aqi: int) -> str:
        """Convert AQI number to status"""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    async def _get_fallback_kolkata_data(self) -> Dict[str, Any]:
        """Fallback data for Kolkata"""
        # Kolkata typically has moderate pollution
        base_pm25 = random.uniform(40, 80)
        aqi = min(200, int(base_pm25 * 2))
        
        return {
            "source": "IQAir (Simulated)",
            "city": "Kolkata", 
            "country": "India",
            "aqi": aqi,
            "pm25": round(base_pm25, 1),
            "status": self._get_aqi_status(aqi),
            "temperature": random.uniform(25, 35),
            "humidity": random.uniform(60, 85),
            "wind_speed": random.uniform(2, 8),
            "timestamp": datetime.now().isoformat(),
            "coordinates": {"lat": 22.5726, "lon": 88.3639},
            "note": "Fallback data - API unavailable"
        }

# Initialize data providers
aqi_provider = AQIDataProvider()
iqair_provider = IQAirDataProvider()

# Real-time air quality endpoints
@app.get("/api/air-quality/dhaka")
async def get_dhaka_air_quality():
    """Server-side proxy for Dhaka air quality data"""
    try:
        data = await aqi_provider.get_dhaka_aqi()
        validated_data = DataValidator.validate_data(data)
        
        return JSONResponse(
            content={
                "status": "success",
                "data": validated_data,
                "cors_resolved": True,
                "server_proxy": True
            },
            headers={
                "Cache-Control": "max-age=300",  # Cache for 5 minutes
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Dhaka air quality: {str(e)}"
        )

@app.get("/api/air-quality/kolkata")
async def get_kolkata_air_quality():
    """Server-side proxy for Kolkata air quality data"""
    try:
        data = await iqair_provider.get_kolkata_aqi()
        validated_data = DataValidator.validate_data(data)
        
        return JSONResponse(
            content={
                "status": "success", 
                "data": validated_data,
                "cors_resolved": True,
                "server_proxy": True
            },
            headers={
                "Cache-Control": "max-age=300",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Kolkata air quality: {str(e)}"
        )

@app.get("/api/air-quality/comparison")
async def get_air_quality_comparison():
    """Compare air quality between Dhaka and Kolkata"""
    try:
        # Fetch data concurrently
        dhaka_task = aqi_provider.get_dhaka_aqi()
        kolkata_task = iqair_provider.get_kolkata_aqi()
        
        dhaka_data, kolkata_data = await asyncio.gather(dhaka_task, kolkata_task)
        
        # Validate data
        validated_dhaka = DataValidator.validate_data(dhaka_data)
        validated_kolkata = DataValidator.validate_data(kolkata_data)
        
        # Calculate comparison metrics
        pm25_diff = validated_dhaka["pm25"] - validated_kolkata["pm25"]
        pollution_ratio = validated_dhaka["pm25"] / validated_kolkata["pm25"] if validated_kolkata["pm25"] > 0 else 0
        
        return JSONResponse(
            content={
                "status": "success",
                "comparison": {
                    "dhaka": validated_dhaka,
                    "kolkata": validated_kolkata,
                    "analysis": {
                        "pm25_difference": round(pm25_diff, 1),
                        "pollution_ratio": round(pollution_ratio, 2),
                        "worse_city": "Dhaka" if pm25_diff > 0 else "Kolkata",
                        "health_impact": "High cross-border concern" if max(validated_dhaka["pm25"], validated_kolkata["pm25"]) > 100 else "Moderate concern"
                    }
                },
                "timestamp": datetime.now().isoformat(),
                "cors_resolved": True
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch comparison data: {str(e)}"
        )

# Proxy endpoints to handle CORS
@app.get("/api/proxy/{service}/health")
async def proxy_health(service: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SERVICES[service]}/health", timeout=10.0)
            return response.json()
        except Exception as e:
            return {"error": str(e), "service": service, "status": "proxy_error"}

@app.post("/api/proxy/{service}/{endpoint}")
async def proxy_endpoint(service: str, endpoint: str, request: Request):
    async with httpx.AsyncClient() as client:
        try:
            body = await request.json() if request.headers.get("content-type") == "application/json" else {}
            response = await client.post(f"{SERVICES[service]}/{endpoint}", json=body, timeout=10.0)
            return response.json()
        except Exception as e:
            return {"error": str(e), "service": service, "endpoint": endpoint, "status": "proxy_error"}

@app.api_route("/api/proxy/bangladesh/collect", methods=["GET", "POST"])
async def bangladesh_collect():
    result = fetch_waqi_city("dhaka")
    if result.get("status") == "success":
        return result
    # fallback demo data
    return {
        "status": "success",
        "city": "Dhaka",
        "aqi": 59,
        "pm25": 13,
        "pm10": 34,
        "co": 356,
        "so2": 2,
        "no2": 8,
        "o3": 14,
        "temperature": 28,
        "humidity": 85,
        "pressure": 1007,
        "wind_speed": 5,
        "time": "2025-06-25T12:00:00+06:00",
        "source": "demo-fallback"
    }

@app.api_route("/api/proxy/india/collect", methods=["GET", "POST"])
async def india_collect():
    result = fetch_waqi_city("kolkata")
    if result.get("status") == "success":
        return result
    # fallback demo data
    return {
        "status": "success",
        "city": "Kolkata",
        "aqi": 72,
        "pm25": 22,
        "pm10": 40,
        "co": 400,
        "so2": 3,
        "no2": 12,
        "o3": 18,
        "temperature": 30,
        "humidity": 80,
        "pressure": 1005,
        "wind_speed": 6,
        "time": "2025-06-25T12:00:00+05:30",
        "source": "demo-fallback"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "AQMS Interactive Demo with Real-Time Data",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "cors_enabled": True,
        "proxy_enabled": True,
        "real_time_data": True,
        "data_sources": ["AQI.in", "IQAir"]
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("interactive_demo.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/favicon.ico")
async def favicon():
    favicon_path = "favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    # 1x1 transparent gif fallback
    return HTMLResponse(
        content=(
            "GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!"
            "\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
            "\x00\x02\x02D\x01\x00;"
        ),
        media_type="image/gif"
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 