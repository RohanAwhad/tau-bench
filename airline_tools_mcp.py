#!/usr/bin/env python3
"""
MCP Server for Airline Tools using FastMCP with SSE (Server-Sent Events)

This server exposes all airline tools from tau-bench as MCP tools.
Run with: python airline_tools_mcp.py
MCP URL: http://localhost:8000/sse
Reload endpoint: POST http://localhost:8000/reload
"""

import logging
from typing import Any, Dict, List

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.requests import Request
import uvicorn

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

# Load airline data globally (mutable dict)
logger.info("Loading airline data...")
airline_data = load_data()
logger.info(f"Loaded {len(airline_data.get('flights', {}))} flights, "
            f"{len(airline_data.get('reservations', {}))} reservations, "
            f"{len(airline_data.get('users', {}))} users")


def reload_database():
    """Reload the airline database from source files."""
    global airline_data
    logger.info("Reloading airline database...")
    new_data = load_data()
    airline_data.clear()
    airline_data.update(new_data)
    logger.info(f"Database reloaded: {len(airline_data.get('flights', {}))} flights, "
                f"{len(airline_data.get('reservations', {}))} reservations, "
                f"{len(airline_data.get('users', {}))} users")
    return airline_data


async def reload_endpoint(request: Request):
    """REST endpoint to reload the database."""
    reload_database()
    return JSONResponse({
        "status": "success",
        "message": "Database reloaded",
        "stats": {
            "flights": len(airline_data.get('flights', {})),
            "reservations": len(airline_data.get('reservations', {})),
            "users": len(airline_data.get('users', {}))
        }
    })


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


async def run_reload_server():
    """Run the reload endpoint on a separate port."""
    reload_app = Starlette(
        routes=[
            Route("/reload", reload_endpoint, methods=["POST", "GET"]),
        ]
    )
    config = uvicorn.Config(reload_app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import asyncio
    import threading

    logger.info("Starting Airline Tools MCP Server with SSE")
    logger.info("MCP endpoint: http://localhost:8000/sse")
    logger.info("Reload endpoint: POST http://localhost:8001/reload")

    # Start the reload server in a separate thread
    def start_reload_server():
        asyncio.run(run_reload_server())

    reload_thread = threading.Thread(target=start_reload_server, daemon=True)
    reload_thread.start()

    # Run the MCP server on port 8000
    mcp.run(transport="sse", port=8000)
