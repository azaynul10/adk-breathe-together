"""
Air Quality Data Schema for Transnational AQMS
Unified schema for cross-border air quality data harmonization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from geojson_pydantic import Point
import uuid

class AirQualityMeasurement(BaseModel):
    """
    Core air quality measurement schema supporting both government 
    and low-cost sensor data with cross-border standardization.
    """
    
    # Unique identifiers
    measurement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    station_id: str = Field(..., description="Unique station identifier")
    
    # Temporal information
    timestamp: datetime = Field(..., description="Measurement timestamp in UTC")
    local_timestamp: datetime = Field(..., description="Local timezone timestamp")
    
    # Spatial information
    coordinates: Point = Field(..., description="GeoJSON Point with WGS84 coordinates")
    elevation: Optional[float] = Field(None, description="Elevation in meters above sea level")
    
    # Air quality parameters (µg/m³)
    pm25: float = Field(..., ge=0, le=1000, description="PM2.5 concentration")
    pm10: Optional[float] = Field(None, ge=0, le=2000, description="PM10 concentration")
    no2: Optional[float] = Field(None, ge=0, le=500, description="NO2 concentration")
    so2: Optional[float] = Field(None, ge=0, le=1000, description="SO2 concentration")
    co: Optional[float] = Field(None, ge=0, le=50000, description="CO concentration")
    o3: Optional[float] = Field(None, ge=0, le=500, description="O3 concentration")
    
    # Meteorological parameters
    temperature: Optional[float] = Field(None, description="Temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity %")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed in m/s")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    pressure: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    
    # Data quality and source information
    measurement_type: Literal["government", "low_cost", "satellite", "model"] = Field(
        ..., description="Type of measurement source"
    )
    country_code: Literal["BD", "IN"] = Field(..., description="ISO country code")
    data_quality: Literal["valid", "questionable", "invalid"] = Field(
        default="valid", description="Data quality flag"
    )
    calibration_factor: Optional[float] = Field(
        None, description="Calibration factor applied for harmonization"
    )
    
    # Additional metadata
    source_agency: str = Field(..., description="Data source agency")
    processing_level: Literal["raw", "validated", "calibrated", "harmonized"] = Field(
        default="raw", description="Data processing level"
    )
    
    @validator('pm25')
    def validate_pm25(cls, v):
        """Validate PM2.5 values with regional context"""
        if v > 500:
            # Log extreme values but don't reject (dust storms, fires)
            pass
        return v
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        """Ensure coordinates are within South Asian region"""
        lon, lat = v.coordinates
        if not (80 <= lon <= 95 and 20 <= lat <= 30):
            raise ValueError("Coordinates outside expected South Asian region")
        return v

class WeatherData(BaseModel):
    """
    Meteorological data schema for transboundary pollution modeling
    """
    
    timestamp: datetime
    coordinates: Point
    
    # Surface meteorology
    temperature_2m: float = Field(..., description="2m temperature in Celsius")
    humidity_2m: float = Field(..., ge=0, le=100, description="2m relative humidity %")
    wind_speed_10m: float = Field(..., ge=0, description="10m wind speed in m/s")
    wind_direction_10m: float = Field(..., ge=0, le=360, description="10m wind direction")
    surface_pressure: float = Field(..., description="Surface pressure in hPa")
    
    # Boundary layer parameters
    boundary_layer_height: float = Field(..., ge=0, description="Boundary layer height in meters")
    mixing_ratio: Optional[float] = Field(None, description="Water vapor mixing ratio")
    
    # Precipitation
    precipitation: float = Field(default=0, ge=0, description="Precipitation in mm/hour")
    
    # Visibility and atmospheric conditions
    visibility: Optional[float] = Field(None, ge=0, description="Visibility in km")
    cloud_cover: Optional[float] = Field(None, ge=0, le=100, description="Cloud cover %")
    
    # Model-specific fields
    model_name: str = Field(..., description="Weather model name (e.g., WRF-Chem)")
    forecast_hour: int = Field(..., ge=0, description="Forecast hour from model initialization")

class EmissionSource(BaseModel):
    """
    Emission source data for source apportionment analysis
    """
    
    source_id: str = Field(..., description="Unique source identifier")
    source_type: Literal[
        "industrial", "vehicular", "residential", "agricultural", 
        "construction", "waste_burning", "brick_kiln", "power_plant"
    ]
    coordinates: Point
    
    # Emission rates (kg/hour)
    pm25_emission: float = Field(..., ge=0, description="PM2.5 emission rate")
    pm10_emission: Optional[float] = Field(None, ge=0, description="PM10 emission rate")
    nox_emission: Optional[float] = Field(None, ge=0, description="NOx emission rate")
    so2_emission: Optional[float] = Field(None, ge=0, description="SO2 emission rate")
    
    # Temporal patterns
    operating_hours: List[int] = Field(..., description="Operating hours (0-23)")
    seasonal_factor: float = Field(default=1.0, description="Seasonal adjustment factor")
    
    # Stack parameters (for point sources)
    stack_height: Optional[float] = Field(None, description="Stack height in meters")
    stack_diameter: Optional[float] = Field(None, description="Stack diameter in meters")
    exit_velocity: Optional[float] = Field(None, description="Exit velocity in m/s")
    exit_temperature: Optional[float] = Field(None, description="Exit temperature in Celsius")

class PolicyAction(BaseModel):
    """
    Policy action schema for automated response system
    """
    
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger_timestamp: datetime
    
    # Trigger conditions
    trigger_pm25: float = Field(..., description="PM2.5 level that triggered action")
    trigger_location: Point
    trigger_country: Literal["BD", "IN", "both"]
    
    # Action details
    action_type: Literal[
        "brick_kiln_shutdown", "odd_even_vehicles", "construction_halt",
        "school_closure", "industrial_audit", "street_watering",
        "public_advisory", "emergency_alert"
    ]
    action_description: str = Field(..., description="Detailed action description")
    
    # Scope and duration
    affected_area: Dict[str, Any] = Field(..., description="GeoJSON polygon of affected area")
    duration_hours: int = Field(..., ge=1, description="Action duration in hours")
    
    # Implementation details
    implementing_agency: str = Field(..., description="Responsible agency")
    notification_channels: List[str] = Field(..., description="Notification channels used")
    
    # Effectiveness tracking
    expected_reduction: Optional[float] = Field(None, description="Expected PM2.5 reduction %")
    actual_reduction: Optional[float] = Field(None, description="Measured PM2.5 reduction %")

class CrossBorderAlert(BaseModel):
    """
    Cross-border alert schema for transnational coordination
    """
    
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    
    # Alert classification
    severity: Literal["low", "moderate", "high", "emergency"]
    alert_type: Literal["pollution_spike", "transboundary_transport", "policy_coordination"]
    
    # Geographic scope
    origin_country: Literal["BD", "IN"]
    affected_countries: List[Literal["BD", "IN"]]
    affected_cities: List[str]
    
    # Pollution data
    current_pm25: float = Field(..., description="Current PM2.5 level")
    forecast_pm25: List[float] = Field(..., description="24-hour PM2.5 forecast")
    transboundary_contribution: float = Field(..., ge=0, le=100, description="% from transboundary sources")
    
    # Recommended actions
    recommended_actions: List[str] = Field(..., description="Recommended policy actions")
    coordination_required: bool = Field(..., description="Requires cross-border coordination")
    
    # Communication
    message_bengali: str = Field(..., description="Alert message in Bengali")
    message_hindi: str = Field(..., description="Alert message in Hindi")
    message_english: str = Field(..., description="Alert message in English")

# Schema registry for version management
SCHEMA_VERSION = "1.0.0"
SCHEMA_REGISTRY = {
    "air_quality": AirQualityMeasurement,
    "weather": WeatherData,
    "emissions": EmissionSource,
    "policy": PolicyAction,
    "alert": CrossBorderAlert
}

