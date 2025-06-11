"""
Dhaka PM2.5 Collector Agent
Sequential agent for collecting and processing air quality data from Dhaka monitoring stations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

class SequentialAgent:
    def __init__(self, name: str, tools: List[Any], protocol: Any = None):
        self.name = name
        self.tools = tools
        self.protocol = protocol
        self.logger = logging.getLogger(name)
    
    async def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the agent's workflow"""
        pass

class IoTool:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the tool's function"""
        pass

class BigQueryTool:
    def __init__(self, dataset: str, schema: Any = None):
        self.dataset = dataset
        self.schema = schema
    
    async def store(self, data: List[Dict[str, Any]]) -> bool:
        """Store data in BigQuery"""
        pass

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.air_quality import AirQualityMeasurement
from communication.protocols import BangladeshIndiaProtocol

@dataclass
class SensorConfig:
    """Configuration for individual sensors"""
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    sensor_type: str
    api_endpoint: str
    calibration_factor: float = 1.0
    is_active: bool = True

class DhakaAirQualityTool(IoTool):
    """
    Tool for collecting air quality data from Dhaka monitoring stations
    """
    
    def __init__(self):
        super().__init__(
            name="dhaka_air_quality_collector",
            config={
                "government_stations": 15,
                "low_cost_sensors": 32,
                "collection_interval": 300,  
                "api_timeout": 30
            }
        )
        
        
        self.government_stations = [
            SensorConfig("DH_GOV_001", "Dhanmondi", 23.7461, 90.3742, "BAM", "api.doe.gov.bd/station/001"),
            SensorConfig("DH_GOV_002", "Farmgate", 23.7588, 90.3892, "TEOM", "api.doe.gov.bd/station/002"),
            SensorConfig("DH_GOV_003", "Tejgaon", 23.7633, 90.3950, "BAM", "api.doe.gov.bd/station/003"),
            SensorConfig("DH_GOV_004", "Ramna", 23.7370, 90.3947, "TEOM", "api.doe.gov.bd/station/004"),
            SensorConfig("DH_GOV_005", "Gulshan", 23.7925, 90.4078, "BAM", "api.doe.gov.bd/station/005"),
            SensorConfig("DH_GOV_006", "Uttara", 23.8759, 90.3795, "TEOM", "api.doe.gov.bd/station/006"),
            SensorConfig("DH_GOV_007", "Old Dhaka", 23.7104, 90.4074, "BAM", "api.doe.gov.bd/station/007"),
            SensorConfig("DH_GOV_008", "Motijheel", 23.7330, 90.4172, "TEOM", "api.doe.gov.bd/station/008"),
            SensorConfig("DH_GOV_009", "Mirpur", 23.8103, 90.3654, "BAM", "api.doe.gov.bd/station/009"),
            SensorConfig("DH_GOV_010", "Wari", 23.7208, 90.4264, "TEOM", "api.doe.gov.bd/station/010"),
            SensorConfig("DH_GOV_011", "Savar", 23.8583, 90.2667, "BAM", "api.doe.gov.bd/station/011"),
            SensorConfig("DH_GOV_012", "Gazipur", 23.9999, 90.4203, "TEOM", "api.doe.gov.bd/station/012"),
            SensorConfig("DH_GOV_013", "Narayanganj", 23.6238, 90.4969, "BAM", "api.doe.gov.bd/station/013"),
            SensorConfig("DH_GOV_014", "Keraniganj", 23.6792, 90.3542, "TEOM", "api.doe.gov.bd/station/014"),
            SensorConfig("DH_GOV_015", "Tongi", 23.8979, 90.4026, "BAM", "api.doe.gov.bd/station/015")
        ]
        
        
        self.low_cost_sensors = [
            SensorConfig(f"DH_LC_{i:03d}", f"LowCost_{i}", 
                        23.7 + (i * 0.01), 90.35 + (i * 0.01), 
                        "PurpleAir", f"api.purpleair.com/sensor/{i}")
            for i in range(1, 33)
        ]
        
        self.all_sensors = self.government_stations + self.low_cost_sensors
    
    async def execute(self) -> List[Dict[str, Any]]:
        """
        Collect data from all active monitoring stations
        """
        import logging
        logger = logging.getLogger(self.name)
        logger.info(f"Starting data collection from {len(self.all_sensors)} sensors")
        
        
        tasks = []
        for sensor in self.all_sensors:
            if sensor.is_active:
                tasks.append(self._collect_from_sensor(sensor))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        
        valid_measurements = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to collect from sensor {self.all_sensors[i].station_id}: {result}")
            elif result:
                valid_measurements.append(result)
        
        logger.info(f"Successfully collected data from {len(valid_measurements)} sensors")
        return valid_measurements
    
    async def _collect_from_sensor(self, sensor: SensorConfig) -> Optional[Dict[str, Any]]:
        """
        Collect data from a single sensor
        """
        try:
            
            await asyncio.sleep(0.1)  
            
            
            import random
            base_pm25 = 120  
            variation = random.uniform(-30, 50)
            pm25_raw = max(0, base_pm25 + variation)
            
            
            if sensor.sensor_type == "PurpleAir":
                pm25_calibrated = pm25_raw * sensor.calibration_factor * 0.85  
            else:
                pm25_calibrated = pm25_raw
            from opentelemetry import metrics

            # Get the meter
            meter = metrics.get_meter(__name__)

            
            pm25_gauge = meter.create_gauge(
                name="custom.googleapis.com/pm25_level",
                description="PM2.5 level in Dhaka",
                unit="ug/m3"
            )

            
            pm25_gauge.set(pm25_calibrated, attributes={"station_id": sensor.station_id, "country_code": "BD"})
            
            measurement_data = {
                "measurement_id": f"{sensor.station_id}_{datetime.now().isoformat()}",
                "station_id": sensor.station_id,
                "timestamp": datetime.now().isoformat(),
                "local_timestamp": datetime.now().isoformat(),
                "coordinates": {
                    "type": "Point",
                    "coordinates": [sensor.longitude, sensor.latitude]
                },
                "pm25": round(pm25_calibrated, 1),
                "pm10": round(pm25_calibrated * 1.5, 1) if random.random() > 0.3 else None,
                "temperature": round(random.uniform(20, 35), 1),
                "humidity": round(random.uniform(60, 90), 1),
                "wind_speed": round(random.uniform(1, 8), 1),
                "wind_direction": round(random.uniform(0, 360), 0),
                "measurement_type": "government" if "GOV" in sensor.station_id else "low_cost",
                "country_code": "BD",
                "source_agency": "Department of Environment, Bangladesh",
                "processing_level": "calibrated" if sensor.sensor_type == "PurpleAir" else "validated"
            }
            
            return measurement_data
            
        except Exception as e:
            import logging
            logger = logging.getLogger("dhaka_sensor_collector")
            logger.error(f"Error collecting from sensor {sensor.station_id}: {e}")
            return None
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """
        Get status of all sensors
        """
        active_count = sum(1 for sensor in self.all_sensors if sensor.is_active)
        government_active = sum(1 for sensor in self.government_stations if sensor.is_active)
        lowcost_active = sum(1 for sensor in self.low_cost_sensors if sensor.is_active)
        
        return {
            "total_sensors": len(self.all_sensors),
            "active_sensors": active_count,
            "government_stations": {
                "total": len(self.government_stations),
                "active": government_active
            },
            "low_cost_sensors": {
                "total": len(self.low_cost_sensors),
                "active": lowcost_active
            },
            "last_updated": datetime.now().isoformat()
        }

