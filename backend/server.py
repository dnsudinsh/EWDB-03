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
app = FastAPI(title="EW HALIMUNAN ATM - Himpunan Analisis Lindungan Intelijen Medan Udara Negara")

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

# ============ SAMPLE DATA - EW HALIMUNAN ATM - MALAYSIAN ARMED FORCES ============

# Malacca Strait Commercial Radar Database
MALACCA_RADAR_DB = {
    "commercial_radars": ["S-band X-band", "Furuno FAR-21xx", "JRC JMA-53xx"],
    "pirate_signals": {
        "vhf_patterns": ["BaoFeng UV-5R bursts", "Motorola CP040 encrypted"],
        "satphone_bursts": ["Iridium 1626.5 MHz", "Thuraya 1626.75 MHz"],
    }
}

# Tactical EW Kit Configuration
TACTICAL_EW_KIT = {
    "hardware": {
        "sdr": "LimeSDR Mini (RM 2,500)",
        "tablet": "Ruggedized Android (RM 5,000)",
        "antenna": "Discone with tactical mast (RM 1,500)",
        "battery": "48-hour operation"
    },
    "capabilities": [
        "DF accuracy: 2° with 3 units",
        "Frequency range: 50MHz - 3.8GHz",
        "Storage: 10,000 signal fingerprints",
        "Burst detection: down to 50ms"
    ]
}

