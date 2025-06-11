"""
Regional Orchestrator Agent
Coordinates data from multiple agents and implements transboundary pollution modeling
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
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

# Import our schemas and protocols
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.air_quality import AirQualityMeasurement, PolicyAction, CrossBorderAlert
from communication.protocols import PolicyCoordinationProtocol, AlertDistributionProtocol

class DataValidator:
    """
    Validates data from multiple sources before processing
    """
    
    def __init__(self, max_pm25: float = 900):
        self.max_pm25 = max_pm25
        self.validation_rules = {
            "pm25_max": max_pm25,
            "pm25_min": 0,
            "wind_speed_max": 30,
            "temperature_max": 50,
            "temperature_min": 0
        }
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming data from multiple sources
        """
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "modified_data": data.copy()
        }
        
        # Validate PM2.5 data
        if "pm25" in data:
            pm25 = data["pm25"]
            if pm25 > self.validation_rules["pm25_max"]:
                validation_results["warnings"].append(f"PM2.5 value {pm25} exceeds maximum threshold")
                validation_results["modified_data"]["pm25"] = self.validation_rules["pm25_max"]
            
            if pm25 < self.validation_rules["pm25_min"]:
                validation_results["errors"].append(f"PM2.5 value {pm25} below minimum threshold")
                validation_results["is_valid"] = False
        
        # Validate meteorological data
        if "wind_speed_ms" in data:
            wind_speed = data["wind_speed_ms"]
            if wind_speed > self.validation_rules["wind_speed_max"]:
                validation_results["warnings"].append(f"Wind speed {wind_speed} exceeds maximum threshold")
                validation_results["modified_data"]["wind_speed_ms"] = self.validation_rules["wind_speed_max"]
        
        # Validate timestamp
        if "timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                time_diff = abs((datetime.now() - timestamp.replace(tzinfo=None)).total_seconds())
                if time_diff > 86400:  # More than 24 hours old
                    validation_results["warnings"].append(f"Data timestamp is {time_diff/3600:.1f} hours old")
            except Exception as e:
                validation_results["errors"].append(f"Invalid timestamp format: {e}")
                validation_results["is_valid"] = False
        
        return validation_results

