# API Specification for Transnational Air Quality Management System

## Overview

The Transnational Air Quality Management System provides RESTful APIs for cross-border air quality monitoring, policy coordination, and alert management. The API is designed to support both country-specific agents and regional orchestration services.

## Base URLs

- **Bangladesh Service:** `https://aqms-bangladesh-r5hed7gtca-uc.a.run.app`
- **India Service:** `https://aqms-india-r5hed7gtca-uc.a.run.app`
- **Regional Orchestrator:** `https://aqms-orchestrator-r5hed7gtca-uc.a.run.app`

## Authentication

All API endpoints use Bearer token authentication:

```
Authorization: Bearer <token>
```

## Common Response Format

All API responses follow a consistent format:

```json
{
  "status": "success|error",
  "timestamp": "2025-06-06T14:30:00Z",
  "data": {},
  "error": "Error message if status is error"
}
```

## Endpoints

### Health Check

**GET** `/health`

Returns the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-06T14:30:00Z",
  "service_type": "agent",
  "country_code": "BD",
  "version": "1.0.0"
}
```

### Data Collection

**POST** `/collect`

Triggers data collection from monitoring stations (country-specific agents only).

**Request Body:**
```json
{
  "force_collection": false,
  "include_forecast": true
}
```

**Response:**
```json
{
  "status": "success",
  "country": "Bangladesh",
  "city": "Dhaka",
  "result": {
    "collection_summary": {
      "raw_measurements": 15,
      "valid_measurements": 14,
      "validation_rate": 0.93
    },
    "storage_success": true,
    "sharing_success": true
  },
  "timestamp": "2025-06-06T14:30:00Z"
}
```

### Regional Orchestration

**POST** `/orchestrate`

Triggers regional coordination workflow (orchestrator only).

**Request Body:**
```json
{
  "dhaka_data": {
    "pm25": 139.0,
    "timestamp": "2025-06-06T14:30:00Z",
    "wind_speed_ms": 3.5,
    "wind_direction_deg": 270,
    "country_code": "BD"
  },
  "kolkata_data": {
    "pm25": 45.6,
    "timestamp": "2025-06-06T14:30:00Z",
    "wind_speed_ms": 4.2,
    "wind_direction_deg": 90,
    "country_code": "IN"
  },
  "force_coordination": false
}
```

**Response:**
```json
{
  "status": "success",
  "orchestration_result": {
    "cities": {
      "dhaka": {
        "status": "success",
        "emission_analysis": {},
        "policy_recommendations": []
      },
      "kolkata": {
        "status": "success",
        "emission_analysis": {},
        "policy_recommendations": []
      }
    },
    "cross_border_coordination": {
      "coordinated_actions": [],
      "shared_data_quality": 0.95
    },
    "alerts": {
      "alerts": [],
      "distribution_success": true
    }
  },
  "timestamp": "2025-06-06T14:30:00Z"
}
```

### Service Status

**GET** `/status`

Returns detailed service status and operational metrics.

**Response:**
```json
{
  "service_type": "agent",
  "country_code": "BD",
  "timestamp": "2025-06-06T14:30:00Z",
  "environment": "production",
  "agent_status": {
    "total_collections": 1247,
    "successful_collections": 1198,
    "success_rate": 0.96,
    "last_collection_time": "2025-06-06T14:25:00Z"
  }
}
```

## Data Schemas

### Air Quality Measurement

```json
{
  "pm25": 139.0,
  "pm10": 180.5,
  "timestamp": "2025-06-06T14:30:00Z",
  "coordinates": [90.4125, 23.8103],
  "station_id": "CAMS_DHAKA_01",
  "country_code": "BD",
  "quality_grade": "reference",
  "meteorological_data": {
    "temperature": 28.5,
    "humidity": 75.0,
    "wind_speed": 3.2,
    "wind_direction": 270
  }
}
```

### Policy Recommendation

```json
{
  "pollution_level": "hazardous",
  "pm25_concentration": 139.0,
  "transboundary_contribution": 71.0,
  "recommendations": [
    "Implement emergency vehicle restrictions",
    "Close schools and outdoor activities",
    "Coordinate with neighboring country"
  ],
  "priority": "high",
  "estimated_effectiveness": 0.75,
  "implementation_timeline": "immediate"
}
```

## Error Codes

- **400 Bad Request:** Invalid request parameters
- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Endpoint not found
- **500 Internal Server Error:** Server error
- **503 Service Unavailable:** Service temporarily unavailable

