"""Apstra MCP Server implementation for stdio mode.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.api_client import get_apstra_config
from .tools import (
    handle_list_blueprints,
    handle_get_blueprint_details,
    handle_get_system_details,
    handle_virtual_networks,
    handle_security_zones,
    handle_config_audits,
    handle_get_blueprint_anomalies,
    handle_apply_system_golden_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("apstra")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Apstra tools with comprehensive descriptions for LLM."""
    return [
        Tool(
            name="list_blueprints",
            description=(
                "List all Apstra blueprints with their name, design type, status, and infrastructure counts "
                "(leaf/spine switches, gateways, security zones, virtual networks). "
                "Returns a formatted table with suggestions for next actions."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_blueprint_details",
            description=(
                "Get detailed information about a specific Apstra blueprint. "
                "Accepts blueprint ID or name. Returns comprehensive report with: "
                "basic info, infrastructure summary, virtual networks table, systems table, and security zones table. "
                "Use for blueprint configuration review and network topology analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "The ID or name/label of the blueprint to get details for. Can be the exact blueprint ID (UUID) or the human-readable blueprint label/name."
                    }
                },
                "required": ["blueprint_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_system_details",
            description=(
                "Get comprehensive system details for all network devices in a specific Apstra blueprint. "
                "Accepts blueprint ID or name. Returns structured JSON with system identification, "
                "network configuration (device role, loopback address, eBGP ASN, anycast VTEP), "
                "and management info, followed by LLM instructions for fancy markdown table formatting. "
                "Use for device inventory management and network topology analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "The ID or name/label of the blueprint to get system details for. Can be the exact blueprint ID (UUID) or the human-readable blueprint label/name."
                    }
                },
                "required": ["blueprint_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_virtual_networks",
            description=(
                "Get comprehensive virtual networks information for a specific Apstra blueprint. "
                "Accepts blueprint ID or name. Returns structured JSON with network details including "
                "IPv4/IPv6 CIDR, anycast gateways, VXLAN VNID, VRF targets, MTU, VLAN ID, and tags, "
                "followed by LLM instructions for fancy markdown table formatting. "
                "Use for network configuration review and VLAN/VXLAN analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "The ID or name/label of the blueprint to get virtual networks for. Can be the exact blueprint ID (UUID) or the human-readable blueprint label/name."
                    }
                },
                "required": ["blueprint_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_security_zones",
            description=(
                "Get comprehensive security zones information for a specific Apstra blueprint using /api/blueprints/{bp_id}/security-zones. "
                "Accepts blueprint ID or name. Returns structured JSON with zone details including "
                "zone ID, zone type, EVPN VRF, VRF targets, VXLAN VNID, MTU, VLAN ID, routing policies, and tags, "
                "followed by LLM instructions for fancy markdown table formatting. "
                "Every Apstra blueprint has at least one default security zone. "
                "Security zones provide L3 network segmentation and tenant isolation in multi-tenant networks. "
                "Use for security zone configuration review and VRF/VLAN analysis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "The ID or name/label of the blueprint to get security zones for. Can be the exact blueprint ID (UUID) or the human-readable blueprint label/name. Returns full list of security zones with their IDs."
                    }
                },
                "required": ["blueprint_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_config_audits",
            description=(
                "Get comprehensive configuration audit information for a specific Apstra blueprint. "
                "Accepts blueprint ID or name. Returns structured JSON with configuration mismatches, "
                "device deployment status, error messages, and deployment statistics, "
                "followed by LLM instructions for fancy markdown table formatting. "
                "Shows system IDs that should be mapped to hostnames using get_system_details tool. "
                "Use for configuration compliance monitoring, deployment tracking, and troubleshooting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_id": {
                        "type": "string",
                        "description": "The ID or name/label of the blueprint to get configuration audits for. Can be the exact blueprint ID (UUID) or the human-readable blueprint label/name. Note: System IDs in results should be mapped to hostnames using get_system_details for better readability."
                    }
                },
                "required": ["blueprint_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_blueprint_anomalies",
            description=(
                "Get detailed anomalies information for a specific system or entire blueprint in Apstra. "
                "Accepts either system_id OR blueprint_id and returns structured JSON with ALL anomalies grouped by type "
                "(BGP, route, config drift or deviation, interface, etc.). For config anomalies, provides Unix-style "
                "diff showing configuration changes. Shows complete anomaly picture across all affected systems. "
                "IMPORTANT: For route anomalies like 0.0.0.0/0 or specific routes affecting multiple systems, "
                "use blueprint_id to see the complete scope across all nodes. Each anomaly type gets custom table formatting "
                "with type-specific technical details, severity indicators, and system correlation. "
                "Use for comprehensive anomaly analysis and troubleshooting across single systems or entire blueprints."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "The system ID to get anomalies for. This should be the exact system ID (e.g., '005056013306') as returned by other system queries. Use this for single-system anomaly analysis."
                    },
                    "blueprint_id": {
                        "type": "string",
                        "description": "The blueprint ID to get all anomalies for. Use this to see anomalies across all systems in a blueprint, especially useful for route anomalies affecting multiple nodes."
                    }
                },
                "oneOf": [
                    {"required": ["system_id"]},
                    {"required": ["blueprint_id"]}
                ],
                "additionalProperties": False
            }
        ),
        Tool(
            name="apply_system_golden_config",
            description=(
                "Apply golden configuration to a system that has configuration anomalies. "
                "Shows configuration diff and requires explicit confirmation before applying changes. "
                "Provides pre-application diff display, confirmation workflow, and post-application status. "
                "Returns structured JSON with application status and next steps. "
                "IMPORTANT: Use 'confirmation=yes' parameter to actually apply the config after reviewing the diff. "
                "Use for configuration drift remediation and compliance enforcement."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "system_id": {
                        "type": "string",
                        "description": "The system ID to apply golden config to. This should be the exact system ID (e.g., '005056013306') as returned by other system queries."
                    },
                    "confirmation": {
                        "type": "string",
                        "description": "Confirmation to proceed with config application. Use 'yes', 'confirm', or 'apply' to proceed after reviewing the configuration diff. Leave empty or use 'no' to just show the diff without applying."
                    }
                },
                "required": ["system_id"],
                "additionalProperties": False
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls by dispatching to appropriate tool modules."""
    logger.info(f"🔧 Tool called: {name} with arguments: {arguments}")
    
    # Tool dispatch mapping
    tool_handlers = {
        "list_blueprints": handle_list_blueprints,
        "get_blueprint_details": handle_get_blueprint_details,
        "get_system_details": handle_get_system_details,
        "get_virtual_networks": handle_virtual_networks,
        "get_security_zones": handle_security_zones,
        "get_config_audits": handle_config_audits,
        "get_blueprint_anomalies": handle_get_blueprint_anomalies,
        "apply_system_golden_config": handle_apply_system_golden_config
    }
    
    # Get the appropriate handler
    handler = tool_handlers.get(name)
    if not handler:
        error_msg = f"Unknown tool: {name}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Call the handler
    try:
        logger.info(f"📨 Dispatching to {handler.__name__}")
        result = await handler(arguments)
        logger.info(f"✅ Tool {name} completed successfully")
        return result
    except Exception as e:
        error_msg = f"Error in tool {name}: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


async def main():
    """Main entry point for the Apstra MCP server in stdio mode."""
    logger.info("Starting Apstra MCP Server in stdio mode...")
    
    # Validate environment variables on startup
    try:
        base_url, token = get_apstra_config()
        logger.info("Apstra configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please set APSTRA_BASE_URL and APSTRA_API_TOKEN environment variables")
        return
    
    # stdio mode for Claude Desktop integration
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli():
    """CLI entry point for stdio mode only."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
