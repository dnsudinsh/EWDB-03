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
app = FastAPI(title="AEGIS MIND - Sistem Sokongan Keputusan Peperangan Elektronik ATM")

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

# ============ SAMPLE DATA - MALAYSIAN ARMED FORCES CONTEXT ============

SAMPLE_EMITTERS = [
    # ===== SCENARIO 1: SELAT MELAKA GUARDIAN - Malacca Strait =====
    {
        "name": "Xiang Yang Hong 03 - Research Vessel",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 2800,
        "frequency_max": 3200,
        "prf": 2000,
        "pulse_width": 2.0,
        "modulation_type": "pulse",
        "latitude": 3.85,
        "longitude": 100.2,
        "affiliation": "unknown",
        "description": "Chinese 'research vessel' conducting surveys with unusual radar emissions"
    },
    {
        "name": "MV Sinar Kudus - Pirate Mothership",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 156.0,
        "frequency_max": 157.0,
        "modulation_type": "FM",
        "latitude": 4.12,
        "longitude": 100.45,
        "affiliation": "hostile",
        "description": "Suspected pirate mothership using encrypted VHF for coordination"
    },
    {
        "name": "Vietnamese Fishing Fleet - GPS Spoofed",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Vietnam",
        "threat_level": "medium",
        "frequency_min": 1575.0,
        "frequency_max": 1580.0,
        "modulation_type": "spread_spectrum",
        "latitude": 4.35,
        "longitude": 100.8,
        "affiliation": "unknown",
        "description": "Fishing vessels with disabled AIS in Malaysian EEZ"
    },
    {
        "name": "KD Lekiu - TLDM Frigate",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 8500,
        "frequency_max": 9500,
        "prf": 3500,
        "pulse_width": 0.5,
        "modulation_type": "pulse",
        "latitude": 4.0,
        "longitude": 100.3,
        "affiliation": "friendly",
        "description": "TLDM patrol vessel on OP PASIR duty"
    },
    {
        "name": "Lumut EW Station",
        "emitter_type": "radar",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 1200,
        "frequency_max": 1400,
        "prf": 400,
        "pulse_width": 20,
        "modulation_type": "pulse",
        "latitude": 4.24,
        "longitude": 100.62,
        "affiliation": "friendly",
        "description": "Coastal surveillance radar station"
    },
    # ===== SCENARIO 2: RAJAWALI SHIELD - Sabah ESSCOM =====
    {
        "name": "Abu Sayyaf Comms - Baofeng Radio",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Philippines",
        "threat_level": "critical",
        "frequency_min": 400.0,
        "frequency_max": 470.0,
        "modulation_type": "FM",
        "latitude": 4.45,
        "longitude": 118.65,
        "affiliation": "hostile",
        "description": "KFR group using commercial radio with rudimentary encryption"
    },
    {
        "name": "Panther Boat - Sat Phone Burst",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 1616.0,
        "frequency_max": 1626.5,
        "modulation_type": "TDMA",
        "latitude": 4.52,
        "longitude": 118.8,
        "affiliation": "hostile",
        "description": "Fast smuggling boat with intermittent Iridium satellite phone"
    },
    {
        "name": "Recon Drone - DJI Controller",
        "emitter_type": "communication",
        "platform": "uav",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 2400,
        "frequency_max": 2483,
        "modulation_type": "FHSS",
        "latitude": 4.48,
        "longitude": 118.72,
        "affiliation": "hostile",
        "description": "Modified DJI drone for pre-raid ISR of ESSCOM bases"
    },
    {
        "name": "ESSCOM Command Post",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 225.0,
        "frequency_max": 400.0,
        "modulation_type": "encrypted",
        "latitude": 4.47,
        "longitude": 118.1,
        "affiliation": "friendly",
        "description": "Eastern Security Command tactical communications"
    },
    {
        "name": "Aerodyne Counter-UAV",
        "emitter_type": "jammer",
        "platform": "uav",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 2400,
        "frequency_max": 5800,
        "modulation_type": "broadband",
        "latitude": 4.46,
        "longitude": 118.15,
        "affiliation": "friendly",
        "description": "Malaysian-made drone with lightweight jammer payload"
    },
    # ===== SCENARIO 3: NUSANTARA SPECTRUM - South China Sea =====
    {
        "name": "CCG 5901 - Coast Guard Cutter",
        "emitter_type": "jammer",
        "platform": "ship",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 100.0,
        "frequency_max": 500.0,
        "modulation_type": "noise",
        "latitude": 5.82,
        "longitude": 112.15,
        "affiliation": "hostile",
        "description": "World's largest coast guard ship with advanced EW suite jamming MAF comms"
    },
    {
        "name": "Maritime Militia Flotilla",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 156.0,
        "frequency_max": 163.0,
        "modulation_type": "FM",
        "latitude": 5.75,
        "longitude": 112.3,
        "affiliation": "hostile",
        "description": "'Little Blue Men' civilian vessels creating spectrum chaos"
    },
    {
        "name": "H-6K Elint Aircraft",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 8000,
        "frequency_max": 12000,
        "prf": 5000,
        "pulse_width": 0.3,
        "modulation_type": "chirp",
        "latitude": 6.1,
        "longitude": 112.5,
        "affiliation": "hostile",
        "description": "Electronic reconnaissance aircraft probing MAF air defense"
    },
    {
        "name": "KD Keris - LCS Patrol",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9000,
        "frequency_max": 9500,
        "prf": 4000,
        "pulse_width": 0.4,
        "modulation_type": "pulse",
        "latitude": 5.65,
        "longitude": 112.0,
        "affiliation": "friendly",
        "description": "Littoral Combat Ship with Thales NS 100 radar"
    },
    {
        "name": "F/A-18D Hornet - TUDM",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 8500,
        "frequency_max": 10500,
        "prf": 6000,
        "pulse_width": 0.2,
        "modulation_type": "pulse",
        "latitude": 5.9,
        "longitude": 111.8,
        "affiliation": "friendly",
        "description": "TUDM fighter with SUPER NASA radar on air defense patrol"
    },
    {
        "name": "Kasawari Gas Platform",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 450.0,
        "frequency_max": 470.0,
        "modulation_type": "digital",
        "latitude": 5.7,
        "longitude": 111.95,
        "affiliation": "friendly",
        "description": "PETRONAS critical infrastructure requiring EW protection"
    }
]

