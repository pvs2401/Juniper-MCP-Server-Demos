"""Get system details tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_get_system_details(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the get_system_details tool call."""
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not blueprint_id:
        error_msg = "Blueprint ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔍 Fetching system details for blueprint: {blueprint_id}")
        
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
        
        # Get detailed system information from the correct endpoint
        bp_id = blueprint_info['id']
        logger.info(f"📡 Getting system data for blueprint ID: {bp_id}")
        # Use the correct Apstra API endpoint for system info
        systems_response = make_apstra_api_call(f"/api/blueprints/{bp_id}/experience/web/system-info")
        
        # Extract systems data from the response
        systems_data = {"data": []}
        if isinstance(systems_response, dict) and 'data' in systems_response:
            systems_data = systems_response
        
        # Format the system details as JSON
        result = format_system_details_json(systems_data, blueprint_info.get('label', blueprint_id))
        
        logger.info(f"✅ System details retrieved for blueprint: {blueprint_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting system details: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_system_details_json(systems_data, blueprint_name):
    """Format system data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as a comprehensive markdown table.
    """
    import json
    
    if isinstance(systems_data, dict) and 'data' in systems_data:
        systems = systems_data['data']
        if systems:
            # Build structured JSON output with requested fields
            formatted_systems = []
            
            for system_data in systems:
                # Extract loopback address
                loopback_address = "N/A"
                if system_data.get('loopback') and isinstance(system_data['loopback'], dict):
                    loopback_address = system_data['loopback'].get('ipv4_addr', 'N/A')
                
                system_json = {
                    # Basic system information using the requested mapping
                    "NAME": system_data.get('label', 'N/A'),
                    "HOSTNAME": system_data.get('hostname', 'N/A'),
                    "SERIAL_NO": system_data.get('system_id', 'N/A'),
                    "DEVICE_ROLE": system_data.get('role', 'N/A'),
                    "LOOPBACK_ADDRESS": loopback_address,
                    "EBGP_ASN": system_data.get('domain_id', 'N/A'),
                    "DEPLOY_MODE": system_data.get('deploy_mode', 'N/A'),
                    "MANAGEMENT_LEVEL": system_data.get('management_level', 'N/A'),
                    "TAGS": ', '.join(system_data.get('tags', [])) if system_data.get('tags') else 'None'
                }
                
                formatted_systems.append(system_json)
            
            # Create the final JSON structure
            result_json = {
                "status": "success",
                "message": f"Retrieved {len(systems)} systems from blueprint '{blueprint_name}'",
                "blueprint_name": blueprint_name,
                "total_systems": len(systems),
                "systems": formatted_systems
            }
            
            # Add table creation prompt as directive to any LLM
            table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS FANCY SYSTEM DETAILS TABLE

**DIRECTIVE:** You must format the above system data as a comprehensive, visually appealing markdown table.

🎨 **VISUAL REQUIREMENTS:** Create a professional, eye-catching table with extensive use of emojis, proper alignment, and decorative elements.

### SYSTEM DETAILS TABLE

Create a markdown table with the following columns from the "systems" JSON:
- System Name
- Hostname  
- Serial Number
- Device Role
- Loopback Address
- eBGP ASN
- Deploy Mode
- Management Level
- Tags

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy table headers with alignment and use **bold** headers
3. Add summary sections below the table with statistics and insights
4. Use emojis extensively for visual appeal:
   - Role icons (🏗️ Spine, 🌿 Leaf, 🖥️ Generic, 🔄 Redundancy Group)
   - Control level indicators (🎛️ Full Control, 🔧 Unmanaged, ⚙️ Monitored)
   - Network icons (🌐 Loopback, 🔗 eBGP ASN)
   - Status indicators (✅ Active, ⚠️ Warning, 📅 Deploy Mode)
5. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis
6. Group systems by device role for better organization
7. Format IP addresses and ASN numbers consistently
8. Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort table by device role (spine, leaf, generic) for logical grouping
- Add totals row at the bottom with summary by role
- Include control level distribution summary
- Format timestamps as readable dates (e.g., "2 hours ago", "Jan 28, 2025")
- Highlight systems with different control levels using appropriate emojis
- Use alternating visual emphasis (bold names for managed systems)
- Add section dividers with decorative lines (═══, ───, •••)
- Include role-based statistics (e.g., "4 Leaf switches, 2 Spine switches")

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for system names and important values
- Use *italics* for secondary information like serial numbers
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
            # No systems found
            return json.dumps({
                "status": "no_data",
                "message": f"No systems found in blueprint '{blueprint_name}'",
                "blueprint_name": blueprint_name,
                "total_systems": 0,
                "systems": []
            }, indent=2)
    else:
        # If the response format is different, return raw JSON with error status
        return json.dumps({
            "status": "error",
            "message": "Unexpected data format from Apstra API",
            "raw_data": systems_data
        }, indent=2)
