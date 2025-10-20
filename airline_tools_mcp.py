#!/usr/bin/env python3
"""
MCP Server for Airline Tools using SSE (Server-Sent Events)

This server exposes all airline tools from tau-bench as MCP tools.
"""

import asyncio
import json
import logging
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

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

# Create the MCP server
server = Server("airline-tools")

# Global data storage
airline_data: dict[str, Any] = {}

# Map of tool names to tool classes
TOOL_MAP = {
    "book_reservation": BookReservation,
    "calculate": Calculate,
    "cancel_reservation": CancelReservation,
    "get_reservation_details": GetReservationDetails,
    "get_user_details": GetUserDetails,
    "list_all_airports": ListAllAirports,
    "search_direct_flight": SearchDirectFlight,
    "search_onestop_flight": SearchOnestopFlight,
    "send_certificate": SendCertificate,
    "think": Think,
    "transfer_to_human_agents": TransferToHumanAgents,
    "update_reservation_baggages": UpdateReservationBaggages,
    "update_reservation_flights": UpdateReservationFlights,
    "update_reservation_passengers": UpdateReservationPassengers,
}


def convert_tool_info_to_mcp(tool_info: dict[str, Any]) -> Tool:
    """Convert tau-bench tool info format to MCP Tool format."""
    func_info = tool_info["function"]
    return Tool(
        name=func_info["name"],
        description=func_info["description"],
        inputSchema=func_info["parameters"],
    )


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List all available airline tools."""
    logger.info("Listing all airline tools")
    tools = []
    for tool_class in TOOL_MAP.values():
        tool_info = tool_class.get_info()
        mcp_tool = convert_tool_info_to_mcp(tool_info)
        tools.append(mcp_tool)
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls by delegating to the appropriate airline tool."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    if name not in TOOL_MAP:
        raise ValueError(f"Unknown tool: {name}")

    tool_class = TOOL_MAP[name]

    try:
        # Call the tool's invoke method with data and arguments
        result = tool_class.invoke(airline_data, **arguments)

        # Return the result as TextContent
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        error_msg = f"Error: {str(e)}"
        return [TextContent(type="text", text=error_msg)]


@server.list_resources()
async def handle_list_resources() -> list[Any]:
    """List available resources (data snapshots)."""
    return []


@server.list_prompts()
async def handle_list_prompts() -> list[Any]:
    """List available prompts."""
    return []


async def main():
    """Main entry point for the MCP server."""
    global airline_data

    # Load airline data
    logger.info("Loading airline data...")
    airline_data = load_data()
    logger.info(f"Loaded {len(airline_data.get('flights', {}))} flights, "
                f"{len(airline_data.get('reservations', {}))} reservations, "
                f"{len(airline_data.get('users', {}))} users")

    # Run the server using stdio transport
    logger.info("Starting Airline Tools MCP Server (SSE)")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="airline-tools",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
