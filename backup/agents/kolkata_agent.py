"""
Kolkata Meteorological Analyzer Agent
Parallel agent for concurrent processing of meteorological data and traffic patterns
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import random
import math

# Simulated Google ADK imports
class ParallelAgent:
    def __init__(self, name: str, sub_agents: List[Any], protocol: Any = None):
        self.name = name
        self.sub_agents = sub_agents
        self.protocol = protocol
        self.logger = logging.getLogger(name)
    
    async def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute parallel processing"""
        pass
    
    def merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from parallel processing"""
        pass

class WeatherTool:
    def __init__(self, model: str):
        self.model = model
    
    async def execute(self) -> Dict[str, Any]:
        """Execute weather data collection"""
        pass

class SatelliteTool:
    def __init__(self, source: str):
        self.source = source
    
    async def execute(self) -> Dict[str, Any]:
        """Execute satellite data collection"""
        pass

class TrafficCounterTool:
    def __init__(self):
        self.name = "traffic_counter"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute traffic data collection"""
        pass

# Import our schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.air_quality import WeatherData, EmissionSource
from communication.protocols import BangladeshIndiaProtocol

@dataclass
class WeatherStation:
    """Configuration for weather monitoring stations"""
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    elevation: float
    station_type: str  # "surface", "upper_air", "automatic"
    is_active: bool = True

@dataclass
class TrafficCounter:
    """Configuration for traffic counting stations"""
    counter_id: str
    location_name: str
    latitude: float
    longitude: float
    road_type: str  # "highway", "arterial", "local"
    vehicle_types: List[str]
    is_active: bool = True

