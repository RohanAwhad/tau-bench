#!/usr/bin/env python3
"""
MCP Server for Airline Tools using FastMCP with SSE (Server-Sent Events)

This server exposes all airline tools from tau-bench as MCP tools.
Run with: python airline_tools_mcp.py
MCP URL: http://localhost:8000/sse
Reload endpoint: POST http://localhost:8000/reload
"""

import logging
import json
from typing import Any, Dict, List

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
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
from tau_bench.envs.base import consistent_hash, to_hashable

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


def _format_tool_description(tool_class) -> str:
    """Create a rich tool description using the tool's get_info metadata."""
    info = tool_class.get_info().get("function", {})
    description = info.get("description", "").strip()
    properties = info.get("parameters", {}).get("properties", {})

    lines: List[str] = []
    if description:
        lines.append(description)

    if properties:
        if lines:
            lines.append("")
        lines.append("Parameters:")

        for name, schema in properties.items():
            param_type = schema.get("type")
            details: List[str] = []
            if param_type:
                details.append(param_type)

            if param_type == "array":
                item_schema = schema.get("items", {})
                item_type = item_schema.get("type")
                if item_type:
                    details.append(f"items: {item_type}")

            enum_values = schema.get("enum")
            if enum_values:
                formatted_enum = ", ".join(str(value) for value in enum_values)
                details.append(f"options: {formatted_enum}")

            detail_suffix = f" ({', '.join(details)})" if details else ""
            param_description = schema.get("description", "").strip()
            if param_description:
                lines.append(f"- {name}{detail_suffix}: {param_description}")
            else:
                lines.append(f"- {name}{detail_suffix}")

    return "\n".join(lines)


BOOK_RESERVATION_DESCRIPTION = _format_tool_description(BookReservation)
CALCULATE_DESCRIPTION = _format_tool_description(Calculate)
CANCEL_RESERVATION_DESCRIPTION = _format_tool_description(CancelReservation)
GET_RESERVATION_DETAILS_DESCRIPTION = _format_tool_description(GetReservationDetails)
GET_USER_DETAILS_DESCRIPTION = _format_tool_description(GetUserDetails)
LIST_ALL_AIRPORTS_DESCRIPTION = _format_tool_description(ListAllAirports)
SEARCH_DIRECT_FLIGHT_DESCRIPTION = _format_tool_description(SearchDirectFlight)
SEARCH_ONESTOP_FLIGHT_DESCRIPTION = _format_tool_description(SearchOnestopFlight)
SEND_CERTIFICATE_DESCRIPTION = _format_tool_description(SendCertificate)
THINK_DESCRIPTION = _format_tool_description(Think)
TRANSFER_TO_HUMAN_AGENTS_DESCRIPTION = _format_tool_description(TransferToHumanAgents)
UPDATE_RESERVATION_BAGGAGES_DESCRIPTION = _format_tool_description(UpdateReservationBaggages)
UPDATE_RESERVATION_FLIGHTS_DESCRIPTION = _format_tool_description(UpdateReservationFlights)
UPDATE_RESERVATION_PASSENGERS_DESCRIPTION = _format_tool_description(UpdateReservationPassengers)


def get_database_hash() -> str:
    """Compute the current hash of the in-memory airline database."""
    return consistent_hash(to_hashable(airline_data))


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


async def hash_endpoint(request: Request):
    """REST endpoint to get the current database hash."""
    db_hash = get_database_hash()
    logger.info("Computed database hash via /hash endpoint: %s", db_hash)
    return JSONResponse({
        "status": "success",
        "hash": db_hash,
    })


@mcp.tool(description=BOOK_RESERVATION_DESCRIPTION)
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


book_reservation.__doc__ = BOOK_RESERVATION_DESCRIPTION


@mcp.tool(description=CALCULATE_DESCRIPTION)
def calculate(operation: str) -> str:
    """Perform a calculation."""
    return Calculate.invoke(airline_data, operation)


calculate.__doc__ = CALCULATE_DESCRIPTION