SAMPLE_COUNTERMEASURES = [
    {
        "name": "Dagaie NG Decoy System",
        "technique_type": "deception",
        "description": "Naval decoy system on TLDM LCS that mimics commercial tanker signatures to draw out pirates",
        "success_rate": 0.82,
        "resource_cost": "medium",
        "applicable_threats": ["radar", "anti_ship_missile", "pirate_targeting"],
        "side_effects": "Limited inventory per mission"
    },
    {
        "name": "Portable EW Jammer - Handheld",
        "technique_type": "jamming",
        "description": "Man-portable jammer for MAF infantry to detect drone controllers and locate hidden transmitters",
        "success_rate": 0.75,
        "resource_cost": "low",
        "applicable_threats": ["uav_datalink", "communication", "commercial_radio"],
        "side_effects": "Short range, requires line of sight"
    },
    {
        "name": "COMINT/DF Triangulation Array",
        "technique_type": "detection",
        "description": "Multi-site direction finding from Lumut, Langkawi, and Johor to triangulate pirate communications",
        "success_rate": 0.88,
        "resource_cost": "high",
        "applicable_threats": ["communication", "vhf_radio", "satellite_phone"],
        "side_effects": "Requires coordination across multiple stations"
    },
    {
        "name": "GPS Spoofing Defense",
        "technique_type": "cyber",
        "description": "Counter-spoofing system to protect PETRONAS platforms from GPS manipulation",
        "success_rate": 0.78,
        "resource_cost": "medium",
        "applicable_threats": ["gps_spoofing", "navigation_attack"],
        "side_effects": "May require temporary GPS blackout for calibration"
    },
    {
        "name": "Frequency Agility Mode - NS 100",
        "technique_type": "protection",
        "description": "Rapid frequency hopping on Thales NS 100 radar to resist CCG jamming",
        "success_rate": 0.85,
        "resource_cost": "low",
        "applicable_threats": ["noise_jamming", "barrage_jamming"],
        "side_effects": "Reduced detection range during frequency transitions"
    },
    {
        "name": "AI Spectrum Manager",
        "technique_type": "coordination",
        "description": "ML-driven spectrum allocation between TLDM, TUDM, and MMEA to prevent fratricide",
        "success_rate": 0.92,
        "resource_cost": "medium",
        "applicable_threats": ["spectrum_congestion", "friendly_interference"],
        "side_effects": "Requires real-time connectivity to all units"
    },
    {
        "name": "Diplomatic Evidence Generator",
        "technique_type": "intelligence",
        "description": "Automated incident reports with signal recordings for MOFA protests",
        "success_rate": 0.95,
        "resource_cost": "low",
        "applicable_threats": ["sovereignty_intrusion", "eez_violation"],
        "side_effects": "None - passive collection"
    },
    {
        "name": "Cyber-EW Malware Injection",
        "technique_type": "cyber",
        "description": "Inject tracking malware into captured militant devices to map entire KFR networks",
        "success_rate": 0.70,
        "resource_cost": "high",
        "applicable_threats": ["kfr_network", "smuggling_network"],
        "side_effects": "Risk of exposure, requires captured devices"
    }
]