class DhakaDataValidator:
    """
    Data validation and quality assurance for Dhaka measurements
    """
    
    def __init__(self):
        self.validation_rules = {
            "pm25_max": 900,  
            "pm25_min": 0,
            "temperature_max": 50,  
            "temperature_min": 5,   
            "humidity_max": 100,
            "humidity_min": 0,
            "wind_speed_max": 30,   
            "temporal_window": 3600  
        }
    
    def validate_measurement(self, measurement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single measurement and return validation results
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "quality_score": 1.0
        }
        
        
        pm25 = measurement.get("pm25", 0)
        if pm25 > self.validation_rules["pm25_max"]:
            validation_result["warnings"].append(f"PM2.5 value {pm25} exceeds maximum threshold")
            validation_result["quality_score"] *= 0.8
        
        if pm25 < self.validation_rules["pm25_min"]:
            validation_result["errors"].append(f"PM2.5 value {pm25} below minimum threshold")
            validation_result["is_valid"] = False
        
        
        temp = measurement.get("temperature")
        if temp is not None:
            if temp > self.validation_rules["temperature_max"] or temp < self.validation_rules["temperature_min"]:
                validation_result["warnings"].append(f"Temperature {temp}°C outside expected range")
                validation_result["quality_score"] *= 0.9
        
       
        try:
            timestamp = datetime.fromisoformat(measurement["timestamp"].replace('Z', '+00:00'))
            time_diff = abs((datetime.now() - timestamp.replace(tzinfo=None)).total_seconds())
            if time_diff > self.validation_rules["temporal_window"]:
                validation_result["warnings"].append(f"Measurement timestamp {time_diff}s old")
                validation_result["quality_score"] *= 0.95
        except Exception as e:
            validation_result["errors"].append(f"Invalid timestamp format: {e}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    def validate_batch(self, measurements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of measurements and return summary statistics
        """
        total_count = len(measurements)
        valid_count = 0
        warning_count = 0
        error_count = 0
        quality_scores = []
        
        for measurement in measurements:
            result = self.validate_measurement(measurement)
            if result["is_valid"]:
                valid_count += 1
            if result["warnings"]:
                warning_count += 1
            if result["errors"]:
                error_count += 1
            quality_scores.append(result["quality_score"])
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_measurements": total_count,
            "valid_measurements": valid_count,
            "measurements_with_warnings": warning_count,
            "measurements_with_errors": error_count,
            "validation_rate": valid_count / total_count if total_count > 0 else 0,
            "average_quality_score": avg_quality,
            "timestamp": datetime.now().isoformat()
        }

class DhakaAgent(SequentialAgent):
    """
    Main Dhaka PM2.5 collector agent implementing sequential workflow
    """
    
    def __init__(self):
        # Initialize tools
        self.air_quality_tool = DhakaAirQualityTool()
        self.validator = DhakaDataValidator()
        self.bigquery_tool = BigQueryTool(dataset="bangladesh_air_2025", schema=AirQualityMeasurement)
        self.communication_protocol = BangladeshIndiaProtocol(
            country_code="BD",
            api_endpoint="https://api.bangladesh-aqms.gov.bd",
            auth_token="bd_auth_token_placeholder"
        )
        
        super().__init__(
            name="dhaka_pm25_agent",
            tools=[self.air_quality_tool, self.bigquery_tool],
            protocol=self.communication_protocol
        )
        
        self.collection_stats = {
            "total_collections": 0,
            "successful_collections": 0,
            "last_collection": None,
            "average_sensors_per_collection": 0
        }
    
    async def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the sequential workflow for data collection and processing
        """
        self.logger.info("Starting Dhaka PM2.5 collection workflow")
        
        try:
            
            self.logger.info("Step 1: Collecting data from monitoring stations")
            raw_measurements = await self.air_quality_tool.execute()
            
            if not raw_measurements:
                self.logger.warning("No measurements collected")
                return {"status": "no_data", "timestamp": datetime.now().isoformat()}
            
            
            self.logger.info(f"Step 2: Validating {len(raw_measurements)} measurements")
            validation_results = self.validator.validate_batch(raw_measurements)
            
            
            valid_measurements = []
            for measurement in raw_measurements:
                validation = self.validator.validate_measurement(measurement)
                if validation["is_valid"]:
                    measurement["data_quality"] = "valid"
                    measurement["quality_score"] = validation["quality_score"]
                    valid_measurements.append(measurement)
                else:
                    self.logger.warning(f"Rejected measurement from {measurement.get('station_id')}: {validation['errors']}")
            
            # Step 3: Store validated data
            self.logger.info(f"Step 3: Storing {len(valid_measurements)} valid measurements")
            storage_success = await self._store_measurements(valid_measurements)
            
            # Step 4: Share data with India (if cross-border sharing is enabled)
            self.logger.info("Step 4: Sharing aggregated data with India")
            sharing_success = await self._share_cross_border_data(valid_measurements)
            
            # Step 5: Update statistics
            self._update_collection_stats(len(valid_measurements))
            
            # Prepare result summary
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "collection_summary": {
                    "raw_measurements": len(raw_measurements),
                    "valid_measurements": len(valid_measurements),
                    "validation_rate": validation_results["validation_rate"],
                    "average_quality": validation_results["average_quality_score"]
                },
                "storage_success": storage_success,
                "sharing_success": sharing_success,
                "sensor_status": self.air_quality_tool.get_sensor_status()
            }
            
            self.logger.info(f"Workflow completed successfully: {len(valid_measurements)} measurements processed")
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _store_measurements(self, measurements: List[Dict[str, Any]]) -> bool:
        """
        Store measurements in BigQuery
        """
        try:
            # In real implementation, this would use actual BigQuery client
            self.logger.info(f"Storing {len(measurements)} measurements in BigQuery dataset: bangladesh_air_2025")
            await asyncio.sleep(0.2)  # Simulate storage time
            return True
        except Exception as e:
            self.logger.error(f"Failed to store measurements: {e}")
            return False
    
    async def _share_cross_border_data(self, measurements: List[Dict[str, Any]]) -> bool:
        """
        Share aggregated data with India for transboundary analysis
        """
        try:
            # Aggregate data for sharing (don't share individual sensor data)
            if not measurements:
                return True
            
            # Calculate city-wide averages
            pm25_values = [m["pm25"] for m in measurements if m.get("pm25") is not None]
            if not pm25_values:
                return True
            
            aggregated_data = {
                "city": "Dhaka",
                "country": "BD",
                "timestamp": datetime.now().isoformat(),
                "pm25_average": round(sum(pm25_values) / len(pm25_values), 1),
                "pm25_max": round(max(pm25_values), 1),
                "pm25_min": round(min(pm25_values), 1),
                "measurement_count": len(measurements),
                "data_quality": "aggregated"
            }
            
            # Send to India through communication protocol
            success = await self.communication_protocol.send_data(aggregated_data, "IN")
            
            if success:
                self.logger.info("Successfully shared aggregated data with India")
            else:
                self.logger.warning("Failed to share data with India")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sharing cross-border data: {e}")
            return False
    
    def _update_collection_stats(self, measurement_count: int):
        """
        Update collection statistics
        """
        self.collection_stats["total_collections"] += 1
        if measurement_count > 0:
            self.collection_stats["successful_collections"] += 1
        
        self.collection_stats["last_collection"] = datetime.now().isoformat()
        
        # Update rolling average
        total_measurements = (self.collection_stats["average_sensors_per_collection"] * 
                            (self.collection_stats["total_collections"] - 1) + measurement_count)
        self.collection_stats["average_sensors_per_collection"] = (
            total_measurements / self.collection_stats["total_collections"]
        )
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get comprehensive agent status
        """
        return {
            "agent_name": self.name,
            "status": "active",
            "collection_stats": self.collection_stats,
            "sensor_status": self.air_quality_tool.get_sensor_status(),
            "last_updated": datetime.now().isoformat()
        }

# Example usage and testing
async def main():
    """
    Example usage of the Dhaka Agent
    """
    # Initialize and run the agent
    agent = DhakaAgent()
    
    # Run a single collection cycle
    result = await agent.run()
    print("Collection Result:")
    print(json.dumps(result, indent=2))
    
    # Get agent status
    status = agent.get_agent_status()
    print("\nAgent Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
 
    asyncio.run(main())