@mcp.tool(description=CANCEL_RESERVATION_DESCRIPTION)
def cancel_reservation(reservation_id: str) -> str:
    """Cancel a reservation."""
    return CancelReservation.invoke(airline_data, reservation_id)


cancel_reservation.__doc__ = CANCEL_RESERVATION_DESCRIPTION


@mcp.tool(description=GET_RESERVATION_DETAILS_DESCRIPTION)
def get_reservation_details(reservation_id: str) -> str:
    """Get the details of a reservation."""
    return GetReservationDetails.invoke(airline_data, reservation_id)


get_reservation_details.__doc__ = GET_RESERVATION_DETAILS_DESCRIPTION


@mcp.tool(description=GET_USER_DETAILS_DESCRIPTION)
def get_user_details(user_id: str) -> str:
    """Get the details of a user, including their reservations."""
    return GetUserDetails.invoke(airline_data, user_id)


get_user_details.__doc__ = GET_USER_DETAILS_DESCRIPTION


@mcp.tool(description=LIST_ALL_AIRPORTS_DESCRIPTION)
def list_all_airports() -> str:
    """List all airports."""
    return ListAllAirports.invoke(airline_data)


list_all_airports.__doc__ = LIST_ALL_AIRPORTS_DESCRIPTION


@mcp.tool(description=SEARCH_DIRECT_FLIGHT_DESCRIPTION)
def search_direct_flight(origin: str, destination: str, date: str) -> str:
    """Search direct flights between two cities on a specific date."""
    return SearchDirectFlight.invoke(airline_data, origin, destination, date)


search_direct_flight.__doc__ = SEARCH_DIRECT_FLIGHT_DESCRIPTION


@mcp.tool(description=SEARCH_ONESTOP_FLIGHT_DESCRIPTION)
def search_onestop_flight(origin: str, destination: str, date: str) -> str:
    """Search one-stop flights between two cities on a specific date."""
    return SearchOnestopFlight.invoke(airline_data, origin, destination, date)


search_onestop_flight.__doc__ = SEARCH_ONESTOP_FLIGHT_DESCRIPTION


@mcp.tool(description=SEND_CERTIFICATE_DESCRIPTION)
def send_certificate(user_id: str, amount: int) -> str:
    """Send a certificate to a user."""
    return SendCertificate.invoke(airline_data, user_id, amount)


send_certificate.__doc__ = SEND_CERTIFICATE_DESCRIPTION


@mcp.tool(description=THINK_DESCRIPTION)
def think(thought: str) -> str:
    """Think about something (internal reasoning)."""
    return Think.invoke(airline_data, thought)


think.__doc__ = THINK_DESCRIPTION


@mcp.tool(description=TRANSFER_TO_HUMAN_AGENTS_DESCRIPTION)
def transfer_to_human_agents(summary: str) -> str:
    """Transfer to human agents."""
    return TransferToHumanAgents.invoke(airline_data, summary)


transfer_to_human_agents.__doc__ = TRANSFER_TO_HUMAN_AGENTS_DESCRIPTION


@mcp.tool(description=UPDATE_RESERVATION_BAGGAGES_DESCRIPTION)
def update_reservation_baggages(
    reservation_id: str,
    total_baggages: int,
    nonfree_baggages: int,
) -> str:
    """Update the baggage information of a reservation."""
    return UpdateReservationBaggages.invoke(
        airline_data, reservation_id, total_baggages, nonfree_baggages
    )


update_reservation_baggages.__doc__ = UPDATE_RESERVATION_BAGGAGES_DESCRIPTION


@mcp.tool(description=UPDATE_RESERVATION_FLIGHTS_DESCRIPTION)
def update_reservation_flights(
    reservation_id: str,
    flights: List[Dict[str, Any]],
) -> str:
    """Update the flights of a reservation."""
    return UpdateReservationFlights.invoke(airline_data, reservation_id, flights)


update_reservation_flights.__doc__ = UPDATE_RESERVATION_FLIGHTS_DESCRIPTION


@mcp.tool(description=UPDATE_RESERVATION_PASSENGERS_DESCRIPTION)
def update_reservation_passengers(
    reservation_id: str,
    passengers: List[Dict[str, Any]],
) -> str:
    """Update the passengers of a reservation."""
    return UpdateReservationPassengers.invoke(airline_data, reservation_id, passengers)


