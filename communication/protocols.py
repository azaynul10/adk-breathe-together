"""
Agent Communication Protocols for Transnational AQMS
A2A (Agent-to-Agent) protocol implementation for cross-border coordination
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import asyncio
import json

class A2AMessage(BaseModel):
    """
    Standard message format for agent-to-agent communication
    """
    
    # Message metadata
    message_id: str
    timestamp: datetime
    protocol_version: str = "A2A/1.0"
    
    # Sender and receiver information
    sender_agent_id: str
    sender_country: str
    receiver_agent_id: str
    receiver_country: str
    
    # Message content
    message_type: str
    payload: Dict[str, Any]
    
    # Security and routing
    authentication_token: str
    encryption_level: str = "TLS1.3"
    priority: int = 1  # 1=low, 2=normal, 3=high, 4=emergency

class DataExchangeProtocol(ABC):
    """
    Abstract base class for data exchange protocols between countries
    """
    
    @abstractmethod
    async def send_data(self, data: Dict[str, Any], target_country: str) -> bool:
        """Send data to target country"""
        pass
    
    @abstractmethod
    async def receive_data(self) -> Optional[Dict[str, Any]]:
        """Receive data from other countries"""
        pass
    
    @abstractmethod
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate received data"""
        pass

class BangladeshIndiaProtocol(DataExchangeProtocol):
    """
    Specific implementation for Bangladesh-India data exchange
    """
    
    def __init__(self, country_code: str, api_endpoint: str, auth_token: str):
        self.country_code = country_code
        self.api_endpoint = api_endpoint
        self.auth_token = auth_token
        self.message_queue = asyncio.Queue()
        
    async def send_data(self, data: Dict[str, Any], target_country: str) -> bool:
        """
        Send air quality data to target country with proper formatting
        """
        try:
            message = A2AMessage(
                message_id=f"{self.country_code}_{datetime.now().isoformat()}",
                timestamp=datetime.now(),
                sender_agent_id=f"{self.country_code}_aqms_agent",
                sender_country=self.country_code,
                receiver_agent_id=f"{target_country}_aqms_agent",
                receiver_country=target_country,
                message_type="air_quality_data",
                payload=data,
                authentication_token=self.auth_token
            )
            
            # Simulate API call to target country
            await self._transmit_message(message)
            return True
            
        except Exception as e:
            print(f"Failed to send data to {target_country}: {e}")
            return False
    
    async def receive_data(self) -> Optional[Dict[str, Any]]:
        """
        Receive and process incoming data from other countries
        """
        try:
            if not self.message_queue.empty():
                message = await self.message_queue.get()
                if await self.validate_data(message.payload):
                    return message.payload
            return None
        except Exception as e:
            print(f"Failed to receive data: {e}")
            return None
    
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate incoming data against schema and business rules
        """
        try:
            # Check required fields
            required_fields = ['pm25', 'timestamp', 'coordinates']
            if not all(field in data for field in required_fields):
                return False
            
            # Validate PM2.5 range
            pm25 = data.get('pm25', 0)
            if not (0 <= pm25 <= 1000):
                return False
            
            # Validate timestamp (within last 24 hours)
            timestamp = datetime.fromisoformat(data['timestamp'])
            time_diff = datetime.now() - timestamp
            if time_diff.total_seconds() > 86400:  # 24 hours
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _transmit_message(self, message: A2AMessage):
        """
        Internal method to transmit message (simulated)
        """
        # In real implementation, this would use HTTP/gRPC/WebSocket
        await asyncio.sleep(0.1)  # Simulate network delay
        print(f"Transmitted message {message.message_id} to {message.receiver_country}")

class PolicyCoordinationProtocol:
    """
    Protocol for coordinating policy actions between countries
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.active_policies = {}
        
    async def propose_joint_action(self, action_type: str, details: Dict[str, Any]) -> str:
        """
        Propose a joint policy action to neighboring countries
        """
        proposal_id = f"policy_{datetime.now().isoformat()}"
        
        proposal = {
            "proposal_id": proposal_id,
            "proposing_country": self.country_code,
            "action_type": action_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "status": "proposed"
        }
        
        # Store proposal
        self.active_policies[proposal_id] = proposal
        
        # Send to neighboring countries (simulated)
        await self._notify_neighbors(proposal)
        
        return proposal_id
    
    async def respond_to_proposal(self, proposal_id: str, response: str, comments: str = "") -> bool:
        """
        Respond to a policy proposal from another country
        """
        if proposal_id not in self.active_policies:
            return False
        
        proposal = self.active_policies[proposal_id]
        proposal["responses"] = proposal.get("responses", {})
        proposal["responses"][self.country_code] = {
            "response": response,  # "accept", "reject", "modify"
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if all countries have responded
        if len(proposal["responses"]) >= 2:  # BD and IN
            await self._finalize_proposal(proposal_id)
        
        return True
    
    async def _notify_neighbors(self, proposal: Dict[str, Any]):
        """
        Notify neighboring countries about policy proposal
        """
        # Simulate notification to neighboring countries
        print(f"Notifying neighbors about proposal: {proposal['action_type']}")
        await asyncio.sleep(0.1)
    
    async def _finalize_proposal(self, proposal_id: str):
        """
        Finalize policy proposal based on responses
        """
        proposal = self.active_policies[proposal_id]
        responses = proposal.get("responses", {})
        
        # Simple majority rule
        accepts = sum(1 for r in responses.values() if r["response"] == "accept")
        if accepts >= len(responses) / 2:
            proposal["status"] = "approved"
            await self._implement_policy(proposal)
        else:
            proposal["status"] = "rejected"
        
        print(f"Proposal {proposal_id} {proposal['status']}")
    
    async def _implement_policy(self, proposal: Dict[str, Any]):
        """
        Implement approved policy action
        """
        print(f"Implementing policy: {proposal['action_type']}")
        # Implementation logic would go here

class AlertDistributionProtocol:
    """
    Protocol for distributing alerts across multiple channels and countries
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.alert_channels = {
            "government": "api.gov.endpoint",
            "public_sms": "sms.gateway.endpoint",
            "digital_billboards": "billboard.api.endpoint",
            "mobile_app": "app.notification.endpoint",
            "social_media": "social.api.endpoint"
        }
    
    async def distribute_alert(self, alert_data: Dict[str, Any], channels: List[str]) -> Dict[str, bool]:
        """
        Distribute alert across specified channels
        """
        results = {}
        
        for channel in channels:
            try:
                success = await self._send_to_channel(channel, alert_data)
                results[channel] = success
            except Exception as e:
                print(f"Failed to send alert to {channel}: {e}")
                results[channel] = False
        
        return results
    
    async def _send_to_channel(self, channel: str, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert to specific channel
        """
        if channel not in self.alert_channels:
            return False
        
        # Format message based on channel
        if channel == "public_sms":
            message = self._format_sms_message(alert_data)
        elif channel == "digital_billboards":
            message = self._format_billboard_message(alert_data)
        else:
            message = alert_data
        
        # Simulate sending (in real implementation, use appropriate APIs)
        await asyncio.sleep(0.1)
        print(f"Sent alert to {channel}: {message}")
        return True
    
    def _format_sms_message(self, alert_data: Dict[str, Any]) -> str:
        """
        Format alert for SMS (160 character limit)
        """
        severity = alert_data.get("severity", "moderate")
        pm25 = alert_data.get("current_pm25", 0)
        
        if self.country_code == "BD":
            return f"বায়ু দূষণ সতর্কতা: PM2.5 {pm25} µg/m³. {severity} স্তর। সাবধানতা অবলম্বন করুন।"
        else:
            return f"वायु प्रदूषण चेतावनी: PM2.5 {pm25} µg/m³. {severity} स्तर। सावधानी बरतें।"
    
    def _format_billboard_message(self, alert_data: Dict[str, Any]) -> str:
        """
        Format alert for digital billboards
        """
        severity = alert_data.get("severity", "moderate")
        pm25 = alert_data.get("current_pm25", 0)
        
        color_code = {
            "low": "GREEN",
            "moderate": "YELLOW", 
            "high": "ORANGE",
            "emergency": "RED"
        }.get(severity, "YELLOW")
        
        return f"AIR QUALITY: {color_code} | PM2.5: {pm25} µg/m³ | {severity.upper()}"

# Protocol factory for easy instantiation
class ProtocolFactory:
    """
    Factory class for creating protocol instances
    """
    
    @staticmethod
    def create_data_exchange_protocol(country_code: str, config: Dict[str, Any]) -> DataExchangeProtocol:
        """
        Create data exchange protocol instance
        """
        return BangladeshIndiaProtocol(
            country_code=country_code,
            api_endpoint=config.get("api_endpoint"),
            auth_token=config.get("auth_token")
        )
    
    @staticmethod
    def create_policy_protocol(country_code: str) -> PolicyCoordinationProtocol:
        """
        Create policy coordination protocol instance
        """
        return PolicyCoordinationProtocol(country_code)
    
    @staticmethod
    def create_alert_protocol(country_code: str) -> AlertDistributionProtocol:
        """
        Create alert distribution protocol instance
        """
        return AlertDistributionProtocol(country_code)

