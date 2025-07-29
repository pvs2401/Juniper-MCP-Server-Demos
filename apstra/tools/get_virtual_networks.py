"""Get virtual networks tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_virtual_networks(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the virtual_networks tool call."""
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not blueprint_id:
        error_msg = "Blueprint ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔍 Fetching virtual networks for blueprint: {blueprint_id}")
        
        # First, get the list of blueprints to find the correct ID
        blueprints_data = make_apstra_api_call("/api/blueprints")
        blueprint_info = None
        
        if isinstance(blueprints_data, dict) and 'items' in blueprints_data:
            for bp in blueprints_data['items']:
                if (bp.get('id') == blueprint_id or 
                    bp.get('label', '').lower() == blueprint_id.lower()):
                    blueprint_info = bp
                    break
        
        if not blueprint_info:
            error_msg = f"Blueprint '{blueprint_id}' not found"
            logger.error(f"❌ {error_msg}")
            return [TextContent(type="text", text=error_msg)]
        
        # Get virtual networks from the correct endpoint
        bp_id = blueprint_info['id']
        logger.info(f"📡 Getting virtual networks for blueprint ID: {bp_id}")
        # Use the Apstra API endpoint for virtual networks
        vn_response = make_apstra_api_call(f"/api/blueprints/{bp_id}/virtual-networks")
        
        # Extract virtual networks data from the response
        vn_data = {"virtual_networks": {}}
        if isinstance(vn_response, dict) and 'virtual_networks' in vn_response:
            vn_data = vn_response
        
        # Format the virtual networks details as JSON
        result = format_virtual_networks_json(vn_data, blueprint_info.get('label', blueprint_id))
        
        logger.info(f"✅ Virtual networks retrieved for blueprint: {blueprint_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting virtual networks: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_virtual_networks_json(vn_data, blueprint_name):
    """Format virtual networks data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as a comprehensive markdown table.
    """
    import json
    
    if isinstance(vn_data, dict) and 'virtual_networks' in vn_data:
        virtual_networks = vn_data['virtual_networks']
        if virtual_networks:
            # Build structured JSON output with requested fields
            formatted_vns = []
            
            for vn_id, vn_data in virtual_networks.items():
                # Extract tags as comma-separated string
                tags_str = ', '.join(vn_data.get('tags', [])) if vn_data.get('tags') else 'None'
                
                vn_json = {
                    # Field mapping based on provided schema
                    "NAME": vn_data.get('label', 'N/A'),
                    "ID": vn_data.get('id', 'N/A'),
                    "IPV4_CIDR": vn_data.get('ipv4_subnet', 'N/A'),
                    "IPV4_ANYCAST_GW": vn_data.get('virtual_gateway_ipv4', 'N/A'),
                    "IPV6_CIDR": vn_data.get('ipv6_subnet', 'N/A'),
                    "IPV6_ANYCAST_GW": vn_data.get('virtual_gateway_ipv6', 'N/A'),
                    "VXLAN_VNID": vn_data.get('vn_id', 'N/A'),
                    "VRF_TARGET": vn_data.get('route_target', 'N/A'),
                    "MTU": vn_data.get('l3_mtu', 'N/A'),
                    "VLAN_ID": vn_data.get('reserved_vlan_id', 'N/A'),
                    "TAGS": tags_str
                }
                
                formatted_vns.append(vn_json)
            
            # Create the final JSON structure
            result_json = {
                "status": "success",
                "message": f"Retrieved {len(virtual_networks)} virtual networks from blueprint '{blueprint_name}'",
                "blueprint_name": blueprint_name,
                "total_virtual_networks": len(virtual_networks),
                "virtual_networks": formatted_vns
            }
            
            # Add table creation prompt as directive to any LLM
            table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS FANCY VIRTUAL NETWORKS TABLE

**DIRECTIVE:** You must format the above virtual networks data as a comprehensive, visually appealing markdown table.

🎨 **VISUAL REQUIREMENTS:** Create a professional, eye-catching table with extensive use of emojis, proper alignment, and decorative elements.

### VIRTUAL NETWORKS TABLE

Create a markdown table with the following columns from the "virtual_networks" JSON:
- Network Name
- ID
- IPv4 CIDR
- IPv4 Anycast GW
- IPv6 CIDR
- IPv6 Anycast GW
- VXLAN VNID
- VRF Target
- MTU
- VLAN ID
- Tags

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy table headers with alignment and use **bold** headers
3. Add summary sections below the table with statistics and insights
4. Use emojis extensively for visual appeal:
   - Network icons (🌐 Networks, 🔗 VLAN, 📡 VXLAN, 🏷️ VRF)
   - Protocol indicators (🌍 IPv4, 🌎 IPv6, 🚪 Gateway)
   - Status indicators (✅ Active, ⚠️ Warning, 📏 MTU)
5. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis
6. Group networks by VLAN ID or subnet for better organization
7. Format IP addresses and CIDR consistently
8. Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort table by VLAN ID or network name for logical grouping
- Add totals row at the bottom with summary statistics
- Include IPv4/IPv6 distribution summary
- Format IP addresses with proper CIDR notation
- Highlight different VRF targets using appropriate emojis
- Use alternating visual emphasis (bold names for primary networks)
- Add section dividers with decorative lines (═══, ───, •••)
- Include network statistics (e.g., "5 IPv4 networks, 2 IPv6 enabled")

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for network names and important values
- Use *italics* for secondary information like VRF targets
- Add horizontal rules (---) between major sections
- Include table captions with descriptive titles
- Use consistent spacing and alignment for professional appearance
- Add network topology context where relevant

**YOU MUST RESPOND WITH A FANCY STYLED MARKDOWN TABLE IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the table visually stunning with emojis, proper formatting, and professional styling!

---
"""
            
            return json.dumps(result_json, indent=2) + table_prompt
        else:
            # No virtual networks found
            return json.dumps({
                "status": "no_data",
                "message": f"No virtual networks found in blueprint '{blueprint_name}'",
                "blueprint_name": blueprint_name,
                "total_virtual_networks": 0,
                "virtual_networks": []
            }, indent=2)
    else:
        # If the response format is different, return raw JSON with error status
        return json.dumps({
            "status": "error",
            "message": "Unexpected data format from Apstra API",
            "raw_data": vn_data
        }, indent=2)