SAMPLE_EMITTERS = [
    # ===== DEMO 1: SELAT MELAKA GUARDIAN - QUICK WIN SCENARIO =====
    # Friendly Forces
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
        "latitude": 5.50,
        "longitude": 100.0,
        "affiliation": "friendly",
        "description": "TLDM Frigate on OP PASIR patrol duty",
        "scenario": "selat_melaka",
        "callsign": "PASIR-01"
    },
    {
        "name": "KD Gempita - Lumut EW Station",
        "emitter_type": "elint",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 50,
        "frequency_max": 3800,
        "modulation_type": "passive",
        "latitude": 4.24,
        "longitude": 100.62,
        "affiliation": "friendly",
        "description": "Coastal EW station monitoring 25,000 sq km of Malacca Strait",
        "scenario": "selat_melaka",
        "coverage_radius_km": 150
    },
    {
        "name": "MMEA Kimanis - OPV",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9200,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 5.75,
        "longitude": 100.25,
        "affiliation": "friendly",
        "description": "MMEA Offshore Patrol Vessel coordinating with TLDM",
        "scenario": "selat_melaka",
        "callsign": "MMEA-07"
    },
    {
        "name": "ATR-72 MPA - En Route",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9300,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 3.13,
        "longitude": 101.55,
        "affiliation": "friendly",
        "description": "Maritime Patrol Aircraft en route from Subang",
        "scenario": "selat_melaka",
        "callsign": "ORION-1"
    },
    # Piracy Threat Layer
    {
        "name": "MV Ocean Trader - Distress",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Panama",
        "threat_level": "medium",
        "frequency_min": 156.8,
        "frequency_max": 156.8,
        "modulation_type": "FM",
        "latitude": 5.65,
        "longitude": 100.15,
        "affiliation": "neutral",
        "description": "Container ship sending distress: Under attack by fast boats",
        "scenario": "selat_melaka",
        "ais_status": "active",
        "anomaly_score": 25
    },
    {
        "name": "Fast Attack Craft 1 - No AIS",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "critical",
        "frequency_min": 462.0,
        "frequency_max": 467.0,
        "modulation_type": "encrypted_fm",
        "latitude": 5.62,
        "longitude": 100.12,
        "affiliation": "hostile",
        "description": "Pirate fast boat - No AIS, IR signature detected, VHF chatter matches known patterns",
        "scenario": "selat_melaka",
        "ais_status": "disabled",
        "anomaly_score": 92
    },
    {
        "name": "Fast Attack Craft 2 - No AIS",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "critical",
        "frequency_min": 462.0,
        "frequency_max": 467.0,
        "modulation_type": "encrypted_fm",
        "latitude": 5.68,
        "longitude": 100.18,
        "affiliation": "hostile",
        "description": "Pirate fast boat - Coordinated attack pattern detected",
        "scenario": "selat_melaka",
        "ais_status": "disabled",
        "anomaly_score": 89
    },
    {
        "name": "SS Sunrise - Pirate Mothership",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 3.5,
        "frequency_max": 30.0,
        "modulation_type": "HF_SSB",
        "latitude": 5.55,
        "longitude": 99.95,
        "affiliation": "hostile",
        "description": "AIS spoofed as fishing vessel - Unusual HF transmissions - Coordinates 2km from claimed position",
        "scenario": "selat_melaka",
        "ais_status": "spoofed",
        "anomaly_score": 95
    },
    # Chinese ISR Threat Layer
    {
        "name": "Xiang Yang Hong 06 - Research Vessel",
        "emitter_type": "sonar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 12.0,
        "frequency_max": 12.0,
        "modulation_type": "multi_beam",
        "latitude": 4.85,
        "longitude": 99.75,
        "affiliation": "unknown",
        "description": "Chinese research vessel - Active multi-beam sonar, unusual radar sweeps, satellite uplink bursts",
        "scenario": "selat_melaka",
        "anomaly_score": 78
    },
    # Commercial Interference
    {
        "name": "VLCC TI Europe - Radar Fault",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Belgium",
        "threat_level": "low",
        "frequency_min": 9300,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 3.95,
        "longitude": 100.35,
        "affiliation": "neutral",
        "description": "Malfunctioning radar causing interference with Port Klang VTS",
        "scenario": "selat_melaka",
        "interference_source": True
    },
    
    # ===== DEMO 2: RAJAWALI SHIELD - TACTICAL BOOTS-ON-GROUND =====
    # Friendly Forces
    {
        "name": "11 RAD - Pulau Bum Bum",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 225.0,
        "frequency_max": 400.0,
        "modulation_type": "encrypted",
        "latitude": 4.48,
        "longitude": 118.68,
        "affiliation": "friendly",
        "description": "11th Battalion Royal Malay Regiment - Infantry position",
        "scenario": "rajawali",
        "callsign": "HARIMAU-6"
    },
    {
        "name": "PASKAL Team - Zodiac Insert",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 300.0,
        "frequency_max": 320.0,
        "modulation_type": "encrypted_burst",
        "latitude": 4.52,
        "longitude": 118.72,
        "affiliation": "friendly",
        "description": "PASKAL special forces inserting via Zodiac",
        "scenario": "rajawali",
        "callsign": "IKAN-1"
    },
    {
        "name": "EC-725 Caracal - Overwatch",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9000,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 4.55,
        "longitude": 118.60,
        "affiliation": "friendly",
        "description": "EC-725 helicopter providing overwatch - Hot extraction standby",
        "scenario": "rajawali",
        "callsign": "NURI-9"
    },
    {
        "name": "Tanjung Labian Radar",
        "emitter_type": "radar",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 2700,
        "frequency_max": 2900,
        "modulation_type": "pulse",
        "latitude": 4.35,
        "longitude": 118.40,
        "affiliation": "friendly",
        "description": "Coastal radar station - ESSCOM Sector 4 coverage",
        "scenario": "rajawali"
    },
    # KFR Threat Layer
    {
        "name": "KFR Signal 1 - Baofeng Encrypted",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Philippines",
        "threat_level": "critical",
        "frequency_min": 462.5625,
        "frequency_max": 462.5625,
        "modulation_type": "encrypted_fm",
        "latitude": 4.46,
        "longitude": 118.70,
        "affiliation": "hostile",
        "description": "Abu Sayyaf cell - Encryption matches 2014 Singamata attackers - 3 min pre-assault pattern",
        "scenario": "rajawali",
        "voice_match": "ASG Sub-leader Ali - 87% confidence",
        "anomaly_score": 95
    },
    {
        "name": "KFR Pump Boat 1",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Philippines",
        "threat_level": "critical",
        "frequency_min": 462.0,
        "frequency_max": 467.0,
        "modulation_type": "FM",
        "latitude": 4.44,
        "longitude": 118.73,
        "affiliation": "hostile",
        "description": "Militant pump boat - 3 persons detected",
        "scenario": "rajawali",
        "anomaly_score": 88
    },
    {
        "name": "KFR Pump Boat 2",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Philippines",
        "threat_level": "critical",
        "frequency_min": 462.0,
        "frequency_max": 467.0,
        "modulation_type": "FM",
        "latitude": 4.45,
        "longitude": 118.75,
        "affiliation": "hostile",
        "description": "Militant pump boat - 3 persons detected",
        "scenario": "rajawali",
        "anomaly_score": 86
    },
    # Smuggling Network
    {
        "name": "Smuggler Burst Signal",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 446.0,
        "frequency_max": 446.5,
        "modulation_type": "burst_fm",
        "latitude": 4.50,
        "longitude": 118.80,
        "affiliation": "hostile",
        "description": "Cigarette/arms smuggling - Burst transmission every 5 min - Pattern matches known smugglers",
        "scenario": "rajawali",
        "anomaly_score": 72
    },
    # Drone Recon
    {
        "name": "DJI Mavic 3 - Recon Drone",
        "emitter_type": "communication",
        "platform": "uav",
        "origin": "Unknown",
        "threat_level": "high",
        "frequency_min": 2400,
        "frequency_max": 2483,
        "modulation_type": "FHSS",
        "latitude": 4.475,
        "longitude": 118.67,
        "affiliation": "hostile",
        "description": "Reconnaissance drone observing base perimeter - 3rd day of activity pattern",
        "scenario": "rajawali",
        "controller_location": {"lat": 4.47, "lng": 118.69, "distance_m": 800},
        "anomaly_score": 85
    },
    
    # ===== DEMO 3: NUSANTARA SPECTRUM - STRATEGIC SCS SCENARIO =====
    # Friendly Forces
    {
        "name": "KD Mahawangsa - AOR",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9200,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 5.70,
        "longitude": 112.10,
        "affiliation": "friendly",
        "description": "Auxiliary Oiler Replenishment supporting SCS operations",
        "scenario": "nusantara",
        "callsign": "LOGISTIK-1"
    },
    {
        "name": "FA-18D Hornet 1 - CAP",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 8500,
        "frequency_max": 10500,
        "prf": 6000,
        "pulse_width": 0.2,
        "modulation_type": "pulse",
        "latitude": 5.95,
        "longitude": 111.80,
        "affiliation": "friendly",
        "description": "TUDM fighter on Combat Air Patrol with SUPER NASA radar",
        "scenario": "nusantara",
        "callsign": "HELANG-1"
    },
    {
        "name": "FA-18D Hornet 2 - CAP",
        "emitter_type": "radar",
        "platform": "aircraft",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 8500,
        "frequency_max": 10500,
        "prf": 6000,
        "pulse_width": 0.2,
        "modulation_type": "pulse",
        "latitude": 5.90,
        "longitude": 111.95,
        "affiliation": "friendly",
        "description": "TUDM fighter wingman - Combat Air Patrol",
        "scenario": "nusantara",
        "callsign": "HELANG-2"
    },
    {
        "name": "KD Rencong - Future LCS",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 9000,
        "frequency_max": 9500,
        "prf": 4000,
        "pulse_width": 0.4,
        "modulation_type": "pulse",
        "latitude": 5.75,
        "longitude": 112.05,
        "affiliation": "friendly",
        "description": "MEKO-class LCS with Thales NS 100 radar - Sovereignty patrol",
        "scenario": "nusantara",
        "callsign": "DAULAT-1"
    },
    {
        "name": "Platform Duyong-A - PETRONAS",
        "emitter_type": "communication",
        "platform": "ground",
        "origin": "Malaysia",
        "threat_level": "low",
        "frequency_min": 450.0,
        "frequency_max": 470.0,
        "modulation_type": "digital",
        "latitude": 5.72,
        "longitude": 111.98,
        "affiliation": "friendly",
        "description": "PETRONAS gas platform - Critical infrastructure (40% of national gas)",
        "scenario": "nusantara",
        "production_value_usd_day": 15000000
    },
    # CCG White Hull Threat
    {
        "name": "CCG 5901 - Mega Cutter",
        "emitter_type": "jammer",
        "platform": "ship",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 156.0,
        "frequency_max": 174.0,
        "modulation_type": "noise",
        "latitude": 5.85,
        "longitude": 112.25,
        "affiliation": "hostile",
        "description": "World's largest coast guard ship (12,000 ton) - Actively jamming Malaysian VHF communications",
        "scenario": "nusantara",
        "jamming_active": True,
        "escalation_risk": 0.34
    },
    {
        "name": "Maritime Militia Vessel 1",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 9300,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 5.80,
        "longitude": 112.18,
        "affiliation": "hostile",
        "description": "Little Blue Men - Fishing vessel creating swarm pattern",
        "scenario": "nusantara",
        "ais_status": "civilian"
    },
    {
        "name": "Maritime Militia Vessel 2",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 9300,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 5.82,
        "longitude": 112.22,
        "affiliation": "hostile",
        "description": "Little Blue Men - Coordinated movement pattern",
        "scenario": "nusantara"
    },
    {
        "name": "Maritime Militia Vessel 3",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 9300,
        "frequency_max": 9500,
        "modulation_type": "pulse",
        "latitude": 5.78,
        "longitude": 112.20,
        "affiliation": "hostile",
        "description": "Little Blue Men - Spectrum chaos creation",
        "scenario": "nusantara"
    },
    {
        "name": "Maritime Militia Vessel 4",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "China",
        "threat_level": "medium",
        "frequency_min": 156.0,
        "frequency_max": 163.0,
        "modulation_type": "FM",
        "latitude": 5.76,
        "longitude": 112.15,
        "affiliation": "hostile",
        "description": "Militia vessel - VHF crowding tactics",
        "scenario": "nusantara"
    },
    {
        "name": "Maritime Militia Vessel 5",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "China",
        "threat_level": "medium",
        "frequency_min": 156.0,
        "frequency_max": 163.0,
        "modulation_type": "FM",
        "latitude": 5.83,
        "longitude": 112.28,
        "affiliation": "hostile",
        "description": "Militia vessel - Exclusion zone approach",
        "scenario": "nusantara"
    },
    {
        "name": "Maritime Militia Vessel 6",
        "emitter_type": "communication",
        "platform": "ship",
        "origin": "China",
        "threat_level": "medium",
        "frequency_min": 156.0,
        "frequency_max": 163.0,
        "modulation_type": "FM",
        "latitude": 5.79,
        "longitude": 112.30,
        "affiliation": "hostile",
        "description": "Militia vessel - Pattern indicates coordinated probe",
        "scenario": "nusantara"
    },
    # PLA Navy Shadowing
    {
        "name": "Type 052D Kunming - Destroyer",
        "emitter_type": "radar",
        "platform": "ship",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 2900,
        "frequency_max": 3100,
        "prf": 5000,
        "modulation_type": "pulse",
        "latitude": 6.10,
        "longitude": 112.60,
        "affiliation": "hostile",
        "description": "PLA Navy destroyer over-the-horizon - Collecting MAF radar signatures",
        "scenario": "nusantara",
        "sigint_active": True
    },
    {
        "name": "H-6K Elint Aircraft",
        "emitter_type": "elint",
        "platform": "aircraft",
        "origin": "China",
        "threat_level": "critical",
        "frequency_min": 8000,
        "frequency_max": 18000,
        "modulation_type": "passive",
        "latitude": 6.25,
        "longitude": 112.45,
        "affiliation": "hostile",
        "description": "Electronic reconnaissance aircraft probing MAF air defense radar",
        "scenario": "nusantara",
        "sigint_active": True
    },
    # Space-based ISR
    {
        "name": "Yaogan Satellite - Overhead",
        "emitter_type": "radar",
        "platform": "satellite",
        "origin": "China",
        "threat_level": "high",
        "frequency_min": 9500,
        "frequency_max": 9800,
        "modulation_type": "SAR",
        "latitude": 5.80,
        "longitude": 112.00,
        "affiliation": "hostile",
        "description": "Yaogan satellite overhead in 15 minutes - SAR imaging capability",
        "scenario": "nusantara",
        "pass_time_minutes": 15
    }
]