SCENARIOS = [
    {
        "id": "scenario_1",
        "name": "Selat Melaka Guardian",
        "name_bm": "Penjaga Selat Melaka",
        "description": "Maritime Domain Awareness & Anti-Piracy operations in the critical Malacca Strait choke point between Port Klang and Pulau Pinang",
        "region": "Selat Melaka (Malacca Strait)",
        "center_lat": 4.0,
        "center_lng": 100.4,
        "zoom": 8,
        "emitters": ["Xiang Yang Hong 03 - Research Vessel", "MV Sinar Kudus - Pirate Mothership", "Vietnamese Fishing Fleet - GPS Spoofed", "KD Lekiu - TLDM Frigate", "Lumut EW Station"],
        "threat_summary": "Multi-threat environment: State actor ISR (Chinese research vessel), pirate mothership coordinating fast boat attacks, illegal fishing with GPS spoofing. Support OP PASIR and MMEA cooperation.",
        "ew_focus": ["Electronic Support (ES)", "COMINT/DF", "AIS Correlation", "Pattern of Life Analysis"],
        "operations": ["OP PASIR", "MMEA Joint Ops"]
    },
    {
        "id": "scenario_2", 
        "name": "Rajawali Shield",
        "name_bm": "Perisai Rajawali",
        "description": "Sabah Eastern Security Command (ESSCOM) border surveillance against KFR groups, smuggling networks, and intrusion drones in ESSZONE from Semporna to Tawau",
        "region": "ESSZONE - Sabah Timur",
        "center_lat": 4.48,
        "center_lng": 118.5,
        "zoom": 10,
        "emitters": ["Abu Sayyaf Comms - Baofeng Radio", "Panther Boat - Sat Phone Burst", "Recon Drone - DJI Controller", "ESSCOM Command Post", "Aerodyne Counter-UAV"],
        "threat_summary": "Asymmetric threats: Abu Sayyaf/ISSP-linked militants using encrypted commercial radios, smuggling boats running dark, reconnaissance drones targeting ESSCOM bases. Direct support to OP SABAH TIMUR.",
        "ew_focus": ["Low-Cost Portable EW", "KFR Pattern Recognition", "Cyber-EW Convergence", "Counter-UAV"],
        "operations": ["OP SABAH TIMUR", "ESSCOM Border Ops"]
    },
    {
        "id": "scenario_3",
        "name": "Nusantara Spectrum",
        "name_bm": "Spektrum Nusantara",
        "description": "South China Sea sovereignty patrol and strategic deterrence near Beting Patinggi Ali (Luconia Shoals) and Kasawari gas field, protecting Malaysian EEZ",
        "region": "Laut China Selatan (SCS) - Malaysian EEZ",
        "center_lat": 5.8,
        "center_lng": 112.1,
        "zoom": 8,
        "emitters": ["CCG 5901 - Coast Guard Cutter", "Maritime Militia Flotilla", "H-6K Elint Aircraft", "KD Keris - LCS Patrol", "F/A-18D Hornet - TUDM", "Kasawari Gas Platform"],
        "threat_summary": "High-end state actor threat: CCG ships with advanced jammers, 'Little Blue Men' creating spectrum chaos, H-6K electronic reconnaissance probing air defense, need to protect PETRONAS Kasawari gas field.",
        "ew_focus": ["Electronic Protection (EP)", "Joint Spectrum Management", "Counter-ISR", "Diplomatic Evidence Collection"],
        "operations": ["TLDM Sovereignty Patrol", "TUDM Air Defense", "PETRONAS Protection"]
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
        
        system_message = """You are AEGIS MIND, an advanced Electronic Warfare AI assistant for the Malaysian Armed Forces (Angkatan Tentera Malaysia - ATM).

OPERATIONAL CONTEXT:
- Supporting TLDM (Royal Malaysian Navy), TUDM (Royal Malaysian Air Force), and TDM (Malaysian Army)
- Key operations: OP PASIR (Malacca Strait), OP SABAH TIMUR (ESSCOM), sovereignty patrols in South China Sea
- Coordinating with MMEA (Malaysian Maritime Enforcement Agency) and PDRM (Royal Malaysian Police)

THREAT ENVIRONMENT:
- State actors: Chinese coast guard (CCG), research vessels, and 'Little Blue Men' maritime militia
- Non-state actors: Abu Sayyaf/ISSP KFR groups, pirates, smuggling networks
- Critical infrastructure: PETRONAS offshore platforms (Kasawari gas field)

You provide:
- Threat analysis specific to Malaysian territorial waters and EEZ
- Countermeasure recommendations within MAF capabilities
- Kill chain analysis for both state and non-state threats
- Spectrum management for joint operations
- Cost-effective solutions for budget constraints

Respond in a concise, military-professional manner. Use technical terminology appropriately.
When discussing threats, provide confidence levels, recommended actions, and cost implications.
Reference specific Malaysian assets (KD Lekiu, F/A-18D, LCS, etc.) when relevant.
Support diplomatic objectives - Malaysia maintains strategic neutrality."""

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
