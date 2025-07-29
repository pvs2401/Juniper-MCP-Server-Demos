"""Get security zones tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_security_zones(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the security_zones tool call."""
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not blueprint_id:
        error_msg = "Blueprint ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔍 Fetching security zones for blueprint: {blueprint_id}")
        
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
        
        # Get security zones from the correct API endpoint: /api/blueprints/{bp_id}/security-zones
        bp_id = blueprint_info['id']
        logger.info(f"📡 Getting security zones from /api/blueprints/{bp_id}/security-zones")
        # Use the correct Apstra API endpoint for security zones
        sz_response = make_apstra_api_call(f"/api/blueprints/{bp_id}/security-zones")
        
        # Debug: Log the actual API response structure
        logger.info(f"🔍 Raw API response type: {type(sz_response)}")
        if isinstance(sz_response, dict):
            logger.info(f"🔍 API response keys: {list(sz_response.keys())}")
        
        # Handle API response properly - API returns {"items": {zone_id: zone_data}}
        if sz_response is None:
            logger.warning(f"⚠️ API returned None for security zones in blueprint: {bp_id}")
            sz_data = {"items": {}}
        elif isinstance(sz_response, dict) and 'items' in sz_response:
            # API response has the correct structure already
            sz_data = sz_response
            zone_count = len(sz_response.get('items', {}))
            logger.info(f"📊 Found {zone_count} security zones in API response")
        elif isinstance(sz_response, dict):
            # Fallback: if API returns direct zone mapping (unexpected but handle it)
            sz_data = {"items": sz_response}
            logger.info(f"📊 Found {len(sz_response)} security zones (direct format)")
        else:
            logger.warning(f"⚠️ Unexpected API response type for security zones: {type(sz_response)}")
            sz_data = {"items": {}}
        
        # Format the security zones details as JSON
        result = format_security_zones_json(sz_data, blueprint_info.get('label', blueprint_id))
        
        logger.info(f"✅ Security zones retrieved for blueprint: {blueprint_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting security zones: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_security_zones_json(sz_data, blueprint_name):
    """Format security zones data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as a comprehensive markdown table.
    """
    import json
    
    if isinstance(sz_data, dict) and 'items' in sz_data:
        security_zones = sz_data['items']
        if security_zones:
            # Build structured JSON output with requested fields
            formatted_szs = []
            
            for sz_id, sz_data in security_zones.items():
                # Extract tags as comma-separated string
                tags_str = ', '.join(sz_data.get('tags', [])) if sz_data.get('tags') else 'None'
                
                # Handle route target - prefer route_target, fallback to rt_policy
                route_target = sz_data.get('route_target')
                if not route_target and isinstance(sz_data.get('rt_policy'), dict):
                    route_target = sz_data.get('rt_policy', {}).get('export_rt')
                route_target = route_target or 'N/A'
                
                sz_json = {
                    # Field mapping based on actual Apstra security zones API response
                    "NAME": sz_data.get('label', sz_id),
                    "ID": sz_id,  # The sz_id from the API response key
                    "TYPE": sz_data.get('sz_type', 'N/A'),
                    "EVPN_VRF": sz_data.get('vrf_name', 'N/A'),
                    "VRF_TARGET": route_target,
                    "VXLAN_VNID": sz_data.get('vni_id') if sz_data.get('vni_id') is not None else 'N/A',
                    "MTU": sz_data.get('l3_mtu', 'N/A'),
                    "VLAN_ID": sz_data.get('vlan_id') if sz_data.get('vlan_id') is not None else 'N/A',
                    "TAGS": tags_str,
                    "ROUTING_POLICY": sz_data.get('routing_policy_id', 'N/A'),
                    "IMPORT_POLICY": sz_data.get('import_policy', 'N/A'),
                    "EVPN_IRB_MODE": sz_data.get('junos_evpn_irb_mode', 'N/A'),
                    "VRF_DESCRIPTION": sz_data.get('vrf_description', 'N/A'),
                    "TENANT": sz_data.get('tenant', 'N/A')
                }
                
                formatted_szs.append(sz_json)
            
            # Create the final JSON structure
            result_json = {
                "status": "success",
                "message": f"Retrieved {len(security_zones)} security zones from blueprint '{blueprint_name}'",
                "blueprint_name": blueprint_name,
                "total_security_zones": len(security_zones),
                "security_zones": formatted_szs
            }
            
            # Add table creation prompt as directive to any LLM
            table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS FANCY SECURITY ZONES TABLE

**DIRECTIVE:** You must format the above security zones data as a comprehensive, visually appealing markdown table.

🎨 **VISUAL REQUIREMENTS:** Create a professional, eye-catching table with extensive use of emojis, proper alignment, and decorative elements.

### SECURITY ZONES TABLE

Create a markdown table with the following columns from the "security_zones" JSON:
- Zone Name (NAME)
- ID
- Type (TYPE)  
- EVPN VRF
- VRF Target
- VXLAN VNID
- MTU
- VLAN ID
- Routing Policy
- Import Policy
- Tags

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy table headers with alignment and use **bold** headers
3. Add summary sections below the table with statistics and insights
4. Use emojis extensively for visual appeal:
   - Security icons (�️ Security Zones, � VRF, 🏷️ VNI, 🌐 EVPN)
   - Type indicators (� EVPN, 🏗️ L3 Fabric, 🔗 VRF, 🚪 Zone)
   - Network indicators (🌍 VNI, 🏷️ VLAN, 📏 MTU, 🎯 Target, 📋 Policy)
5. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis
6. Group zones by type (EVPN vs L3 Fabric) for better organization
7. Format VRF targets, VNI IDs, and VLAN IDs consistently
8. Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort table by zone type and then by name for logical grouping
- Add totals row at the bottom with summary statistics
- Include type distribution summary (EVPN vs L3 Fabric counts)
- Format VRF targets with proper notation
- Highlight different zone types using appropriate emojis
- Use alternating visual emphasis (bold names for primary zones)
- Add section dividers with decorative lines (═══, ───, •••)
- Include zone statistics (e.g., "2 EVPN zones, 1 L3 Fabric zone")
- Show routing and import policy information where available
- Use alternating visual emphasis (bold names for primary zones)
- Add section dividers with decorative lines (═══, ───, •••)
- Include zone statistics (e.g., "2 EVPN zones, 1 L3 Fabric zone")
- Show routing and import policy information where available

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for zone names and important values
- Use *italics* for secondary information like VRF names and policy IDs
- Add horizontal rules (---) between major sections
- Include table captions with descriptive titles
- Use consistent spacing and alignment for professional appearance
- Add security context where relevant
- Format policy information consistently (routing/import policies)
- Show VNI and VLAN relationships clearly

**YOU MUST RESPOND WITH A FANCY STYLED MARKDOWN TABLE IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the table visually stunning with emojis, proper formatting, and professional styling!

---
"""
            
            return json.dumps(result_json, indent=2) + table_prompt
        else:
            # No security zones found - this is unusual since every blueprint should have a default zone
            no_zones_json = {
                "status": "no_data",
                "message": f"No security zones found in blueprint '{blueprint_name}'. This is unusual - every Apstra blueprint should have at least one default security zone.",
                "blueprint_name": blueprint_name,
                "total_security_zones": 0,
                "security_zones": [],
                "note": "This may indicate an API access issue, blueprint corruption, or unexpected blueprint state. Check blueprint status in Apstra UI.",
                "troubleshooting": "Try using get_blueprint_details to verify blueprint health and accessibility."
            }
            
            no_zones_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT NO SECURITY ZONES MESSAGE

**DIRECTIVE:** You must format the above response as a clear informational message about the absence of security zones.

🎨 **VISUAL REQUIREMENTS:** Create a helpful, informative message explaining why no security zones were found.

### NO SECURITY ZONES MESSAGE STRUCTURE

Create an informative message with the following sections:

#### 1. 🔍 SECURITY ZONES STATUS
- Blueprint name and status
- Clear indication that no security zones are configured
- Explanation that this may be normal

#### 2. � POSSIBLE ISSUES
- API connectivity or access problems
- Blueprint in corrupted or unexpected state  
- Permissions issue accessing blueprint data
- Blueprint may be in maintenance or deployment mode

#### 3. 🔧 TROUBLESHOOTING STEPS
- Verify blueprint accessibility using get_blueprint_details tool
- Check Apstra system connectivity and authentication
- Confirm blueprint is fully deployed and operational
- Review blueprint status in Apstra UI

**FORMATTING RULES:**
1. Use informative language that doesn't suggest an error
2. Include blueprint identification prominently
3. Use info emojis: 🔍 Search, 📋 Info, 🎯 Action, 💡 Tip
4. **VISUAL ENHANCEMENT:** Use decorative elements and clear section headers
5. Professional formatting with helpful guidance

**YOU MUST RESPOND WITH A CLEAR INFORMATIONAL MESSAGE IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make it clear this is informational, not an error condition!

---
"""
            
            return json.dumps(no_zones_json, indent=2) + no_zones_prompt
    else:
        # Handle case where sz_data is not properly structured
        error_json = {
            "status": "error",
            "message": f"Invalid security zones data structure for blueprint '{blueprint_name}'",
            "blueprint_name": blueprint_name,
            "total_security_zones": 0,
            "security_zones": [],
            "error_details": "API response was not in expected format"
        }
        
        return json.dumps(error_json, indent=2)