class WRFWeatherModel:
    """
    Weather Research and Forecasting (WRF) model integration
    """
    
    def __init__(self):
        self.model_name = "WRF-Chem v4.3"
        self.domain_config = {
            "center_lat": 22.5726,  # Kolkata coordinates
            "center_lon": 88.3639,
            "resolution": 1.0,  # 1 km resolution
            "domain_size": (100, 100),  # 100x100 km domain
            "vertical_levels": 35
        }
        
        self.forecast_hours = 72  # 3-day forecast
        self.update_interval = 6  # 6-hour model updates
    
    async def get_current_conditions(self) -> Dict[str, Any]:
        """
        Get current meteorological conditions from WRF model
        """
        # Simulate WRF model data retrieval
        await asyncio.sleep(0.3)  # Simulate model processing time
        
        # Generate realistic meteorological data for Kolkata
        base_temp = 28  # Typical temperature for Kolkata
        season_factor = math.sin((datetime.now().timetuple().tm_yday / 365.0) * 2 * math.pi)
        
        current_conditions = {
            "timestamp": datetime.now().isoformat(),
            "model_name": self.model_name,
            "forecast_hour": 0,  # Current conditions
            "coordinates": {
                "type": "Point",
                "coordinates": [88.3639, 22.5726]
            },
            
            # Surface meteorology
            "temperature_2m": round(base_temp + season_factor * 8 + random.uniform(-3, 3), 1),
            "humidity_2m": round(random.uniform(65, 85), 1),
            "wind_speed_10m": round(random.uniform(2, 12), 1),
            "wind_direction_10m": round(random.uniform(0, 360), 0),
            "surface_pressure": round(random.uniform(1008, 1018), 1),
            
            # Boundary layer parameters
            "boundary_layer_height": round(random.uniform(800, 2000), 0),
            "mixing_ratio": round(random.uniform(12, 18), 2),
            
            # Precipitation
            "precipitation": round(max(0, random.gauss(0, 2)), 1),
            
            # Visibility and atmospheric conditions
            "visibility": round(random.uniform(5, 15), 1),
            "cloud_cover": round(random.uniform(20, 80), 0)
        }
        
        return current_conditions
    
    async def get_forecast(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get meteorological forecast for specified hours
        """
        forecast_data = []
        
        for hour in range(1, min(hours + 1, self.forecast_hours + 1)):
            await asyncio.sleep(0.05)  # Simulate processing time
            
            # Generate forecast data with some temporal correlation
            base_conditions = await self.get_current_conditions()
            
            # Add temporal trends
            temp_trend = random.uniform(-0.5, 0.5) * hour
            wind_trend = random.uniform(-0.2, 0.2) * hour
            
            forecast_point = base_conditions.copy()
            forecast_point.update({
                "timestamp": (datetime.now() + timedelta(hours=hour)).isoformat(),
                "forecast_hour": hour,
                "temperature_2m": round(base_conditions["temperature_2m"] + temp_trend, 1),
                "wind_speed_10m": round(max(0, base_conditions["wind_speed_10m"] + wind_trend), 1),
                "boundary_layer_height": round(base_conditions["boundary_layer_height"] * 
                                             (1 + random.uniform(-0.2, 0.2)), 0)
            })
            
            forecast_data.append(forecast_point)
        
        return forecast_data
    
    def calculate_dispersion_parameters(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate atmospheric dispersion parameters from weather data
        """
        wind_speed = weather_data.get("wind_speed_10m", 5)
        boundary_layer_height = weather_data.get("boundary_layer_height", 1000)
        temperature = weather_data.get("temperature_2m", 25)
        
        # Pasquill stability classification
        if wind_speed < 2:
            stability_class = "F"  # Very stable
        elif wind_speed < 3:
            stability_class = "E"  # Stable
        elif wind_speed < 5:
            stability_class = "D"  # Neutral
        elif wind_speed < 6:
            stability_class = "C"  # Slightly unstable
        else:
            stability_class = "B"  # Unstable
        
        # Mixing height factor
        mixing_factor = min(1.0, boundary_layer_height / 1500.0)
        
        # Ventilation coefficient (wind speed × mixing height)
        ventilation_coefficient = wind_speed * boundary_layer_height / 1000.0
        
        return {
            "stability_class": stability_class,
            "mixing_factor": round(mixing_factor, 3),
            "ventilation_coefficient": round(ventilation_coefficient, 1),
            "dispersion_favorable": ventilation_coefficient > 5000,
            "stagnation_risk": wind_speed < 2 and boundary_layer_height < 800
        }

class INSATSatelliteData:
    """
    INSAT-3DR satellite data integration for aerosol and atmospheric monitoring
    """
    
    def __init__(self):
        self.satellite_name = "INSAT-3DR"
        self.refresh_interval = 300  # 5 minutes
        self.spatial_resolution = 4.0  # 4 km resolution
        
    async def get_aerosol_data(self) -> Dict[str, Any]:
        """
        Get aerosol optical depth and related parameters
        """
        await asyncio.sleep(0.2)  # Simulate satellite data processing
        
        # Generate realistic aerosol data for Kolkata region
        base_aod = 0.6  # Typical AOD for Kolkata
        seasonal_variation = math.sin((datetime.now().timetuple().tm_yday / 365.0) * 2 * math.pi) * 0.3
        
        aerosol_data = {
            "timestamp": datetime.now().isoformat(),
            "satellite": self.satellite_name,
            "spatial_resolution_km": self.spatial_resolution,
            
            # Aerosol parameters
            "aerosol_optical_depth_550nm": round(base_aod + seasonal_variation + random.uniform(-0.2, 0.3), 3),
            "aerosol_optical_depth_865nm": round((base_aod + seasonal_variation) * 0.7 + random.uniform(-0.1, 0.2), 3),
            "angstrom_exponent": round(random.uniform(0.8, 1.6), 2),
            
            # Atmospheric parameters
            "water_vapor_cm": round(random.uniform(2.5, 4.5), 1),
            "cloud_fraction": round(random.uniform(0.2, 0.8), 2),
            "surface_reflectance": round(random.uniform(0.05, 0.15), 3),
            
            # Quality flags
            "data_quality": "good" if random.random() > 0.1 else "moderate",
            "cloud_contamination": random.random() < 0.3,
            "sun_glint": random.random() < 0.1
        }
        
        return aerosol_data
    
    async def get_atmospheric_profile(self) -> Dict[str, Any]:
        """
        Get atmospheric temperature and humidity profiles
        """
        await asyncio.sleep(0.15)
        
        # Generate vertical profiles (simplified)
        pressure_levels = [1000, 925, 850, 700, 500, 300, 200, 100]  # hPa
        temperatures = []
        humidities = []
        
        surface_temp = 28 + random.uniform(-3, 3)
        surface_humidity = 75 + random.uniform(-10, 10)
        
        for i, pressure in enumerate(pressure_levels):
            # Temperature decreases with altitude
            temp = surface_temp - (i * 6.5)  # Standard lapse rate
            temperatures.append(round(temp, 1))
            
            # Humidity generally decreases with altitude
            humidity = surface_humidity * (pressure / 1000.0) ** 0.5
            humidities.append(round(max(5, humidity), 1))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "satellite": self.satellite_name,
            "pressure_levels_hpa": pressure_levels,
            "temperature_profile_c": temperatures,
            "humidity_profile_percent": humidities,
            "tropopause_height_km": round(random.uniform(16, 18), 1),
            "precipitable_water_mm": round(random.uniform(40, 60), 1)
        }