class EmissionTracker:
    """
    Tracks emission sources and performs source apportionment
    """
    
    def __init__(self, source_apportionment: str = "PMF 4.0"):
        self.model_name = source_apportionment
        self.emission_sources = {
            "BD": {
                "brick_kilns": 0.35,  # Fraction of total emissions
                "vehicles": 0.25,
                "industries": 0.20,
                "construction": 0.10,
                "waste_burning": 0.05,
                "others": 0.05
            },
            "IN": {
                "vehicles": 0.40,
                "industries": 0.25,
                "construction": 0.15,
                "waste_burning": 0.10,
                "brick_kilns": 0.05,
                "others": 0.05
            }
        }
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform source apportionment analysis
        """
        # Extract relevant data
        country = data.get("country_code", "BD")
        pm25 = data.get("pm25", 0)
        
        # Get emission source breakdown for the country
        sources = self.emission_sources.get(country, self.emission_sources["BD"])
        
        # Calculate source contributions
        source_contributions = {}
        for source, fraction in sources.items():
            source_contributions[source] = round(pm25 * fraction, 1)
        
        # Calculate transboundary contribution (simplified model)
        # This would be more complex in a real implementation
        wind_direction = data.get("wind_direction_deg", 0)
        wind_speed = data.get("wind_speed_ms", 0)
        
        # For Dhaka: wind from India (west) increases transboundary contribution
        # For Kolkata: wind from Bangladesh (east) increases transboundary contribution
        transboundary_factor = 0.0
        
        if country == "BD":  # Bangladesh
            # Wind from west (225-315 degrees) brings pollution from India
            if 225 <= wind_direction <= 315:
                transboundary_factor = min(1.0, wind_speed / 10.0) * 0.6
            else:
                transboundary_factor = 0.2  # Baseline transboundary contribution
        else:  # India
            # Wind from east (45-135 degrees) brings pollution from Bangladesh
            if 45 <= wind_direction <= 135:
                transboundary_factor = min(1.0, wind_speed / 10.0) * 0.4
            else:
                transboundary_factor = 0.1  # Baseline transboundary contribution
        
        # Calculate local vs transboundary contributions
        local_contribution = round(pm25 * (1 - transboundary_factor), 1)
        transboundary_contribution = round(pm25 * transboundary_factor, 1)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "country": country,
            "pm25_total": pm25,
            "local_contribution": local_contribution,
            "local_percentage": round((1 - transboundary_factor) * 100, 1),
            "transboundary_contribution": transboundary_contribution,
            "transboundary_percentage": round(transboundary_factor * 100, 1),
            "source_contributions": source_contributions,
            "model": self.model_name,
            "confidence_level": "medium"  # In real implementation, this would be calculated
        }

class TransboundaryModel:
    """
    Models transboundary pollution transport between countries
    """
    
    def __init__(self, equation: str = "PM2.5 = α·Local + β·Transboundary + ε"):
        self.model_equation = equation
        self.model_coefficients = {
            "BD": {"alpha": 0.38, "beta": 0.62, "epsilon": 5.0},  # Dhaka coefficients
            "IN": {"alpha": 0.55, "beta": 0.45, "epsilon": 3.0}   # Kolkata coefficients
        }
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute transboundary pollution modeling
        """
        # Extract meteorological data
        wind_speed = data.get("wind_speed_ms", 0)
        wind_direction = data.get("wind_direction_deg", 0)
        boundary_layer_height = data.get("boundary_layer_height_m", 1000)
        country = data.get("country_code", "BD")
        
        # Get model coefficients for the country
        coef = self.model_coefficients.get(country, self.model_coefficients["BD"])
        
        # Calculate transport efficiency based on meteorological conditions
        transport_efficiency = self._calculate_transport_efficiency(
            wind_speed, wind_direction, boundary_layer_height, country
        )
        
        # Adjust coefficients based on transport efficiency
        adjusted_alpha = coef["alpha"] * (1 - transport_efficiency)
        adjusted_beta = coef["beta"] * transport_efficiency
        
        # Normalize coefficients to sum to 1
        total = adjusted_alpha + adjusted_beta
        if total > 0:
            adjusted_alpha /= total
            adjusted_beta /= total
        
        # Calculate transport time to border
        transport_time = self._calculate_transport_time(wind_speed, country)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "country": country,
            "model_equation": self.model_equation,
            "base_coefficients": {
                "local": coef["alpha"],
                "transboundary": coef["beta"]
            },
            "adjusted_coefficients": {
                "local": round(adjusted_alpha, 2),
                "transboundary": round(adjusted_beta, 2)
            },
            "transport_efficiency": round(transport_efficiency, 2),
            "transport_time_hours": round(transport_time, 1) if transport_time != float('inf') else None,
            "meteorological_factors": {
                "wind_speed_ms": wind_speed,
                "wind_direction_deg": wind_direction,
                "boundary_layer_height_m": boundary_layer_height
            }
        }
    
    def _calculate_transport_efficiency(self, wind_speed: float, wind_direction: float, 
                                       boundary_layer_height: float, country: str) -> float:
        """
        Calculate pollution transport efficiency between countries
        """
        # Base efficiency depends on wind speed
        if wind_speed < 1:
            base_efficiency = 0.1  # Very low transport
        elif wind_speed < 3:
            base_efficiency = 0.3  # Low transport
        elif wind_speed < 6:
            base_efficiency = 0.6  # Moderate transport
        else:
            base_efficiency = 0.8  # High transport
        
        # Direction factor depends on country and wind direction
        direction_factor = 0.5  # Default neutral factor
        
        if country == "BD":  # Bangladesh
            # Wind from west (225-315 degrees) brings pollution from India
            if 225 <= wind_direction <= 315:
                direction_factor = 1.0
            # Wind from east (45-135 degrees) carries pollution away
            elif 45 <= wind_direction <= 135:
                direction_factor = 0.2
        else:  # India
            # Wind from east (45-135 degrees) brings pollution from Bangladesh
            if 45 <= wind_direction <= 135:
                direction_factor = 1.0
            # Wind from west (225-315 degrees) carries pollution away
            elif 225 <= wind_direction <= 315:
                direction_factor = 0.2
        
        # Boundary layer factor - higher boundary layer means better dispersion
        if boundary_layer_height < 500:
            bl_factor = 1.2  # Poor dispersion, increased transport
        elif boundary_layer_height < 1000:
            bl_factor = 1.0  # Neutral
        else:
            bl_factor = 0.8  # Good dispersion, decreased transport
        
        # Calculate final efficiency
        efficiency = base_efficiency * direction_factor * bl_factor
        
        # Clamp to valid range
        return max(0.1, min(efficiency, 0.9))
    
    def _calculate_transport_time(self, wind_speed: float, country: str) -> float:
        """
        Calculate approximate transport time to border
        """
        if wind_speed < 0.5:
            return float('inf')  # Effectively no transport
        
        # Approximate distances to border
        distances = {
            "BD": 50,  # Dhaka to India border (km)
            "IN": 80   # Kolkata to Bangladesh border (km)
        }
        
        distance = distances.get(country, 50)
        
        # Convert wind speed from m/s to km/h
        speed_kmh = wind_speed * 3.6
        
        # Calculate time in hours
        return distance / speed_kmh

