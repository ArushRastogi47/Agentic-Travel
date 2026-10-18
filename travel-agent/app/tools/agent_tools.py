"""
Executable LangChain tools for real model tool calling.
These tools wrap the underlying providers and can be bound directly to Gemini.
"""

from __future__ import annotations

import json
from langchain_core.tools import tool

from app.logging_config import logger
from app.tools.flights import get_flight_provider
from app.tools.hotels import get_hotel_provider
from app.tools.places import get_places_provider
from app.tools.routing import get_routing_provider
from app.tools.weather import get_weather_provider


@tool
def search_flights(origin: str, destination: str, date: str, travelers: int = 1) -> str:
    """
    Search for flights between origin and destination on a specific date.
    
    Args:
        origin: Departure city or airport code (e.g., 'Delhi' or 'DEL')
        destination: Arrival destination city (e.g., 'Dubai', 'Goa', 'Paris')
        date: Travel date in YYYY-MM-DD format
        travelers: Number of passengers (default 1)
    """
    logger.info(f"[Tool:search_flights] Calling for {origin} -> {destination} on {date}")
    try:
        provider = get_flight_provider()
        results = provider.search_flights(origin, destination, date, travelers)
        return json.dumps([r.model_dump(mode="json") for r in results], indent=2)
    except Exception as exc:
        return f"Flight search failed: {exc}"


@tool
def search_hotels(destination: str, check_in: str, check_out: str, nights: int = 3) -> str:
    """
    Search for hotel accommodations at a destination for the given stay duration.
    
    Args:
        destination: Destination city (e.g., 'Dubai', 'Goa', 'Paris')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        nights: Number of nights to stay (e.g., 3)
    """
    logger.info(f"[Tool:search_hotels] Calling for {destination} ({nights} nights)")
    try:
        provider = get_hotel_provider()
        results = provider.search_hotels(destination, check_in, check_out, nights)
        return json.dumps([r.model_dump(mode="json") for r in results], indent=2)
    except Exception as exc:
        return f"Hotel search failed: {exc}"


@tool
def get_weather_forecast(destination: str, start_date: str, end_date: str) -> str:
    """
    Get live weather forecast and packing recommendations for a destination.
    
    Args:
        destination: Target destination city (e.g., 'Dubai', 'Goa', 'Paris')
        start_date: Start date of trip in YYYY-MM-DD format
        end_date: End date of trip in YYYY-MM-DD format
    """
    logger.info(f"[Tool:get_weather_forecast] Calling for {destination} ({start_date} to {end_date})")
    try:
        provider = get_weather_provider()
        info = provider.get_weather(destination, start_date, end_date)
        return json.dumps(info.model_dump(mode="json"), indent=2)
    except Exception as exc:
        return f"Weather forecast failed: {exc}"


@tool
def get_destination_attractions(destination: str) -> str:
    """
    Get popular points of interest, tourist attractions, and activities for a destination.
    
    Args:
        destination: Target city name (e.g., 'Dubai', 'Goa', 'Paris')
    """
    logger.info(f"[Tool:get_destination_attractions] Calling for {destination}")
    try:
        provider = get_places_provider()
        places = provider.get_places(destination)
        return json.dumps(places, indent=2)
    except Exception as exc:
        return f"Attractions lookup failed: {exc}"


@tool
def calculate_trip_budget(
    destination: str,
    duration_days: int,
    user_budget: float = 0.0,
    flight_price: float = 0.0,
    hotel_nightly_price: float = 0.0,
) -> str:
    """
    Calculate deterministic trip expenses including transit, dining, activities, and buffer.
    
    Args:
        destination: Destination city name
        duration_days: Length of trip in days
        user_budget: Target maximum budget provided by user
        flight_price: Estimated one-way or base flight price
        hotel_nightly_price: Nightly room price
    """
    logger.info(f"[Tool:calculate_trip_budget] Computing budget for {destination}")
    try:
        from app.agents.budget_agent import _DAILY_ACTIVITIES, _DAILY_FOOD

        nights = max(duration_days - 1, 1)
        flight_cost = flight_price * 2  # roundtrip
        hotel_cost = hotel_nightly_price * nights

        routing = get_routing_provider()
        transport_info = routing.estimate_transport(destination, duration_days)
        transport_cost = transport_info.get("total_transport_cost", 0)

        dest_lower = destination.lower()
        food_cost = _DAILY_FOOD.get(dest_lower, 1500) * duration_days
        activities_cost = _DAILY_ACTIVITIES.get(dest_lower, 1500) * duration_days

        subtotal = flight_cost + hotel_cost + transport_cost + food_cost + activities_cost
        misc = round(subtotal * 0.10, 2)
        total = round(subtotal + misc, 2)

        return json.dumps({
            "destination": destination,
            "duration_days": duration_days,
            "flights": flight_cost,
            "hotels": hotel_cost,
            "transport": transport_cost,
            "food": food_cost,
            "activities": activities_cost,
            "miscellaneous_buffer": misc,
            "estimated_total": total,
            "user_budget": user_budget,
            "within_budget": (total <= user_budget) if user_budget > 0 else True,
            "remaining_budget": round(user_budget - total, 2) if user_budget > 0 else 0,
        }, indent=2)
    except Exception as exc:
        return f"Budget calculation failed: {exc}"


# List of all available travel tools
ALL_TRAVEL_TOOLS = [
    search_flights,
    search_hotels,
    get_weather_forecast,
    get_destination_attractions,
    calculate_trip_budget,
]
