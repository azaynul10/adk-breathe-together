"""
Comprehensive test suite for Transnational AQMS
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.dhaka_agent import DhakaAgent, DhakaAirQualityTool, DhakaDataValidator
from agents.kolkata_agent import KolkataAgent, WRFWeatherModel, INSATSatelliteData
from agents.orchestrator import RegionalOrchestrator, DataValidator, EmissionTracker
from schemas.air_quality import AirQualityMeasurement
from communication.protocols import BangladeshIndiaProtocol

class TestDhakaAgent:
    """Test suite for Dhaka Agent"""
    
    @pytest.fixture
    def dhaka_agent(self):
        """Create Dhaka agent instance for testing"""
        return DhakaAgent()
    
    @pytest.fixture
    def air_quality_tool(self):
        """Create air quality tool instance for testing"""
        return DhakaAirQualityTool()
    
    @pytest.fixture
    def data_validator(self):
        """Create data validator instance for testing"""
        return DhakaDataValidator()
    
    @pytest.mark.asyncio
    async def test_dhaka_agent_initialization(self, dhaka_agent):
        """Test Dhaka agent initialization"""
        assert dhaka_agent.name == "dhaka_pm25_agent"
        assert dhaka_agent.air_quality_tool is not None
        assert dhaka_agent.validator is not None
        assert dhaka_agent.collection_stats["total_collections"] == 0
    
    @pytest.mark.asyncio
    async def test_air_quality_data_collection(self, air_quality_tool):
        """Test air quality data collection"""
        measurements = await air_quality_tool.execute()
        
        assert isinstance(measurements, list)
        assert len(measurements) > 0
        
        # Check first measurement structure
        measurement = measurements[0]
        assert "pm25" in measurement
        assert "timestamp" in measurement
        assert "coordinates" in measurement
        assert "country_code" in measurement
        assert measurement["country_code"] == "BD"
        
        # Validate PM2.5 range
        assert 0 <= measurement["pm25"] <= 1000
    
    @pytest.mark.asyncio
    async def test_data_validation(self, data_validator):
        """Test data validation functionality"""
        # Test valid measurement
        valid_measurement = {
            "pm25": 50.0,
            "timestamp": datetime.now().isoformat(),
            "temperature": 25.0,
            "humidity": 70.0
        }
        
        result = data_validator.validate_measurement(valid_measurement)
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
        
        # Test invalid measurement
        invalid_measurement = {
            "pm25": -10.0,  # Invalid negative value
            "timestamp": "invalid_timestamp",
            "temperature": 100.0  # Extreme temperature
        }
        
        result = data_validator.validate_measurement(invalid_measurement)
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_dhaka_agent_workflow(self, dhaka_agent):
        """Test complete Dhaka agent workflow"""
        result = await dhaka_agent.run()
        
        assert "status" in result
        assert "timestamp" in result
        
        if result["status"] == "success":
            assert "collection_summary" in result
            assert "storage_success" in result
            assert "sharing_success" in result
            assert result["collection_summary"]["raw_measurements"] >= 0
            assert result["collection_summary"]["valid_measurements"] >= 0

class TestKolkataAgent:
    """Test suite for Kolkata Agent"""
    
    @pytest.fixture
    def kolkata_agent(self):
        """Create Kolkata agent instance for testing"""
        return KolkataAgent()
    
    @pytest.fixture
    def weather_model(self):
        """Create weather model instance for testing"""
        return WRFWeatherModel()
    
    @pytest.fixture
    def satellite_tool(self):
        """Create satellite tool instance for testing"""
        return INSATSatelliteData()
    
    @pytest.mark.asyncio
    async def test_kolkata_agent_initialization(self, kolkata_agent):
        """Test Kolkata agent initialization"""
        assert kolkata_agent.name == "kolkata_met_agent"
        assert kolkata_agent.weather_model is not None
        assert kolkata_agent.satellite_tool is not None
        assert kolkata_agent.traffic_monitor is not None
    
    @pytest.mark.asyncio
    async def test_weather_data_collection(self, weather_model):
        """Test weather data collection"""
        current_conditions = await weather_model.get_current_conditions()
        
        assert "timestamp" in current_conditions
        assert "temperature_2m" in current_conditions
        assert "wind_speed_10m" in current_conditions
        assert "boundary_layer_height" in current_conditions
        
        # Validate ranges
        assert -10 <= current_conditions["temperature_2m"] <= 50
        assert 0 <= current_conditions["wind_speed_10m"] <= 30
        assert 100 <= current_conditions["boundary_layer_height"] <= 3000
    
    @pytest.mark.asyncio
    async def test_satellite_data_collection(self, satellite_tool):
        """Test satellite data collection"""
        aerosol_data = await satellite_tool.get_aerosol_data()
        
        assert "timestamp" in aerosol_data
        assert "aerosol_optical_depth_550nm" in aerosol_data
        assert "data_quality" in aerosol_data
        
        # Validate AOD range
        aod = aerosol_data["aerosol_optical_depth_550nm"]
        assert 0 <= aod <= 5.0  # Typical AOD range
    
    @pytest.mark.asyncio
    async def test_forecast_generation(self, weather_model):
        """Test weather forecast generation"""
        forecast = await weather_model.get_forecast(24)
        
        assert isinstance(forecast, list)
        assert len(forecast) <= 24
        
        if forecast:
            forecast_point = forecast[0]
            assert "forecast_hour" in forecast_point
            assert forecast_point["forecast_hour"] > 0
    
    @pytest.mark.asyncio
    async def test_kolkata_agent_workflow(self, kolkata_agent):
        """Test complete Kolkata agent workflow"""
        result = await kolkata_agent.run()
        
        assert "status" in result
        assert "timestamp" in result
        
        if result["status"] == "success":
            assert "current_conditions" in result
            assert "transboundary_analysis" in result
            assert "emission_estimates" in result

class TestRegionalOrchestrator:
    """Test suite for Regional Orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        return RegionalOrchestrator()
    
    @pytest.fixture
    def data_validator(self):
        """Create data validator instance for testing"""
        return DataValidator()
    
    @pytest.fixture
    def emission_tracker(self):
        """Create emission tracker instance for testing"""
        return EmissionTracker()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context data for testing"""
        return {
            "dhaka_data": {
                "pm25": 139.0,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 3.5,
                "wind_direction_deg": 270,
                "boundary_layer_height_m": 800,
                "country_code": "BD"
            },
            "kolkata_data": {
                "pm25": 45.6,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 4.2,
                "wind_direction_deg": 90,
                "boundary_layer_height_m": 1200,
                "country_code": "IN"
            }
        }
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.name == "regional_orchestrator"
        assert orchestrator.data_validator is not None
        assert orchestrator.emission_tracker is not None
        assert orchestrator.transboundary_model is not None
        assert orchestrator.policy_engine is not None
    
    @pytest.mark.asyncio
    async def test_data_validation(self, data_validator):
        """Test orchestrator data validation"""
        valid_data = {
            "pm25": 100.0,
            "timestamp": datetime.now().isoformat(),
            "wind_speed_ms": 5.0,
            "country_code": "BD"
        }
        
        result = await data_validator.execute(valid_data)
        assert result["is_valid"] is True
        assert "modified_data" in result
    
    @pytest.mark.asyncio
    async def test_emission_tracking(self, emission_tracker):
        """Test emission source tracking"""
        test_data = {
            "pm25": 100.0,
            "country_code": "BD",
            "wind_direction_deg": 270,
            "wind_speed_ms": 5.0
        }
        
        result = await emission_tracker.execute(test_data)
        assert "local_contribution" in result
        assert "transboundary_contribution" in result
        assert "source_contributions" in result
        assert result["local_contribution"] + result["transboundary_contribution"] == test_data["pm25"]
    
    @pytest.mark.asyncio
    async def test_orchestrator_workflow(self, orchestrator, sample_context):
        """Test complete orchestrator workflow"""
        result = await orchestrator.run(sample_context)
        
        assert "status" in result
        assert "timestamp" in result
        
        if result["status"] == "success":
            assert "cities" in result
            assert "cross_border_coordination" in result
            assert "alerts" in result
            
            # Check city results
            assert "dhaka" in result["cities"]
            assert "kolkata" in result["cities"]
            
            # Validate processing results
            dhaka_result = result["cities"]["dhaka"]
            kolkata_result = result["cities"]["kolkata"]
            
            if dhaka_result.get("status") == "success":
                assert "emission_analysis" in dhaka_result
                assert "policy_recommendations" in dhaka_result
            
            if kolkata_result.get("status") == "success":
                assert "emission_analysis" in kolkata_result
                assert "policy_recommendations" in kolkata_result

class TestCommunicationProtocols:
    """Test suite for communication protocols"""
    
    @pytest.fixture
    def bd_protocol(self):
        """Create Bangladesh protocol instance"""
        return BangladeshIndiaProtocol("BD", "test_endpoint", "test_token")
    
    @pytest.fixture
    def in_protocol(self):
        """Create India protocol instance"""
        return BangladeshIndiaProtocol("IN", "test_endpoint", "test_token")
    
    @pytest.mark.asyncio
    async def test_data_validation(self, bd_protocol):
        """Test protocol data validation"""
        valid_data = {
            "pm25": 50.0,
            "timestamp": datetime.now().isoformat(),
            "coordinates": [90.0, 23.0]
        }
        
        is_valid = await bd_protocol.validate_data(valid_data)
        assert is_valid is True
        
        invalid_data = {
            "pm25": -10.0,  # Invalid value
            "timestamp": "invalid",
            "coordinates": [90.0, 23.0]
        }
        
        is_valid = await bd_protocol.validate_data(invalid_data)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_cross_border_communication(self, bd_protocol):
        """Test cross-border data sharing"""
        test_data = {
            "city": "Dhaka",
            "pm25": 100.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Test sending data
        success = await bd_protocol.send_data(test_data, "IN")
        assert isinstance(success, bool)

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # Initialize components
        dhaka_agent = DhakaAgent()
        kolkata_agent = KolkataAgent()
        orchestrator = RegionalOrchestrator()
        
        # Collect data from both agents
        dhaka_result = await dhaka_agent.run()
        kolkata_result = await kolkata_agent.run()
        
        # Prepare orchestration context
        context = {
            "dhaka_data": {
                "pm25": 139.0,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 3.5,
                "wind_direction_deg": 270,
                "boundary_layer_height_m": 800,
                "country_code": "BD"
            },
            "kolkata_data": {
                "pm25": 45.6,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 4.2,
                "wind_direction_deg": 90,
                "boundary_layer_height_m": 1200,
                "country_code": "IN"
            }
        }
        
        # Run orchestration
        orchestration_result = await orchestrator.run(context)
        
        # Validate results
        assert dhaka_result["status"] in ["success", "error"]
        assert kolkata_result["status"] in ["success", "error"]
        assert orchestration_result["status"] in ["success", "error"]
        
        # If all successful, check data flow
        if all(r["status"] == "success" for r in [dhaka_result, kolkata_result, orchestration_result]):
            assert "cities" in orchestration_result
            assert len(orchestration_result["cities"]) == 2

class TestPerformance:
    """Performance tests for the system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_data_collection(self):
        """Test concurrent data collection performance"""
        dhaka_agent = DhakaAgent()
        
        # Run multiple concurrent collections
        tasks = [dhaka_agent.run() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that all tasks completed
        assert len(results) == 5
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found exceptions: {exceptions}"
    
    @pytest.mark.asyncio
    async def test_orchestrator_performance(self):
        """Test orchestrator performance with multiple requests"""
        orchestrator = RegionalOrchestrator()
        
        context = {
            "dhaka_data": {
                "pm25": 100.0,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 5.0,
                "wind_direction_deg": 270,
                "boundary_layer_height_m": 1000,
                "country_code": "BD"
            },
            "kolkata_data": {
                "pm25": 50.0,
                "timestamp": datetime.now().isoformat(),
                "wind_speed_ms": 4.0,
                "wind_direction_deg": 90,
                "boundary_layer_height_m": 1200,
                "country_code": "IN"
            }
        }
        
        # Measure processing time
        start_time = datetime.now()
        result = await orchestrator.run(context)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Performance assertions
        assert processing_time < 10.0, f"Processing took too long: {processing_time}s"
        assert result["status"] == "success"

# Test configuration
if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