SAMPLE_COUNTERMEASURES = [
    # Demo 1: Selat Melaka Guardian Countermeasures
    {
        "name": "Lumut EW Station Triangulation",
        "technique_type": "detection",
        "description": "Multi-site DF from Lumut, Langkawi, and Johor triangulates pirate communications within 2° accuracy",
        "success_rate": 0.88,
        "resource_cost": "medium",
        "applicable_threats": ["communication", "vhf_radio", "hf_ssb", "satphone"],
        "side_effects": "Requires coordination across 3 stations",
        "scenario": "selat_melaka"
    },
    {
        "name": "AIS Correlation Engine",
        "technique_type": "detection",
        "description": "AI correlates AIS signals with radar returns to identify vessels with spoofed or disabled transponders",
        "success_rate": 0.92,
        "resource_cost": "low",
        "applicable_threats": ["ais_spoofing", "pirate_vessel"],
        "side_effects": "2% false positive rate",
        "scenario": "selat_melaka"
    },
    {
        "name": "Piracy Risk Index Calculator",
        "technique_type": "intelligence",
        "description": "ML model considering moon phase, weather, recent incidents to predict piracy risk level",
        "success_rate": 0.78,
        "resource_cost": "low",
        "applicable_threats": ["piracy"],
        "side_effects": "None - predictive only",
        "scenario": "selat_melaka"
    },
    {
        "name": "VHF Selective Jammer",
        "technique_type": "jamming",
        "description": "Broadcast targeted VHF jam on pirate frequencies only, preserving legitimate maritime traffic",
        "success_rate": 0.82,
        "resource_cost": "medium",
        "applicable_threats": ["pirate_coordination"],
        "side_effects": "Risk of collateral interference within 5km",
        "scenario": "selat_melaka"
    },
    {
        "name": "ReCAAP Auto-Report Generator",
        "technique_type": "intelligence",
        "description": "Automatically generates POLIS reports for MMEA and updates ReCAAP ISC database in Singapore",
        "success_rate": 0.95,
        "resource_cost": "low",
        "applicable_threats": ["piracy", "robbery"],
        "side_effects": "None - administrative function",
        "scenario": "selat_melaka"
    },
    # Demo 2: Rajawali Shield Countermeasures  
    {
        "name": "Portable SDR Detector (RM 50K Kit)",
        "technique_type": "detection",
        "description": "LimeSDR Mini handheld system for MAF infantry - detects and locates transmitters in jungle/swamp terrain",
        "success_rate": 0.75,
        "resource_cost": "low",
        "applicable_threats": ["kfr_comms", "smuggler_radio", "drone_controller"],
        "side_effects": "48-hour battery, requires line of sight for best accuracy",
        "scenario": "rajawali",
        "cost_rm": 50000
    },
    {
        "name": "Voice Fingerprint Matcher",
        "technique_type": "intelligence",
        "description": "Audio fingerprinting identifies known KFR leaders from voice patterns with 87% confidence",
        "success_rate": 0.87,
        "resource_cost": "medium",
        "applicable_threats": ["kfr_comms", "militant_coordination"],
        "side_effects": "Requires existing voice database",
        "scenario": "rajawali"
    },
    {
        "name": "KFR Behavioral Predictor",
        "technique_type": "intelligence",
        "description": "ML model trained on 200+ historical KFR incidents - considers lunar cycle, weather, religious dates",
        "success_rate": 0.82,
        "resource_cost": "low",
        "applicable_threats": ["kfr_attack"],
        "side_effects": "None - predictive only",
        "scenario": "rajawali"
    },
    {
        "name": "Drone Frequency Jammer",
        "technique_type": "jamming",
        "description": "Targeted jamming of DJI control frequencies 2.4GHz only, preserving friendly comms",
        "success_rate": 0.88,
        "resource_cost": "medium",
        "applicable_threats": ["drone_recon", "uav_controller"],
        "side_effects": "Effective range 500m, may affect civilian WiFi",
        "scenario": "rajawali"
    },
    {
        "name": "Cyber-EW Malware Injection",
        "technique_type": "cyber",
        "description": "Inject tracking malware into captured militant devices to map entire KFR networks",
        "success_rate": 0.70,
        "resource_cost": "high",
        "applicable_threats": ["kfr_network", "smuggling_network"],
        "side_effects": "Risk of exposure, requires captured devices",
        "scenario": "rajawali"
    },
    # Demo 3: Nusantara Spectrum Countermeasures
    {
        "name": "Frequency Agility Mode - NS 100",
        "technique_type": "protection",
        "description": "Rapid frequency hopping on Thales NS 100 radar to resist CCG barrage jamming",
        "success_rate": 0.85,
        "resource_cost": "low",
        "applicable_threats": ["noise_jamming", "barrage_jamming"],
        "side_effects": "10% reduced detection range during transitions",
        "scenario": "nusantara"
    },
    {
        "name": "Satellite Comm Reroute",
        "technique_type": "protection",
        "description": "Re-route communications via MEASAT satellite, bypassing VHF jamming",
        "success_rate": 0.95,
        "resource_cost": "medium",
        "applicable_threats": ["vhf_jamming", "communication_denial"],
        "side_effects": "Increased latency, bandwidth limited",
        "scenario": "nusantara"
    },
    {
        "name": "Electronic Decoy Generator",
        "technique_type": "deception",
        "description": "Create false EM signatures making platform appear shutdown while operations continue",
        "success_rate": 0.78,
        "resource_cost": "medium",
        "applicable_threats": ["satellite_isr", "sigint_collection"],
        "side_effects": "Requires 30-minute setup time",
        "scenario": "nusantara"
    },
    {
        "name": "EW Drone Mapper",
        "technique_type": "intelligence",
        "description": "Deploy small EW drones to map Chinese radar coverage patterns during confrontation",
        "success_rate": 0.90,
        "resource_cost": "high",
        "applicable_threats": ["radar_mapping"],
        "side_effects": "Drone may be captured/lost",
        "scenario": "nusantara"
    },
    {
        "name": "AI Spectrum Deconfliction",
        "technique_type": "coordination",
        "description": "ML-driven spectrum allocation between TLDM, TUDM, MMEA to prevent friendly fratricide",
        "success_rate": 0.92,
        "resource_cost": "medium",
        "applicable_threats": ["spectrum_congestion", "friendly_interference"],
        "side_effects": "Requires real-time connectivity to all units",
        "scenario": "nusantara"
    },
    {
        "name": "UNCLOS Evidence Package Generator",
        "technique_type": "intelligence",
        "description": "Automatically packages timestamped signal recordings, geolocation, AIS logs for MOFA diplomatic protests",
        "success_rate": 0.95,
        "resource_cost": "low",
        "applicable_threats": ["sovereignty_intrusion", "eez_violation"],
        "side_effects": "None - passive collection per UNCLOS Article 121",
        "scenario": "nusantara"
    },
    {
        "name": "Escalation Risk Calculator",
        "technique_type": "intelligence",
        "description": "Based on 100+ historical SCS encounters, predicts probability of escalation and recommends response level",
        "success_rate": 0.85,
        "resource_cost": "low",
        "applicable_threats": ["ccg_confrontation", "militia_swarm"],
        "side_effects": "Requires diplomatic policy input",
        "scenario": "nusantara"
    }
]