class PolicyDecisionEngine:
    """
    Generates policy recommendations based on air quality and meteorological data
    """
    
    def __init__(self):
        self.decision_thresholds = {
            "BD": {  # Bangladesh thresholds
                "emergency": 200,
                "severe": 150,
                "poor": 100,
                "moderate": 50
            },
            "IN": {  # India thresholds
                "emergency": 180,
                "severe": 120,
                "poor": 90,
                "moderate": 50
            }
        }
        
        self.policy_actions = {
            "BD": {
                "emergency": ["brick_kiln_shutdown", "odd_even_vehicles", "school_closure"],
                "severe": ["brick_kiln_shutdown", "construction_halt"],
                "poor": ["construction_halt", "street_watering"],
                "moderate": ["street_watering", "public_advisory"]
            },
            "IN": {
                "emergency": ["odd_even_vehicles", "school_closure", "industrial_audit"],
                "severe": ["school_closure", "industrial_audit"],
                "poor": ["industrial_audit", "street_watering"],
                "moderate": ["street_watering", "public_advisory"]
            }
        }
    
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate policy recommendations based on air quality data
        """
        # Extract relevant data
        pm25 = data.get("pm25", 0)
        country = data.get("country_code", "BD")
        transboundary_percent = data.get("transboundary_percentage", 0)
        
        # Determine air quality category
        thresholds = self.decision_thresholds.get(country, self.decision_thresholds["BD"])
        
        if pm25 >= thresholds["emergency"]:
            category = "emergency"
        elif pm25 >= thresholds["severe"]:
            category = "severe"
        elif pm25 >= thresholds["poor"]:
            category = "poor"
        elif pm25 >= thresholds["moderate"]:
            category = "moderate"
        else:
            category = "good"
        
        # Get recommended actions for the category
        actions = self.policy_actions.get(country, {}).get(category, [])
        
        # Determine if cross-border coordination is needed
        needs_coordination = transboundary_percent > 30 and category in ["emergency", "severe"]
        
        # Generate policy decision
        policy_decision = {
            "timestamp": datetime.now().isoformat(),
            "country": country,
            "pm25_level": pm25,
            "air_quality_category": category,
            "recommended_actions": actions,
            "transboundary_contribution_percent": transboundary_percent,
            "cross_border_coordination_needed": needs_coordination,
            "implementation_priority": "high" if category in ["emergency", "severe"] else "normal",
            "expected_impact": "significant" if category in ["emergency", "severe"] else "moderate"
        }
        
        return policy_decision

class RegionalOrchestrator(ParallelAgent):
    """
    Main orchestrator agent for transboundary air quality management
    """
    
    def __init__(self):
        # Initialize sub-agents
        self.data_validator = DataValidator(max_pm25=900)
        self.emission_tracker = EmissionTracker(source_apportionment="PMF 4.0")
        self.transboundary_model = TransboundaryModel()
        self.policy_engine = PolicyDecisionEngine()
        
        # Initialize protocols
        self.policy_protocol_bd = PolicyCoordinationProtocol("BD")
        self.policy_protocol_in = PolicyCoordinationProtocol("IN")
        self.alert_protocol_bd = AlertDistributionProtocol("BD")
        self.alert_protocol_in = AlertDistributionProtocol("IN")
        
        super().__init__(
            name="regional_orchestrator",
            sub_agents=[
                self.data_validator,
                self.emission_tracker,
                self.transboundary_model,
                self.policy_engine
            ]
        )
        
        self.orchestration_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "last_run": None,
            "average_processing_time": 0,
            "alerts_generated": 0,
            "policies_coordinated": 0
        }
    
    async def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the orchestration workflow
        """
        start_time = datetime.now()
        self.logger.info("Starting regional orchestration workflow")
        
        try:
            # Extract data from context
            if not context or not isinstance(context, dict):
                self.logger.error("Invalid or missing context data")
                return {
                    "status": "error",
                    "error": "Invalid or missing context data",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Extract air quality and meteorological data
            dhaka_data = context.get("dhaka_data", {})
            kolkata_data = context.get("kolkata_data", {})
            
            # Process data for both cities in parallel
            dhaka_results = await self._process_city_data(dhaka_data, "BD")
            kolkata_results = await self._process_city_data(kolkata_data, "IN")
            
            # Generate cross-border coordination if needed
            coordination_results = await self._coordinate_cross_border_actions(dhaka_results, kolkata_results)
            
            # Generate alerts if needed
            alert_results = await self._generate_alerts(dhaka_results, kolkata_results)
            
            # Update orchestration statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_orchestration_stats(processing_time, 
                                           alerts_generated=len(alert_results.get("alerts", [])),
                                           policies_coordinated=len(coordination_results.get("coordinated_actions", [])))
            
            # Prepare comprehensive result
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": round(processing_time, 2),
                "cities": {
                    "dhaka": dhaka_results,
                    "kolkata": kolkata_results
                },
                "cross_border_coordination": coordination_results,
                "alerts": alert_results,
                "orchestration_stats": self.orchestration_stats
            }
            
            self.logger.info(f"Orchestration workflow completed successfully in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Orchestration workflow failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def _process_city_data(self, city_data: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """
        Process data for a single city
        """
        if not city_data:
            return {"status": "no_data", "country_code": country_code}
        
        try:
            # Add country code if not present
            if "country_code" not in city_data:
                city_data["country_code"] = country_code
            
            # Step 1: Validate data
            validation_result = await self.data_validator.execute(city_data)
            
            if not validation_result["is_valid"]:
                return {
                    "status": "validation_failed",
                    "errors": validation_result["errors"],
                    "country_code": country_code
                }
            
            # Use validated data for further processing
            validated_data = validation_result["modified_data"]
            
            # Step 2: Track emissions
            emission_result = await self.emission_tracker.execute(validated_data)
            
            # Step 3: Model transboundary pollution
            model_result = await self.transboundary_model.execute(validated_data)
            
            # Step 4: Generate policy recommendations
            # Combine emission and model results for policy decisions
            policy_input = {
                **validated_data,
                "transboundary_percentage": model_result["adjusted_coefficients"]["transboundary"] * 100
            }
            policy_result = await self.policy_engine.execute(policy_input)
            
            return {
                "status": "success",
                "country_code": country_code,
                "pm25": validated_data.get("pm25", 0),
                "timestamp": validated_data.get("timestamp", datetime.now().isoformat()),
                "emission_analysis": emission_result,
                "transboundary_model": model_result,
                "policy_recommendations": policy_result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing data for {country_code}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "country_code": country_code
            }
    
    async def _coordinate_cross_border_actions(self, dhaka_results: Dict[str, Any], 
                                             kolkata_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate cross-border policy actions
        """
        coordinated_actions = []
        
        # Check if cross-border coordination is needed
        dhaka_needs_coordination = (dhaka_results.get("status") == "success" and
                                  dhaka_results.get("policy_recommendations", {}).get("cross_border_coordination_needed", False))
        
        kolkata_needs_coordination = (kolkata_results.get("status") == "success" and
                                    kolkata_results.get("policy_recommendations", {}).get("cross_border_coordination_needed", False))
        
        if not (dhaka_needs_coordination or kolkata_needs_coordination):
            return {"status": "not_needed", "coordinated_actions": []}
        
        try:
            # Generate joint policy proposal
            if dhaka_needs_coordination and kolkata_needs_coordination:
                # Both cities need coordination - create joint action
                joint_action = {
                    "action_type": "bilateral_emergency_response",
                    "details": {
                        "dhaka_pm25": dhaka_results.get("pm25", 0),
                        "kolkata_pm25": kolkata_results.get("pm25", 0),
                        "dhaka_actions": dhaka_results.get("policy_recommendations", {}).get("recommended_actions", []),
                        "kolkata_actions": kolkata_results.get("policy_recommendations", {}).get("recommended_actions", []),
                        "implementation_time": datetime.now().isoformat(),
                        "duration_hours": 48
                    }
                }
                
                # Propose joint action from Bangladesh
                proposal_id = await self.policy_protocol_bd.propose_joint_action(
                    joint_action["action_type"], joint_action["details"]
                )
                
                # Simulate India's response
                await self.policy_protocol_in.respond_to_proposal(proposal_id, "accept")
                
                coordinated_actions.append({
                    "proposal_id": proposal_id,
                    "action_type": joint_action["action_type"],
                    "status": "approved",
                    "participating_countries": ["BD", "IN"]
                })
                
            elif dhaka_needs_coordination:
                # Only Dhaka needs coordination - notify India
                notification_action = {
                    "action_type": "transboundary_notification",
                    "details": {
                        "source_country": "BD",
                        "pm25_level": dhaka_results.get("pm25", 0),
                        "transboundary_contribution": dhaka_results.get("transboundary_model", {})
                                                    .get("adjusted_coefficients", {}).get("transboundary", 0) * 100,
                        "requested_actions": ["industrial_emission_reduction"],
                        "duration_hours": 24
                    }
                }
                
                proposal_id = await self.policy_protocol_bd.propose_joint_action(
                    notification_action["action_type"], notification_action["details"]
                )
                
                coordinated_actions.append({
                    "proposal_id": proposal_id,
                    "action_type": notification_action["action_type"],
                    "status": "proposed",
                    "participating_countries": ["BD", "IN"]
                })
                
            elif kolkata_needs_coordination:
                # Only Kolkata needs coordination - notify Bangladesh
                notification_action = {
                    "action_type": "transboundary_notification",
                    "details": {
                        "source_country": "IN",
                        "pm25_level": kolkata_results.get("pm25", 0),
                        "transboundary_contribution": kolkata_results.get("transboundary_model", {})
                                                    .get("adjusted_coefficients", {}).get("transboundary", 0) * 100,
                        "requested_actions": ["brick_kiln_emission_reduction"],
                        "duration_hours": 24
                    }
                }
                
                proposal_id = await self.policy_protocol_in.propose_joint_action(
                    notification_action["action_type"], notification_action["details"]
                )
                
                coordinated_actions.append({
                    "proposal_id": proposal_id,
                    "action_type": notification_action["action_type"],
                    "status": "proposed",
                    "participating_countries": ["IN", "BD"]
                })
            
            return {
                "status": "success",
                "coordinated_actions": coordinated_actions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error coordinating cross-border actions: {e}")
            return {
                "status": "error",
                "error": str(e),
                "coordinated_actions": []
            }
    
    async def _generate_alerts(self, dhaka_results: Dict[str, Any], kolkata_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate alerts based on air quality and transboundary analysis
        """
        alerts = []
        
        try:
            # Check Dhaka air quality for alerts
            if dhaka_results.get("status") == "success":
                dhaka_pm25 = dhaka_results.get("pm25", 0)
                dhaka_category = dhaka_results.get("policy_recommendations", {}).get("air_quality_category", "")
                
                if dhaka_category in ["emergency", "severe"]:
                    # Generate alert for Dhaka
                    dhaka_alert = self._create_alert(
                        "BD", dhaka_pm25, dhaka_category,
                        dhaka_results.get("transboundary_model", {}).get("adjusted_coefficients", {}).get("transboundary", 0) * 100,
                        dhaka_results.get("policy_recommendations", {}).get("recommended_actions", [])
                    )
                    
                    # Distribute alert
                    channels = ["government", "public_sms", "digital_billboards", "mobile_app"]
                    distribution_result = await self.alert_protocol_bd.distribute_alert(dhaka_alert, channels)
                    
                    alerts.append({
                        "alert": dhaka_alert,
                        "distribution": distribution_result
                    })
            
            # Check Kolkata air quality for alerts
            if kolkata_results.get("status") == "success":
                kolkata_pm25 = kolkata_results.get("pm25", 0)
                kolkata_category = kolkata_results.get("policy_recommendations", {}).get("air_quality_category", "")
                
                if kolkata_category in ["emergency", "severe"]:
                    # Generate alert for Kolkata
                    kolkata_alert = self._create_alert(
                        "IN", kolkata_pm25, kolkata_category,
                        kolkata_results.get("transboundary_model", {}).get("adjusted_coefficients", {}).get("transboundary", 0) * 100,
                        kolkata_results.get("policy_recommendations", {}).get("recommended_actions", [])
                    )
                    
                    # Distribute alert
                    channels = ["government", "public_sms", "digital_billboards", "mobile_app"]
                    distribution_result = await self.alert_protocol_in.distribute_alert(kolkata_alert, channels)
                    
                    alerts.append({
                        "alert": kolkata_alert,
                        "distribution": distribution_result
                    })
            
            # Check for transboundary alert
            if (dhaka_results.get("status") == "success" and kolkata_results.get("status") == "success"):
                dhaka_transboundary = dhaka_results.get("transboundary_model", {}).get("adjusted_coefficients", {}).get("transboundary", 0)
                kolkata_transboundary = kolkata_results.get("transboundary_model", {}).get("adjusted_coefficients", {}).get("transboundary", 0)
                
                if dhaka_transboundary > 0.5 or kolkata_transboundary > 0.4:
                    # Generate transboundary alert
                    transboundary_alert = {
                        "alert_id": f"TB_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "alert_type": "transboundary_transport",
                        "severity": "high",
                        "affected_countries": ["BD", "IN"],
                        "timestamp": datetime.now().isoformat(),
                        "message": "Significant transboundary pollution detected between Bangladesh and India",
                        "details": {
                            "dhaka_pm25": dhaka_results.get("pm25", 0),
                            "kolkata_pm25": kolkata_results.get("pm25", 0),
                            "dhaka_transboundary_percent": round(dhaka_transboundary * 100, 1),
                            "kolkata_transboundary_percent": round(kolkata_transboundary * 100, 1)
                        }
                    }
                    
                    # Distribute to both countries
                    await self.alert_protocol_bd.distribute_alert(transboundary_alert, ["government"])
                    await self.alert_protocol_in.distribute_alert(transboundary_alert, ["government"])
                    
                    alerts.append({
                        "alert": transboundary_alert,
                        "type": "transboundary"
                    })
            
            return {
                "status": "success",
                "alerts": alerts,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")
            return {
                "status": "error",
                "error": str(e),
                "alerts": []
            }
    
    def _create_alert(self, country: str, pm25: float, category: str, 
                     transboundary_percent: float, recommended_actions: List[str]) -> Dict[str, Any]:
        """
        Create alert message in appropriate format and languages
        """
        city = "Dhaka" if country == "BD" else "Kolkata"
        
        # Map category to severity
        severity_map = {
            "emergency": "emergency",
            "severe": "high",
            "poor": "moderate",
            "moderate": "low",
            "good": "low"
        }
        
        severity = severity_map.get(category, "moderate")
        
        # Create alert in English
        message_english = f"Air Quality Alert: {city} is experiencing {category} air pollution levels. Current PM2.5: {pm25} µg/m³. "
        if recommended_actions:
            message_english += f"Recommended actions: {', '.join(recommended_actions)}."
        
        # Create alert in Bengali (simplified translation)
        message_bengali = f"বায়ু দূষণ সতর্কতা: {city} শহরে {category} মাত্রার বায়ু দূষণ। বর্তমান PM2.5: {pm25} µg/m³।"
        
        # Create alert in Hindi (simplified translation)
        message_hindi = f"वायु प्रदूषण चेतावनी: {city} में {category} स्तर का वायु प्रदूषण। वर्तमान PM2.5: {pm25} µg/m³।"
        
        return {
            "alert_id": f"{country}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "alert_type": "pollution_spike",
            "origin_country": country,
            "affected_countries": [country],
            "affected_cities": [city],
            "current_pm25": pm25,
            "forecast_pm25": [pm25 * 0.9, pm25 * 0.85, pm25 * 0.8],  # Simplified 24-hour forecast
            "transboundary_contribution": transboundary_percent,
            "recommended_actions": recommended_actions,
            "coordination_required": transboundary_percent > 30,
            "message_bengali": message_bengali,
            "message_hindi": message_hindi,
            "message_english": message_english
        }
    
    def _update_orchestration_stats(self, processing_time: float, alerts_generated: int = 0, 
                                  policies_coordinated: int = 0):
        """
        Update orchestration statistics
        """
        self.orchestration_stats["total_runs"] += 1
        self.orchestration_stats["successful_runs"] += 1
        self.orchestration_stats["last_run"] = datetime.now().isoformat()
        self.orchestration_stats["alerts_generated"] += alerts_generated
        self.orchestration_stats["policies_coordinated"] += policies_coordinated
        
        # Update rolling average processing time
        total_time = (self.orchestration_stats["average_processing_time"] * 
                     (self.orchestration_stats["total_runs"] - 1) + processing_time)
        self.orchestration_stats["average_processing_time"] = total_time / self.orchestration_stats["total_runs"]
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get comprehensive orchestrator status
        """
        return {
            "orchestrator_name": self.name,
            "status": "active",
            "orchestration_stats": self.orchestration_stats,
            "last_updated": datetime.now().isoformat()
        }

# Example usage and testing
async def main():
    """
    Example usage of the Regional Orchestrator
    """
    # Initialize the orchestrator
    orchestrator = RegionalOrchestrator()
    
    # Create sample data
    context = {
        "dhaka_data": {
            "pm25": 139.0,
            "timestamp": datetime.now().isoformat(),
            "wind_speed_ms": 3.5,
            "wind_direction_deg": 270,  # Wind from the west
            "boundary_layer_height_m": 800,
            "country_code": "BD"
        },
        "kolkata_data": {
            "pm25": 45.6,
            "timestamp": datetime.now().isoformat(),
            "wind_speed_ms": 4.2,
            "wind_direction_deg": 90,  # Wind from the east
            "boundary_layer_height_m": 1200,
            "country_code": "IN"
        }
    }
    
    # Run the orchestrator
    result = await orchestrator.run(context)
    print("Orchestration Result:")
    print(json.dumps(result, indent=2))
    
    # Get orchestrator status
    status = orchestrator.get_orchestrator_status()
    print("\nOrchestrator Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the example
    asyncio.run(main())

