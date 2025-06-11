import asyncio
from agents.dhaka_agent import DhakaAgent
from agents.kolkata_agent import KolkataAgent
from agents.orchestrator import RegionalOrchestrator

async def test():
    print('Testing agents...')
    dhaka = DhakaAgent()
    kolkata = KolkataAgent()
    orchestrator = RegionalOrchestrator()
    print('✅ All agents initialized successfully!')

asyncio.run(test())