SCENARIOS = [
    {
        "id": "scenario_1",
        "name": "SELAT MELAKA GUARDIAN",
        "name_bm": "Penjaga Selat Melaka",
        "description": "Maritime Domain Awareness & Anti-Piracy - Quick Win Demo showing how one EW station in Lumut can monitor the entire northern Malacca Strait",
        "executive_hook": "Show how one EW station provides 10x situational awareness at 1/10th the cost of additional patrol vessels",
        "region": "Selat Melaka (40NM NW of Pulau Pinang)",
        "center_lat": 5.50,
        "center_lng": 100.15,
        "zoom": 9,
        "time_setting": "0300H Tuesday - Peak shipping hours",
        "emitters": ["KD Lekiu - TLDM Frigate", "KD Gempita - Lumut EW Station", "MMEA Kimanis - OPV", "ATR-72 MPA - En Route", "MV Ocean Trader - Distress", "Fast Attack Craft 1 - No AIS", "Fast Attack Craft 2 - No AIS", "SS Sunrise - Pirate Mothership", "Xiang Yang Hong 06 - Research Vessel", "VLCC TI Europe - Radar Fault"],
        "threat_summary": "Multi-threat environment: Pirate attack in progress on container ship, Chinese ISR vessel conducting unusual surveys, commercial radar interference with Port Klang VTS",
        "threat_layers": ["Piracy Activity", "State Actor ISR", "Accidental Interference"],
        "ew_focus": ["Electronic Support (ES)", "COMINT/DF Triangulation", "AIS Correlation", "Pattern of Life Analysis"],
        "operations": ["OP PASIR", "MMEA Joint Ops", "ReCAAP Coordination"],
        "demo_duration_minutes": 7,
        "key_metrics": {
            "response_time_min": 4,
            "false_positive_rate": 0.02,
            "coverage_sq_km": 25000,
            "station_cost_rm_year": 500000,
            "patrol_vessel_cost_rm": 50000000
        }
    },
    {
        "id": "scenario_2", 
        "name": "RAJAWALI SHIELD",
        "name_bm": "Perisai Rajawali",
        "description": "Sabah ESSCOM Border Surveillance - Tactical Demo showing how RM 50K handheld EW gives infantry same capability as RM 50M airborne system",
        "executive_hook": "Show how a RM 50,000 handheld EW device gives infantry battalions in Sabah the same electronic sensing capability as airborne system",
        "region": "ESSZONE Sector 4 (Semporna - Pulau Bum Bum)",
        "center_lat": 4.48,
        "center_lng": 118.68,
        "zoom": 12,
        "time_setting": "0200H Monsoon Season - Heavy rain, low visibility",
        "emitters": ["11 RAD - Pulau Bum Bum", "PASKAL Team - Zodiac Insert", "EC-725 Caracal - Overwatch", "Tanjung Labian Radar", "KFR Signal 1 - Baofeng Encrypted", "KFR Pump Boat 1", "KFR Pump Boat 2", "Smuggler Burst Signal", "DJI Mavic 3 - Recon Drone"],
        "threat_summary": "Asymmetric threats: Abu Sayyaf KFR cell with 6 militants in 2 pump boats, smuggling network using burst transmissions, reconnaissance drone 3rd day of pattern - attack imminent",
        "threat_layers": ["Kidnap-for-Ransom (KFR) Team", "Smuggling Network", "Drone Reconnaissance"],
        "ew_focus": ["Low-Cost Portable EW", "Audio Fingerprinting", "KFR Pattern Recognition", "Counter-UAV"],
        "operations": ["OP SABAH TIMUR", "ESSCOM Border Ops"],
        "demo_duration_minutes": 8,
        "key_metrics": {
            "kit_cost_rm": 50000,
            "signal_detection_count": 47,
            "suspicious_filtered": 3,
            "civilian_filtered": 44,
            "ransom_prevented_rm": 5000000
        }
    },
    {
        "id": "scenario_3",
        "name": "NUSANTARA SPECTRUM",
        "name_bm": "Spektrum Nusantara",
        "description": "South China Sea Strategic Deterrence - Show how Malaysia defends SCS claims using electronic warfare as proportional, non-kinetic tool with diplomatic evidence collection",
        "executive_hook": "Show how Malaysia can defend its South China Sea claims using EW as a proportional, non-kinetic tool that provides diplomatic evidence while protecting assets",
        "region": "Malaysian EEZ (Kasawari Gas Field - Luconia Shoals)",
        "center_lat": 5.80,
        "center_lng": 112.10,
        "zoom": 9,
        "time_setting": "Current - Strategic confrontation in progress",
        "emitters": ["KD Mahawangsa - AOR", "FA-18D Hornet 1 - CAP", "FA-18D Hornet 2 - CAP", "KD Rencong - Future LCS", "Platform Duyong-A - PETRONAS", "CCG 5901 - Mega Cutter", "Maritime Militia Vessel 1", "Maritime Militia Vessel 2", "Maritime Militia Vessel 3", "Maritime Militia Vessel 4", "Maritime Militia Vessel 5", "Maritime Militia Vessel 6", "Type 052D Kunming - Destroyer", "H-6K Elint Aircraft", "Yaogan Satellite - Overhead"],
        "threat_summary": "High-end state actor threat: CCG 5901 actively jamming Malaysian VHF, 6 Maritime Militia vessels creating spectrum chaos, PLA Navy destroyer collecting radar signatures, satellite ISR pass in 15 minutes",
        "threat_layers": ["CCG White Hull Pressure", "PLA Navy Shadowing", "Space-based ISR"],
        "ew_focus": ["Electronic Protection (EP)", "Satellite Comms", "Electronic Deception", "Joint Spectrum Management", "Diplomatic Evidence Collection"],
        "operations": ["TLDM Sovereignty Patrol", "TUDM Air Defense", "PETRONAS Critical Infrastructure Protection"],
        "demo_duration_minutes": 10,
        "key_metrics": {
            "ew_operation_cost_rm": 250000,
            "platform_production_loss_if_shutdown_rm": 25000000,
            "escalation_probability": 0.34,
            "intelligence_gathered": "14 new radar signatures, 3 new comm protocols"
        }
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
        
        system_message = """You are EW HALIMUNAN ATM AI Assistant - Himpunan Analisis Lindungan Intelijen Medan Udara Negara.
You serve the Malaysian Armed Forces (Angkatan Tentera Malaysia - ATM) as an Electronic Warfare decision support system.

SYSTEM TAGLINE: "Halimun menjadi perisai senyap angkasa memayungi negara"
(The Mist becomes the silent shield of the skies protecting the nation)

OPERATIONAL CONTEXT:
- Primary users: TLDM (Royal Malaysian Navy), TUDM (Royal Malaysian Air Force), TDM (Malaysian Army), ESSCOM
- Key operations: OP PASIR (Malacca Strait), OP SABAH TIMUR (ESSCOM), SCS Sovereignty Patrols
- Partner agencies: MMEA (Maritime Enforcement), PDRM (Police), ReCAAP ISC

THREE DEMONSTRATION SCENARIOS:
1. SELAT MELAKA GUARDIAN - Anti-piracy & maritime domain awareness (Quick Win - 7 min)
2. RAJAWALI SHIELD - ESSCOM border surveillance vs KFR/smuggling (Tactical - 8 min)  
3. NUSANTARA SPECTRUM - SCS strategic deterrence vs CCG/PLA (Strategic - 10 min)

KEY CAPABILITIES:
- Anomaly detection: Calculate threat scores from AIS correlation, emission patterns
- Pattern-of-life analysis: ML models trained on 6 months historical data
- Voice fingerprinting: Identify known KFR leaders (Abu Sayyaf/ISSP)
- Escalation prediction: Based on 100+ historical SCS encounters
- Diplomatic evidence: Auto-generate UNCLOS-compliant incident reports

RESPONSE FORMAT:
- Use military-professional Malay/English mix terminology
- Provide confidence levels (%) and cost implications (RM)
- Reference specific MAF assets: KD Lekiu, KD Rencong, F/A-18D, EC-725, etc.
- Support Malaysia's strategic neutrality - proportional, non-kinetic responses
- Format for quick comprehension in tactical environment"""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"halimun-{uuid.uuid4()}",
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
        "system": "EW HALIMUNAN ATM",
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
        # Try to find in sample data by ID
        emitter = next((e for e in SAMPLE_EMITTERS if e.get("id") == emitter_id), None)
    if not emitter:
        # Try to find by name (URL decoded)
        from urllib.parse import unquote
        decoded_id = unquote(emitter_id)
        emitter = next((e for e in SAMPLE_EMITTERS if e.get("name") == decoded_id), None)
    
    if not emitter:
        raise HTTPException(status_code=404, detail="Emitter not found")
    
    query = f"""Analyze this electronic warfare emitter and provide tactical assessment for Malaysian Armed Forces:
    Name: {emitter.get('name')}
    Type: {emitter.get('emitter_type')}
    Origin: {emitter.get('origin')}
    Frequency: {emitter.get('frequency_min')}-{emitter.get('frequency_max')} MHz
    Platform: {emitter.get('platform')}
    Threat Level: {emitter.get('threat_level')}
    Affiliation: {emitter.get('affiliation')}
    Description: {emitter.get('description', 'N/A')}
    
    Provide in Malay/English mix: 1) Threat assessment 2) Likely mission 3) Recommended countermeasures 4) Kill chain position"""
    
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

# Root-level health check for Kubernetes deployment
@app.get("/health")
async def root_health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {
        "status": "healthy",
        "system": "EW HALIMUNAN ATM",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

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
    logger.info("EW HALIMUNAN ATM - Memulakan Sistem...")
    
    # Initialize countermeasures if empty
    count = await db.countermeasures.count_documents({})
    if count == 0:
        for cm in SAMPLE_COUNTERMEASURES:
            cm_obj = dict(cm, id=str(uuid.uuid4()))
            await db.countermeasures.insert_one(cm_obj)
        logger.info("Pangkalan data countermeasures diinisialisasi")
    
    logger.info("EW HALIMUNAN ATM - Sistem Aktif")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("EW HALIMUNAN ATM - Sistem Ditutup")