update_reservation_passengers.__doc__ = UPDATE_RESERVATION_PASSENGERS_DESCRIPTION


def run_hash_smoke_test() -> None:
    """CLI helper to verify reload and hash behavior."""
    logger.info("Running database reload/hash smoke test")

    reload_database()
    baseline_hash = get_database_hash()
    logger.info("Baseline database hash: %s", baseline_hash)

    reload_database()
    post_reload_hash = get_database_hash()
    if post_reload_hash != baseline_hash:
        raise RuntimeError(
            f"Reload hash mismatch: {post_reload_hash} (expected {baseline_hash})"
        )
    logger.info("Reload hash matches baseline: %s", post_reload_hash)

    certificate_result = SendCertificate.invoke(airline_data, "mia_li_3668", 42)
    logger.info("send_certificate result: %s", certificate_result.strip())
    if not certificate_result.lower().startswith("certificate"):
        raise RuntimeError(f"send_certificate failed: {certificate_result}")

    flight_entry = airline_data["flights"]["HAT001"]["dates"]["2024-05-16"]
    if flight_entry["status"] != "available":
        raise RuntimeError("Expected HAT001 on 2024-05-16 to be available for booking")
    payment_amount = flight_entry["prices"]["economy"]

    booking_result = BookReservation.invoke(
        airline_data,
        user_id="mia_li_3668",
        origin="PHL",
        destination="LGA",
        flight_type="one_way",
        cabin="economy",
        flights=[{"flight_number": "HAT001", "date": "2024-05-16"}],
        passengers=[
            {"first_name": "Mia", "last_name": "Li", "dob": "1990-04-05"},
        ],
        payment_methods=[{"payment_id": "credit_card_1955700", "amount": payment_amount}],
        total_baggages=0,
        nonfree_baggages=0,
        insurance="no",
    )
    try:
        booking_payload = json.loads(booking_result)
    except json.JSONDecodeError as exc:  # pragma: no cover - sanity guard
        raise RuntimeError(f"Book reservation failed: {booking_result}") from exc

    new_reservation_id = booking_payload["reservation_id"]
    logger.info("Booked reservation %s via smoke test", new_reservation_id)

    mutated_hash = get_database_hash()
    if mutated_hash == baseline_hash:
        raise RuntimeError(
            "Database hash unchanged after mutations; expected difference"
        )
    logger.info("Hash after tool mutations: %s", mutated_hash)

    reload_database()
    final_hash = get_database_hash()
    if final_hash != baseline_hash:
        raise RuntimeError(
            f"Database did not reset cleanly: {final_hash} (expected {baseline_hash})"
        )
    logger.info("Reload restored baseline hash: %s", final_hash)


async def run_reload_server():
    """Run the reload endpoint on a separate port."""
    reload_app = Starlette(
        routes=[
            Route("/reload", reload_endpoint, methods=["POST", "GET"]),
            Route("/hash", hash_endpoint, methods=["GET"]),
        ]
    )
    config = uvicorn.Config(reload_app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def start_server() -> None:
    import asyncio
    import threading

    logger.info("Starting Airline Tools MCP Server with SSE")
    logger.info("MCP endpoint: http://localhost:8000/sse")
    logger.info("Reload endpoint: POST http://localhost:8001/reload")
    logger.info("Hash endpoint: GET http://localhost:8001/hash")

    # Start the reload server in a separate thread
    def start_reload_server():
        asyncio.run(run_reload_server())

    reload_thread = threading.Thread(target=start_reload_server, daemon=True)
    reload_thread.start()

    # Run the MCP server on port 8000
    mcp.run(transport="sse", port=8000)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Airline MCP server controls")
    parser.add_argument(
        "--test-reload-hash",
        action="store_true",
        help="Run a smoke test that exercises reload and hash operations.",
    )
    args = parser.parse_args()

    if args.test_reload_hash:
        run_hash_smoke_test()
    else:
        start_server()