class KolkataTrafficMonitor:
    """
    Traffic monitoring system for Kolkata emission source tracking
    """
    
    def __init__(self):
        self.counter_network = self._initialize_traffic_counters()
        self.vehicle_emission_factors = {
            "cars": 0.12,  # kg PM2.5 per vehicle-km
            "buses": 0.85,
            "trucks": 1.2,
            "motorcycles": 0.08,
            "auto_rickshaws": 0.15
        }
    
    def _initialize_traffic_counters(self) -> List[TrafficCounter]:
        """
        Initialize traffic counter network across Kolkata
        """
        counters = [
            TrafficCounter("KOL_TC_001", "EM Bypass - Gariahat", 22.4953, 88.3665, "highway", 
                          ["cars", "buses", "trucks", "motorcycles"]),
            TrafficCounter("KOL_TC_002", "VIP Road - Airport", 22.6533, 88.4467, "highway",
                          ["cars", "buses", "trucks", "motorcycles"]),
            TrafficCounter("KOL_TC_003", "AJC Bose Road - Park Street", 22.5448, 88.3426, "arterial",
                          ["cars", "buses", "auto_rickshaws", "motorcycles"]),
            TrafficCounter("KOL_TC_004", "Strand Road - BBD Bagh", 22.5726, 88.3639, "arterial",
                          ["cars", "buses", "trucks", "auto_rickshaws"]),
            TrafficCounter("KOL_TC_005", "Jessore Road - Dum Dum", 22.6757, 88.4372, "arterial",
                          ["cars", "buses", "motorcycles", "auto_rickshaws"]),
        ]
        
        # Add more counters for comprehensive coverage
        for i in range(6, 215):  # Total 214 counters as mentioned in requirements
            lat = 22.4 + random.uniform(0, 0.4)
            lon = 88.2 + random.uniform(0, 0.4)
            road_types = ["highway", "arterial", "local"]
            
            counters.append(TrafficCounter(
                f"KOL_TC_{i:03d}",
                f"Location_{i}",
                lat, lon,
                random.choice(road_types),
                ["cars", "motorcycles", "auto_rickshaws"]
            ))
        
        return counters
    
    async def get_traffic_data(self) -> Dict[str, Any]:
        """
        Collect traffic data from all active counters
        """
        traffic_tasks = []
        for counter in self.counter_network:
            if counter.is_active:
                traffic_tasks.append(self._collect_counter_data(counter))
        
        counter_results = await asyncio.gather(*traffic_tasks)
        
        # Aggregate traffic data
        total_vehicles = {vehicle_type: 0 for vehicle_type in self.vehicle_emission_factors.keys()}
        total_emissions = 0
        active_counters = 0
        
        for result in counter_results:
            if result:
                active_counters += 1
                for vehicle_type, count in result["vehicle_counts"].items():
                    total_vehicles[vehicle_type] += count
                total_emissions += result["estimated_emissions"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_counters": active_counters,
            "total_counters": len(self.counter_network),
            "vehicle_counts": total_vehicles,
            "total_estimated_emissions_kg_hour": round(total_emissions, 2),
            "average_traffic_density": round(sum(total_vehicles.values()) / active_counters if active_counters > 0 else 0, 1),
            "peak_hour_factor": self._calculate_peak_hour_factor()
        }
    
    async def _collect_counter_data(self, counter: TrafficCounter) -> Optional[Dict[str, Any]]:
        """
        Collect data from a single traffic counter
        """
        try:
            await asyncio.sleep(0.02)  # Simulate data collection time
            
            # Generate realistic traffic counts based on road type and time
            hour = datetime.now().hour
            peak_factor = 1.5 if 7 <= hour <= 9 or 17 <= hour <= 19 else 1.0
            
            base_counts = {
                "highway": {"cars": 800, "buses": 50, "trucks": 100, "motorcycles": 400},
                "arterial": {"cars": 400, "buses": 30, "trucks": 20, "motorcycles": 300, "auto_rickshaws": 150},
                "local": {"cars": 150, "buses": 5, "trucks": 5, "motorcycles": 200, "auto_rickshaws": 100}
            }
            
            vehicle_counts = {}
            total_emissions = 0
            
            for vehicle_type in counter.vehicle_types:
                base_count = base_counts[counter.road_type].get(vehicle_type, 0)
                actual_count = int(base_count * peak_factor * random.uniform(0.7, 1.3))
                vehicle_counts[vehicle_type] = actual_count
                
                # Calculate emissions (simplified)
                if vehicle_type in self.vehicle_emission_factors:
                    emissions = actual_count * self.vehicle_emission_factors[vehicle_type] * 0.1  # per hour
                    total_emissions += emissions
            
            return {
                "counter_id": counter.counter_id,
                "location": counter.location_name,
                "coordinates": [counter.longitude, counter.latitude],
                "road_type": counter.road_type,
                "vehicle_counts": vehicle_counts,
                "estimated_emissions": total_emissions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error collecting from counter {counter.counter_id}: {e}")
            return None
    
    def _calculate_peak_hour_factor(self) -> float:
        """
        Calculate current peak hour factor based on time of day
        """
        hour = datetime.now().hour
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 1.5  # Peak hours
        elif 10 <= hour <= 16:
            return 1.2  # Moderate traffic
        elif 20 <= hour <= 22:
            return 1.1  # Evening traffic
        else:
            return 0.7  # Off-peak hours

class KolkataAgent(ParallelAgent):
    """
    Main Kolkata meteorological analyzer agent implementing parallel processing
    """
    
    def __init__(self):
        # Initialize sub-agents/tools
        self.weather_model = WRFWeatherModel()
        self.satellite_tool = INSATSatelliteData()
        self.traffic_monitor = KolkataTrafficMonitor()
        
        # Communication protocol for cross-border coordination
        self.communication_protocol = BangladeshIndiaProtocol(
            country_code="IN",
            api_endpoint="https://api.india-aqms.gov.in",
            auth_token="in_auth_token_placeholder"
        )
        
        super().__init__(
            name="kolkata_met_agent",
            sub_agents=[self.weather_model, self.satellite_tool, self.traffic_monitor],
            protocol=self.communication_protocol
        )
        
        self.processing_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "last_run": None,
            "average_processing_time": 0
        }
    
    async def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute parallel processing workflow for meteorological analysis
        """
        start_time = datetime.now()
        self.logger.info("Starting Kolkata meteorological analysis workflow")
        
        try:
            # Execute parallel data collection from all sources
            self.logger.info("Executing parallel data collection")
            
            # Run all data collection tasks concurrently
            weather_task = self.weather_model.get_current_conditions()
            forecast_task = self.weather_model.get_forecast(24)
            aerosol_task = self.satellite_tool.get_aerosol_data()
            atmospheric_task = self.satellite_tool.get_atmospheric_profile()
            traffic_task = self.traffic_monitor.get_traffic_data()
            
            # Wait for all tasks to complete
            results = await asyncio.gather(
                weather_task,
                forecast_task,
                aerosol_task,
                atmospheric_task,
                traffic_task,
                return_exceptions=True
            )
            
            # Process results and handle any exceptions
            weather_data, forecast_data, aerosol_data, atmospheric_data, traffic_data = results
            
            # Check for exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Task {i} failed: {result}")
                    # Set default values for failed tasks
                    if i == 0:  # weather_data
                        weather_data = {"error": "weather_data_unavailable"}
                    elif i == 1:  # forecast_data
                        forecast_data = []
                    elif i == 2:  # aerosol_data
                        aerosol_data = {"error": "aerosol_data_unavailable"}
                    elif i == 3:  # atmospheric_data
                        atmospheric_data = {"error": "atmospheric_data_unavailable"}
                    elif i == 4:  # traffic_data
                        traffic_data = {"error": "traffic_data_unavailable"}
            
            # Merge and analyze results
            merged_results = self.merge_results([weather_data, aerosol_data, traffic_data])
            
            # Calculate transboundary transport potential
            transport_analysis = self._analyze_transboundary_transport(weather_data, aerosol_data)
            
            # Generate emission estimates
            emission_estimates = self._estimate_local_emissions(traffic_data, weather_data)
            
            # Share relevant data with Bangladesh
            sharing_success = await self._share_cross_border_data(merged_results, transport_analysis)
            
            # Update processing statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_processing_stats(processing_time)
            
            # Prepare comprehensive result
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": round(processing_time, 2),
                "data_sources": {
                    "weather_model": "available" if "error" not in weather_data else "unavailable",
                    "satellite_data": "available" if "error" not in aerosol_data else "unavailable",
                    "traffic_monitoring": "available" if "error" not in traffic_data else "unavailable"
                },
                "current_conditions": merged_results,
                "forecast_summary": {
                    "hours_available": len(forecast_data) if isinstance(forecast_data, list) else 0,
                    "next_24h_trend": self._analyze_forecast_trend(forecast_data) if isinstance(forecast_data, list) else "unavailable"
                },
                "transboundary_analysis": transport_analysis,
                "emission_estimates": emission_estimates,
                "cross_border_sharing": sharing_success
            }
            
            self.logger.info(f"Workflow completed successfully in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from parallel data collection
        """
        weather_data, aerosol_data, traffic_data = results
        
        merged = {
            "timestamp": datetime.now().isoformat(),
            "location": "Kolkata",
            "country": "IN"
        }
        
        # Merge weather data
        if "error" not in weather_data:
            merged.update({
                "wind_patterns": {
                    "speed_ms": weather_data.get("wind_speed_10m"),
                    "direction_deg": weather_data.get("wind_direction_10m"),
                    "boundary_layer_height_m": weather_data.get("boundary_layer_height")
                },
                "atmospheric_conditions": {
                    "temperature_c": weather_data.get("temperature_2m"),
                    "humidity_percent": weather_data.get("humidity_2m"),
                    "pressure_hpa": weather_data.get("surface_pressure"),
                    "visibility_km": weather_data.get("visibility")
                }
            })
            
            # Calculate dispersion parameters
            dispersion = self.weather_model.calculate_dispersion_parameters(weather_data)
            merged["dispersion_conditions"] = dispersion
        
        # Merge aerosol data
        if "error" not in aerosol_data:
            merged["aerosol_conditions"] = {
                "optical_depth": aerosol_data.get("aerosol_optical_depth_550nm"),
                "atmospheric_loading": "high" if aerosol_data.get("aerosol_optical_depth_550nm", 0) > 0.7 else "moderate",
                "data_quality": aerosol_data.get("data_quality")
            }
        
        # Merge traffic data
        if "error" not in traffic_data:
            merged["traffic_conditions"] = {
                "total_vehicles_hour": sum(traffic_data.get("vehicle_counts", {}).values()),
                "estimated_emissions_kg_hour": traffic_data.get("total_estimated_emissions_kg_hour"),
                "traffic_density": traffic_data.get("average_traffic_density"),
                "peak_factor": traffic_data.get("peak_hour_factor")
            }
        
        return merged
    
    def _analyze_transboundary_transport(self, weather_data: Dict[str, Any], aerosol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze potential for transboundary pollution transport
        """
        if "error" in weather_data:
            return {"status": "unavailable", "reason": "weather_data_missing"}
        
        wind_speed = weather_data.get("wind_speed_10m", 0)
        wind_direction = weather_data.get("wind_direction_10m", 0)
        boundary_layer_height = weather_data.get("boundary_layer_height", 1000)
        
        # Determine transport direction (simplified)
        # Wind direction is where wind is coming FROM
        # For transport TO Bangladesh, wind should be from SE (135-225 degrees)
        transport_to_bangladesh = 135 <= wind_direction <= 225
        transport_from_bangladesh = 315 <= wind_direction or wind_direction <= 45
        
        # Calculate transport potential
        transport_potential = "low"
        if wind_speed > 5 and boundary_layer_height > 1000:
            if transport_to_bangladesh or transport_from_bangladesh:
                transport_potential = "high"
            else:
                transport_potential = "moderate"
        elif wind_speed > 3:
            transport_potential = "moderate"
        
        # Estimate transport time to border (simplified)
        distance_to_border_km = 50  # Approximate distance from Kolkata to Bangladesh border
        if wind_speed > 0:
            transport_time_hours = distance_to_border_km / (wind_speed * 3.6)  # Convert m/s to km/h
        else:
            transport_time_hours = float('inf')
        
        return {
            "transport_potential": transport_potential,
            "wind_direction_deg": wind_direction,
            "wind_speed_ms": wind_speed,
            "transport_to_bangladesh": transport_to_bangladesh,
            "transport_from_bangladesh": transport_from_bangladesh,
            "estimated_transport_time_hours": round(transport_time_hours, 1) if transport_time_hours != float('inf') else None,
            "boundary_layer_height_m": boundary_layer_height,
            "favorable_dispersion": boundary_layer_height > 1200 and wind_speed > 4
        }
    
    def _estimate_local_emissions(self, traffic_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate local emission contributions
        """
        if "error" in traffic_data:
            return {"status": "unavailable", "reason": "traffic_data_missing"}
        
        # Base emission estimates
        traffic_emissions = traffic_data.get("total_estimated_emissions_kg_hour", 0)
        
        # Add other emission sources (simplified estimates)
        industrial_emissions = 15.0  # kg/hour baseline
        residential_emissions = 8.0   # kg/hour baseline
        construction_emissions = 5.0  # kg/hour baseline
        
        total_emissions = traffic_emissions + industrial_emissions + residential_emissions + construction_emissions
        
        # Adjust for meteorological conditions
        if "error" not in weather_data:
            wind_speed = weather_data.get("wind_speed_10m", 5)
            boundary_layer_height = weather_data.get("boundary_layer_height", 1000)
            
            # Lower wind speed and boundary layer height lead to higher concentrations
            meteorological_factor = (5.0 / max(wind_speed, 1.0)) * (1000.0 / max(boundary_layer_height, 500.0))
            effective_concentration_factor = min(meteorological_factor, 3.0)  # Cap at 3x
        else:
            effective_concentration_factor = 1.0
        
        return {
            "total_emissions_kg_hour": round(total_emissions, 2),
            "source_breakdown": {
                "traffic": round(traffic_emissions, 2),
                "industrial": industrial_emissions,
                "residential": residential_emissions,
                "construction": construction_emissions
            },
            "meteorological_factor": round(effective_concentration_factor, 2),
            "estimated_concentration_impact": round(total_emissions * effective_concentration_factor * 0.1, 1)  # Simplified conversion to µg/m³
        }
    
    def _analyze_forecast_trend(self, forecast_data: List[Dict[str, Any]]) -> str:
        """
        Analyze 24-hour forecast trend
        """
        if not forecast_data or len(forecast_data) < 6:
            return "insufficient_data"
        
        # Analyze wind speed trend
        wind_speeds = [f.get("wind_speed_10m", 0) for f in forecast_data[:12]]  # First 12 hours
        wind_trend = "increasing" if wind_speeds[-1] > wind_speeds[0] else "decreasing"
        
        # Analyze boundary layer height trend
        bl_heights = [f.get("boundary_layer_height", 1000) for f in forecast_data[:12]]
        bl_trend = "increasing" if bl_heights[-1] > bl_heights[0] else "decreasing"
        
        # Overall dispersion trend
        if wind_trend == "increasing" and bl_trend == "increasing":
            return "improving_dispersion"
        elif wind_trend == "decreasing" and bl_trend == "decreasing":
            return "worsening_dispersion"
        else:
            return "mixed_conditions"
    
    async def _share_cross_border_data(self, merged_results: Dict[str, Any], transport_analysis: Dict[str, Any]) -> bool:
        """
        Share relevant meteorological data with Bangladesh
        """
        try:
            # Prepare data for sharing
            shared_data = {
                "source_city": "Kolkata",
                "source_country": "IN",
                "timestamp": datetime.now().isoformat(),
                "meteorological_conditions": {
                    "wind_speed_ms": merged_results.get("wind_patterns", {}).get("speed_ms"),
                    "wind_direction_deg": merged_results.get("wind_patterns", {}).get("direction_deg"),
                    "boundary_layer_height_m": merged_results.get("wind_patterns", {}).get("boundary_layer_height_m"),
                    "temperature_c": merged_results.get("atmospheric_conditions", {}).get("temperature_c")
                },
                "transboundary_transport": transport_analysis,
                "data_quality": "operational"
            }
            
            # Send to Bangladesh
            success = await self.communication_protocol.send_data(shared_data, "BD")
            
            if success:
                self.logger.info("Successfully shared meteorological data with Bangladesh")
            else:
                self.logger.warning("Failed to share data with Bangladesh")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sharing cross-border data: {e}")
            return False
    
    def _update_processing_stats(self, processing_time: float):
        """
        Update processing statistics
        """
        self.processing_stats["total_runs"] += 1
        self.processing_stats["successful_runs"] += 1
        self.processing_stats["last_run"] = datetime.now().isoformat()
        
        # Update rolling average processing time
        total_time = (self.processing_stats["average_processing_time"] * 
                     (self.processing_stats["total_runs"] - 1) + processing_time)
        self.processing_stats["average_processing_time"] = total_time / self.processing_stats["total_runs"]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get comprehensive agent status
        """
        return {
            "agent_name": self.name,
            "status": "active",
            "processing_stats": self.processing_stats,
            "data_sources": {
                "weather_model": self.weather_model.model_name,
                "satellite": self.satellite_tool.satellite_name,
                "traffic_counters": len(self.traffic_monitor.counter_network)
            },
            "last_updated": datetime.now().isoformat()
        }

# Example usage and testing
async def main():
    """
    Example usage of the Kolkata Agent
    """
    # Initialize and run the agent
    agent = KolkataAgent()
    
    # Run a single analysis cycle
    result = await agent.run()
    print("Analysis Result:")
    print(json.dumps(result, indent=2))
    
    # Get agent status
    status = agent.get_agent_status()
    print("\nAgent Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())

