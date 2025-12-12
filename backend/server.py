from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio
import random
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="AEGIS MIND - Electronic Warfare Decision Support System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ MODELS ============

class Emitter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    emitter_type: str  # radar, communication, jammer, iff
    platform: str  # aircraft, ship, ground, satellite
    origin: str  # country/faction
    threat_level: str  # critical, high, medium, low
    frequency_min: float  # MHz
    frequency_max: float  # MHz
    prf: Optional[float] = None  # Pulse Repetition Frequency
    pulse_width: Optional[float] = None  # microseconds
    modulation_type: Optional[str] = None  # CW, pulse, FM, chirp, FHSS
    latitude: float
    longitude: float
    altitude: Optional[float] = 0
    confidence: float = 0.85
    is_active: bool = True
    affiliation: str = "hostile"  # hostile, friendly, neutral, unknown
    last_detected: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EmitterCreate(BaseModel):
    name: str
    emitter_type: str
    platform: str
    origin: str
    threat_level: str
    frequency_min: float
    frequency_max: float
    prf: Optional[float] = None
    pulse_width: Optional[float] = None
    modulation_type: Optional[str] = None
    latitude: float
    longitude: float
    altitude: Optional[float] = 0
    confidence: float = 0.85
    affiliation: str = "hostile"

class Countermeasure(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    technique_type: str  # jamming, deception, chaff, flare, cyber
    description: str
    success_rate: float
    resource_cost: str  # low, medium, high
    applicable_threats: List[str]
    side_effects: Optional[str] = None

class ThreatAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emitter_id: str
    threat_score: float
    kill_chain_phase: str  # detection, tracking, engagement, intercept
    time_to_impact: Optional[float] = None
    recommended_actions: List[str]
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Scenario(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    region: str
    center_lat: float
    center_lng: float
    zoom: int
    emitters: List[Dict[str, Any]]
    threat_summary: str

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None

# ============ SAMPLE DATA ============

SAMPLE_EMITTERS = [
    # Taiwan Strait Scenario
    {
        "name": "Type 346B - PLAN Destroyer",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 3100,
        "frequency_max": 3500,
        "prf": 3000,
        "pulse_width": 1.5,
        "modulation_type": "pulse",
        "latitude": 25.2,
        "longitude": 120.5,
        "affiliation": "hostile"
    },
    {
        "name": "YLC-8B Early Warning",
        "emitter_type": "radar",
        "platform": "ground",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 1200,
        "frequency_max": 1400,
        "prf": 500,
        "pulse_width": 50,
        "modulation_type": "pulse",
        "latitude": 25.8,
        "longitude": 119.2,
        "affiliation": "hostile"
    },
    {
        "name": "DF-21D Missile Seeker",
        "emitter_type": "radar",
        "platform": "missile",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 9000,
        "frequency_max": 10000,
        "prf": 10000,
        "pulse_width": 0.5,
        "modulation_type": "chirp",
        "latitude": 25.5,
        "longitude": 120.8,
        "affiliation": "hostile"
    },
    {
        "name": "USS Gerald Ford - SPY-6",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "USA",
        "threat_level": "low",
        "frequency_min": 2900,
        "frequency_max": 3100,
        "prf": 4000,
        "pulse_width": 1.0,
        "modulation_type": "pulse",
        "latitude": 24.8,
        "longitude": 121.2,
        "affiliation": "friendly"
    },
    {
        "name": "E-2D Hawkeye AEW",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "USA",
        "threat_level": "low",
        "frequency_min": 400,
        "frequency_max": 450,
        "prf": 300,
        "pulse_width": 10,
        "modulation_type": "pulse",
        "latitude": 24.5,
        "longitude": 122.0,
        "affiliation": "friendly"
    },
    # Ukraine Scenario
    {
        "name": "DJI Mavic Control Link",
        "emitter_type": "communication",
        "platform": "uav",
        "origin": "Unknown",
        "threat_level": "medium",
        "frequency_min": 2400,
        "frequency_max": 2483,
        "modulation_type": "FHSS",
        "latitude": 50.45,
        "longitude": 30.52,
        "affiliation": "hostile"
    },
    {
        "name": "Orlan-10 Datalink",
        "emitter_type": "communication",
        "platform": "uav",
        "origin": "Russia",
        "threat_level": "high",
        "frequency_min": 868,
        "frequency_max": 915,
        "modulation_type": "FM",
        "latitude": 50.48,
        "longitude": 30.55,
        "affiliation": "hostile"
    },
    {
        "name": "S-400 Engagement Radar",
        "emitter_type": "radar",
        "platform": "ground",
        "origin": "Russia",
        "threat_level": "critical",
        "frequency_min": 2000,
        "frequency_max": 4000,
        "prf": 8000,
        "pulse_width": 0.2,
        "modulation_type": "pulse",
        "latitude": 50.6,
        "longitude": 30.3,
        "affiliation": "hostile"
    }
]

SAMPLE_COUNTERMEASURES = [
    {
        "name": "AN/SLQ-32 Mode 4",
        "technique_type": "jamming",
        "description": "Active electronic countermeasure providing noise jamming against fire control radars",
        "success_rate": 0.78,
        "resource_cost": "medium",
        "applicable_threats": ["radar", "missile_seeker"],
        "side_effects": "May reveal own position"
    },
    {
        "name": "Nulka Decoy",
        "technique_type": "deception",
        "description": "Hovering rocket-propelled decoy that provides radar false target",
        "success_rate": 0.85,
        "resource_cost": "high",
        "applicable_threats": ["anti_ship_missile", "radar"],
        "side_effects": "Limited inventory, single use"
    },
    {
        "name": "Mk 36 SRBOC Chaff",
        "technique_type": "chaff",
        "description": "Rapid-blooming chaff providing radar obscuration",
        "success_rate": 0.65,
        "resource_cost": "low",
        "applicable_threats": ["radar", "missile_seeker"],
        "side_effects": "Wind dependent effectiveness"
    },
    {
        "name": "GPS Spoofing Array",
        "technique_type": "cyber",
        "description": "Broadcasts false GPS signals to misdirect GPS-guided threats",
        "success_rate": 0.72,
        "resource_cost": "medium",
        "applicable_threats": ["uav", "cruise_missile"],
        "side_effects": "Affects friendly GPS receivers in area"
    },
    {
        "name": "Adaptive Frequency Jammer",
        "technique_type": "jamming",
        "description": "AI-driven jammer that adapts to target frequency hopping patterns",
        "success_rate": 0.82,
        "resource_cost": "high",
        "applicable_threats": ["communication", "uav_datalink"],
        "side_effects": "Significant power consumption"
    }
]

SCENARIOS = [
    {
        "id": "scenario_1",
        "name": "Carrier Strike Group Defense",
        "description": "USS Gerald Ford transiting Taiwan Strait under threat from PLAN naval forces and coastal defense systems",
        "region": "Taiwan Strait",
        "center_lat": 25.0,
        "center_lng": 121.0,
        "zoom": 7,
        "emitters": ["Type 346B - PLAN Destroyer", "YLC-8B Early Warning", "DF-21D Missile Seeker", "USS Gerald Ford - SPY-6", "E-2D Hawkeye AEW"],
        "threat_summary": "Multiple surface and air defense radars tracking friendly forces. Anti-ship ballistic missile threat detected."
    },
    {
        "id": "scenario_2", 
        "name": "Urban EW - Drone Defense",
        "description": "Urban defense against commercial drone swarm modified for ISR and attack operations",
        "region": "Kyiv, Ukraine",
        "center_lat": 50.45,
        "center_lng": 30.52,
        "zoom": 10,
        "emitters": ["DJI Mavic Control Link", "Orlan-10 Datalink", "S-400 Engagement Radar"],
        "threat_summary": "50+ drones detected. Mix of commercial and military UAVs. Long-range SAM threat from north."
    },
    {
        "id": "scenario_3",
        "name": "Spectrum Management - Contested",
        "description": "Multi-domain operations with congested spectrum requiring dynamic frequency management",
        "region": "Baltic Sea",
        "center_lat": 57.0,
        "center_lng": 20.0,
        "zoom": 6,
        "emitters": [],
        "threat_summary": "Heavy electromagnetic congestion. Multiple friendly and hostile emitters competing for spectrum access."
    }
]

# ============ AI INTEGRATION ============

async def get_ai_response(query: str, context: Dict[str, Any] = None) -> str:
    """Get AI response using Gemini 2.5 Flash via emergentintegrations"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return "AI system offline - API key not configured"
        
        system_message = """You are AEGIS MIND, an advanced Electronic Warfare AI assistant for military decision support.
You have access to real-time EW data and can provide:
- Threat analysis and identification
- Countermeasure recommendations  
- Tactical assessments
- Signal classification insights
- Kill chain analysis

Respond in a concise, military-professional manner. Use technical terminology appropriately.
When discussing threats, provide confidence levels and recommended actions.
Format responses for quick comprehension in high-stress tactical environments."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"aegis-{uuid.uuid4()}",
            system_message=system_message
        ).with_model("gemini", "gemini-2.5-flash")
        
        # Add context to query if available
        enhanced_query = query
        if context:
            enhanced_query = f"Context: {context}\n\nQuery: {query}"
        
        user_message = UserMessage(text=enhanced_query)
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        logging.error(f"AI Error: {str(e)}")
        return f"AI analysis unavailable: {str(e)}"

# ============ SIMULATION ENGINE ============

class BattlefieldSimulator:
    def __init__(self):
        self.active_emitters = []
        self.time_offset = 0
    
    def generate_signal_update(self, emitter: Dict) -> Dict:
        """Generate realistic signal parameter variations"""
        variation = random.uniform(-0.02, 0.02)
        return {
            "emitter_id": emitter.get("id", str(uuid.uuid4())),
            "name": emitter["name"],
            "latitude": emitter["latitude"] + random.uniform(-0.01, 0.01),
            "longitude": emitter["longitude"] + random.uniform(-0.01, 0.01),
            "signal_strength": -50 + random.uniform(-10, 10),  # dBm
            "frequency": (emitter["frequency_min"] + emitter["frequency_max"]) / 2 + random.uniform(-5, 5),
            "confidence": min(1.0, emitter.get("confidence", 0.85) + variation),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "affiliation": emitter["affiliation"],
            "threat_level": emitter["threat_level"]
        }
    
    def assess_threat(self, emitter: Dict) -> Dict:
        """Generate threat assessment for an emitter"""
        threat_scores = {"critical": 0.95, "high": 0.75, "medium": 0.5, "low": 0.25}
        base_score = threat_scores.get(emitter["threat_level"], 0.5)
        
        # Adjust based on type and affiliation
        if emitter["affiliation"] == "hostile":
            base_score *= 1.2
        elif emitter["affiliation"] == "friendly":
            base_score *= 0.1
        
        kill_chain_phases = ["detection", "tracking", "engagement", "intercept"]
        phase = random.choice(kill_chain_phases[:2]) if emitter["affiliation"] == "hostile" else "monitoring"
        
        actions = []
        if base_score > 0.7:
            actions = ["Activate ECM", "Deploy decoys", "Maneuver to minimize exposure"]
        elif base_score > 0.4:
            actions = ["Continue monitoring", "Prepare countermeasures"]
        else:
            actions = ["Track for intelligence", "Log to database"]
        
        return {
            "emitter_id": emitter.get("id", "unknown"),
            "emitter_name": emitter["name"],
            "threat_score": min(1.0, base_score),
            "kill_chain_phase": phase,
            "time_to_impact": random.uniform(30, 300) if base_score > 0.7 else None,
            "recommended_actions": actions,
            "assessed_at": datetime.now(timezone.utc).isoformat()
        }

simulator = BattlefieldSimulator()

# ============ WEBSOCKET CONNECTION MANAGER ============

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# ============ API ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "AEGIS MIND - Electronic Warfare Decision Support System", "status": "operational"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "AEGIS MIND",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Emitter Routes
@api_router.get("/emitters", response_model=List[Dict])
async def get_emitters(affiliation: Optional[str] = None, threat_level: Optional[str] = None):
    query = {}
    if affiliation:
        query["affiliation"] = affiliation
    if threat_level:
        query["threat_level"] = threat_level
    
    emitters = await db.emitters.find(query, {"_id": 0}).to_list(1000)
    if not emitters:
        # Return sample data if DB is empty
        return [dict(e, id=str(uuid.uuid4())) for e in SAMPLE_EMITTERS]
    return emitters

@api_router.post("/emitters", response_model=Dict)
async def create_emitter(emitter: EmitterCreate):
    emitter_obj = Emitter(**emitter.model_dump())
    doc = emitter_obj.model_dump()
    await db.emitters.insert_one(doc)
    return doc

@api_router.get("/emitters/{emitter_id}", response_model=Dict)
async def get_emitter(emitter_id: str):
    emitter = await db.emitters.find_one({"id": emitter_id}, {"_id": 0})
    if not emitter:
        raise HTTPException(status_code=404, detail="Emitter not found")
    return emitter

@api_router.delete("/emitters/{emitter_id}")
async def delete_emitter(emitter_id: str):
    result = await db.emitters.delete_one({"id": emitter_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Emitter not found")
    return {"message": "Emitter deleted"}

# Countermeasure Routes
@api_router.get("/countermeasures", response_model=List[Dict])
async def get_countermeasures():
    countermeasures = await db.countermeasures.find({}, {"_id": 0}).to_list(100)
    if not countermeasures:
        return [dict(c, id=str(uuid.uuid4())) for c in SAMPLE_COUNTERMEASURES]
    return countermeasures

@api_router.get("/countermeasures/recommend/{threat_type}")
async def recommend_countermeasures(threat_type: str):
    """Get recommended countermeasures for a specific threat type"""
    all_cms = await db.countermeasures.find({}, {"_id": 0}).to_list(100)
    if not all_cms:
        all_cms = [dict(c, id=str(uuid.uuid4())) for c in SAMPLE_COUNTERMEASURES]
    
    recommendations = [cm for cm in all_cms if threat_type.lower() in [t.lower() for t in cm.get("applicable_threats", [])]]
    return {
        "threat_type": threat_type,
        "recommendations": sorted(recommendations, key=lambda x: x.get("success_rate", 0), reverse=True),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Scenario Routes
@api_router.get("/scenarios", response_model=List[Dict])
async def get_scenarios():
    return SCENARIOS

@api_router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Get emitters for this scenario
    emitters = []
    for emitter_name in scenario.get("emitters", []):
        emitter = next((e for e in SAMPLE_EMITTERS if e["name"] == emitter_name), None)
        if emitter:
            emitters.append(dict(emitter, id=str(uuid.uuid4())))
    
    return {
        **scenario,
        "emitter_data": emitters,
        "loaded_at": datetime.now(timezone.utc).isoformat()
    }

@api_router.post("/scenarios/{scenario_id}/activate")
async def activate_scenario(scenario_id: str):
    """Activate a scenario and populate emitters"""
    scenario = next((s for s in SCENARIOS if s["id"] == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Clear existing simulation emitters and add scenario emitters
    await db.emitters.delete_many({"source": "simulation"})
    
    emitters_added = []
    for emitter_name in scenario.get("emitters", []):
        emitter_data = next((e for e in SAMPLE_EMITTERS if e["name"] == emitter_name), None)
        if emitter_data:
            emitter_obj = Emitter(**emitter_data, source="simulation")
            doc = emitter_obj.model_dump()
            await db.emitters.insert_one(doc)
            emitters_added.append(doc)
    
    return {
        "scenario_id": scenario_id,
        "status": "activated",
        "emitters_loaded": len(emitters_added),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Threat Assessment Routes
@api_router.get("/threats/assess")
async def assess_all_threats():
    """Generate threat assessment for all active emitters"""
    emitters = await db.emitters.find({"affiliation": "hostile"}, {"_id": 0}).to_list(100)
    if not emitters:
        emitters = [e for e in SAMPLE_EMITTERS if e["affiliation"] == "hostile"]
    
    assessments = [simulator.assess_threat(e) for e in emitters]
    return {
        "total_threats": len(assessments),
        "critical_count": sum(1 for a in assessments if a["threat_score"] > 0.8),
        "assessments": sorted(assessments, key=lambda x: x["threat_score"], reverse=True),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/threats/timeline")
async def get_threat_timeline():
    """Get threat timeline data for visualization"""
    # Generate simulated timeline data
    timeline = []
    base_time = datetime.now(timezone.utc)
    
    events = [
        ("Radar contact detected - Type 346B", "detection", "critical"),
        ("Tracking initiated on CSG", "tracking", "high"),
        ("New emitter - YLC-8B active", "detection", "high"),
        ("Missile seeker active - DF-21D", "engagement", "critical"),
        ("ECM deployed - AN/SLQ-32", "countermeasure", "info"),
        ("Threat neutralized - decoy success", "resolution", "success"),
    ]
    
    for i, (event, phase, severity) in enumerate(events):
        timeline.append({
            "id": str(uuid.uuid4()),
            "timestamp": (base_time.replace(second=0, microsecond=0)).isoformat(),
            "event": event,
            "phase": phase,
            "severity": severity,
            "offset_minutes": -i * 5
        })
    
    return {"timeline": timeline}

# AI Chat Routes
@api_router.post("/ai/chat", response_model=ChatResponse)
async def ai_chat(message: ChatMessage):
    """Send a message to the AI assistant"""
    # Get current threat context
    emitters = await db.emitters.find({}, {"_id": 0}).to_list(50)
    if not emitters:
        emitters = SAMPLE_EMITTERS[:5]
    
    context = {
        "active_emitters": len(emitters),
        "hostile_count": sum(1 for e in emitters if e.get("affiliation") == "hostile"),
        "threat_types": list(set(e.get("emitter_type", "unknown") for e in emitters)),
        "current_scenario": "Active monitoring"
    }
    
    response = await get_ai_response(message.message, context)
    
    return ChatResponse(
        response=response,
        context=context
    )

@api_router.get("/ai/analyze/{emitter_id}")
async def ai_analyze_emitter(emitter_id: str):
    """Get AI analysis of a specific emitter"""
    emitter = await db.emitters.find_one({"id": emitter_id}, {"_id": 0})
    if not emitter:
        # Try to find in sample data
        emitter = next((e for e in SAMPLE_EMITTERS if e.get("id") == emitter_id), None)
    
    if not emitter:
        raise HTTPException(status_code=404, detail="Emitter not found")
    
    query = f"""Analyze this electronic warfare emitter and provide tactical assessment:
    Name: {emitter.get('name')}
    Type: {emitter.get('emitter_type')}
    Origin: {emitter.get('origin')}
    Frequency: {emitter.get('frequency_min')}-{emitter.get('frequency_max')} MHz
    Platform: {emitter.get('platform')}
    Threat Level: {emitter.get('threat_level')}
    
    Provide: 1) Threat assessment 2) Likely mission 3) Recommended countermeasures 4) Kill chain position"""
    
    analysis = await get_ai_response(query)
    
    return {
        "emitter_id": emitter_id,
        "emitter_name": emitter.get("name"),
        "analysis": analysis,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# System Metrics
@api_router.get("/metrics")
async def get_system_metrics():
    """Get current system performance metrics"""
    emitters = await db.emitters.find({}, {"_id": 0}).to_list(1000)
    if not emitters:
        emitters = SAMPLE_EMITTERS
    
    hostile = [e for e in emitters if e.get("affiliation") == "hostile"]
    friendly = [e for e in emitters if e.get("affiliation") == "friendly"]
    
    return {
        "emitters_tracked": len(emitters),
        "hostile_count": len(hostile),
        "friendly_count": len(friendly),
        "classification_accuracy": 0.947,
        "processing_latency_ms": random.randint(15, 45),
        "threat_assessment_ms": random.randint(50, 95),
        "ai_response_ms": random.randint(200, 800),
        "uptime_hours": random.randint(100, 500),
        "signals_processed_24h": random.randint(50000, 150000),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# WebSocket for real-time updates
@app.websocket("/ws/battlefield")
async def websocket_battlefield(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            emitters = SAMPLE_EMITTERS[:5]
            updates = [simulator.generate_signal_update(e) for e in emitters]
            
            await websocket.send_json({
                "type": "battlefield_update",
                "data": updates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            await asyncio.sleep(2)  # Update every 2 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample data if empty"""
    logger.info("AEGIS MIND System Starting...")
    
    # Initialize countermeasures if empty
    count = await db.countermeasures.count_documents({})
    if count == 0:
        for cm in SAMPLE_COUNTERMEASURES:
            cm_obj = dict(cm, id=str(uuid.uuid4()))
            await db.countermeasures.insert_one(cm_obj)
        logger.info("Countermeasures database initialized")
    
    logger.info("AEGIS MIND System Online")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("AEGIS MIND System Shutdown")
