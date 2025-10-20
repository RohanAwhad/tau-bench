#!/usr/bin/env python3
"""
MCP Server for Airline Tools using FastMCP with SSE (Server-Sent Events)

This server exposes all airline tools from tau-bench as MCP tools.
Run with: python airline_tools_mcp.py
Access at: http://localhost:8000/sse
"""

import logging
from typing import Any, Dict, List

from fastmcp import FastMCP

from tau_bench.envs.airline.data import load_data
from tau_bench.envs.airline.tools import (
    BookReservation,
    Calculate,
    CancelReservation,
    GetReservationDetails,
    GetUserDetails,
    ListAllAirports,
    SearchDirectFlight,
    SearchOnestopFlight,
    SendCertificate,
    Think,
    TransferToHumanAgents,
    UpdateReservationBaggages,
    UpdateReservationFlights,
    UpdateReservationPassengers,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airline-tools-mcp")

# Create FastMCP server
mcp = FastMCP("Airline Tools")

# Load airline data globally
logger.info("Loading airline data...")
airline_data = load_data()
logger.info(f"Loaded {len(airline_data.get('flights', {}))} flights, "
            f"{len(airline_data.get('reservations', {}))} reservations, "
            f"{len(airline_data.get('users', {}))} users")


@mcp.tool()
def book_reservation(
    user_id: str,
    origin: str,
    destination: str,
    flight_type: str,
    cabin: str,
    flights: List[Dict[str, Any]],
    passengers: List[Dict[str, Any]],
    payment_methods: List[Dict[str, Any]],
    total_baggages: int,
    nonfree_baggages: int,
    insurance: str,
) -> str:
    """Book a reservation."""
    return BookReservation.invoke(
        airline_data,
        user_id,
        origin,
        destination,
        flight_type,
        cabin,
        flights,
        passengers,
        payment_methods,
        total_baggages,
        nonfree_baggages,
        insurance,
    )


@mcp.tool()
def calculate(operation: str) -> str:
    """Perform a calculation."""
    return Calculate.invoke(airline_data, operation)


@mcp.tool()
def cancel_reservation(reservation_id: str) -> str:
    """Cancel a reservation."""
    return CancelReservation.invoke(airline_data, reservation_id)


@mcp.tool()
def get_reservation_details(reservation_id: str) -> str:
    """Get the details of a reservation."""
    return GetReservationDetails.invoke(airline_data, reservation_id)


@mcp.tool()
def get_user_details(user_id: str) -> str:
    """Get the details of a user, including their reservations."""
    return GetUserDetails.invoke(airline_data, user_id)


@mcp.tool()
def list_all_airports() -> str:
    """List all airports."""
    return ListAllAirports.invoke(airline_data)


@mcp.tool()
def search_direct_flight(origin: str, destination: str, date: str) -> str:
    """Search direct flights between two cities on a specific date."""
    return SearchDirectFlight.invoke(airline_data, origin, destination, date)


@mcp.tool()
def search_onestop_flight(origin: str, destination: str, date: str) -> str:
    """Search one-stop flights between two cities on a specific date."""
    return SearchOnestopFlight.invoke(airline_data, origin, destination, date)


@mcp.tool()
def send_certificate(user_id: str, amount: int) -> str:
    """Send a certificate to a user."""
    return SendCertificate.invoke(airline_data, user_id, amount)


@mcp.tool()
def think(thought: str) -> str:
    """Think about something (internal reasoning)."""
    return Think.invoke(airline_data, thought)


@mcp.tool()
def transfer_to_human_agents(summary: str) -> str:
    """Transfer to human agents."""
    return TransferToHumanAgents.invoke(airline_data, summary)


@mcp.tool()
def update_reservation_baggages(
    reservation_id: str,
    total_baggages: int,
    nonfree_baggages: int,
) -> str:
    """Update the baggage information of a reservation."""
    return UpdateReservationBaggages.invoke(
        airline_data, reservation_id, total_baggages, nonfree_baggages
    )


@mcp.tool()
def update_reservation_flights(
    reservation_id: str,
    flights: List[Dict[str, Any]],
) -> str:
    """Update the flights of a reservation."""
    return UpdateReservationFlights.invoke(airline_data, reservation_id, flights)


@mcp.tool()
def update_reservation_passengers(
    reservation_id: str,
    passengers: List[Dict[str, Any]],
) -> str:
    """Update the passengers of a reservation."""
    return UpdateReservationPassengers.invoke(airline_data, reservation_id, passengers)


if __name__ == "__main__":
    logger.info("Starting Airline Tools MCP Server with SSE on http://localhost:8000/sse")
    # Run with HTTP/SSE transport
    mcp.run(transport="sse")
