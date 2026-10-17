"""
Pydantic models and TypedDicts used across the application.

These are the *contracts* between agents — every provider and agent
reads from / writes to structures defined here.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class DataType(str, Enum):
    """Provenance tag: how trustworthy is this piece of data?"""
    LIVE = "live"
    ESTIMATED = "estimated"
    CACHED = "cached"
    MOCK = "mock"


class HumanDecision(str, Enum):
    APPROVE = "approve"
    CHANGES = "changes"
    PENDING = "pending"


# ── Flight ─────────────────────────────────────────────────────────────

class FlightResult(BaseModel):
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration_minutes: int
    price: float
    currency: str = "INR"
    source: str = "unknown"
    data_type: DataType = DataType.ESTIMATED


# ── Hotel ──────────────────────────────────────────────────────────────

class HotelResult(BaseModel):
    name: str
    location: str
    nightly_price: float
    total_price: float = 0.0
    rating: float = 0.0
    amenities: list[str] = Field(default_factory=list)
    source: str = "unknown"
    data_type: DataType = DataType.ESTIMATED


# ── Weather ────────────────────────────────────────────────────────────

class DailyWeather(BaseModel):
    date: str
    temperature_high: float
    temperature_low: float
    rain_probability: float = 0.0
    description: str = ""


class WeatherInfo(BaseModel):
    location: str
    daily: list[DailyWeather] = Field(default_factory=list)
    packing_suggestions: list[str] = Field(default_factory=list)
    source: str = "unknown"
    data_type: DataType = DataType.ESTIMATED


# ── Budget ─────────────────────────────────────────────────────────────

class BudgetAnalysis(BaseModel):
    flights: float = 0.0
    hotels: float = 0.0
    transport: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    miscellaneous: float = 0.0
    estimated_total: float = 0.0
    user_budget: float = 0.0
    remaining_budget: float = 0.0
    within_budget: bool = True
    currency: str = "INR"


# ── Trip Constraints ───────────────────────────────────────────────────

class TripConstraints(BaseModel):
    destination: str = ""
    origin: str = ""
    duration_days: int = 0
    start_date: str = ""
    end_date: str = ""
    budget: float = 0.0
    currency: str = "INR"
    traveler_count: int = 1
    preferences: list[str] = Field(default_factory=list)


# ── Supervisor Output ─────────────────────────────────────────────────

class SupervisorOutput(BaseModel):
    selected_agents: list[str] = Field(default_factory=list)
    trip_constraints: TripConstraints = Field(default_factory=TripConstraints)
    reasoning: str = ""


# ── Guardrail Output ──────────────────────────────────────────────────

class GuardrailResult(BaseModel):
    allowed: bool = True
    reason: str = ""
    normalized_request: str = ""
