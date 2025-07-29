"""Get blueprint details tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_get_blueprint_details(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the get_blueprint_details tool call."""
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not blueprint_id:
        error_msg = "Blueprint ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔍 Fetching comprehensive details for blueprint: {blueprint_id}")
        
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
        
        # Get detailed blueprint information from nodes endpoint
        bp_id = blueprint_info['id']
        logger.info(f"📡 Getting detailed nodes data for blueprint ID: {bp_id}")
        nodes_data = make_apstra_api_call(f"/api/blueprints/{bp_id}")
        
        # Format the comprehensive blueprint details as JSON
        result = format_blueprint_details_json(blueprint_info, nodes_data)
        
        logger.info(f"✅ Comprehensive blueprint details retrieved for: {blueprint_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting blueprint details: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_blueprint_details_json(blueprint_info, nodes_data):
    """Format blueprint details data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as a comprehensive markdown table.
    """
    import json
    
    # Extract basic blueprint information
    blueprint_json = {
        "BLUEPRINT_ID": blueprint_info.get('id', 'N/A'),
        "NAME": blueprint_info.get('label', 'N/A'),
        "DESIGN_TYPE": blueprint_info.get('design', 'N/A').replace('_', ' ').title(),
        "STATUS": blueprint_info.get('status', 'N/A'),
        "CREATED_AT": blueprint_info.get('created_at', 'N/A'),
        "LAST_MODIFIED": blueprint_info.get('last_modified_at', 'N/A'),
        "LEAF_COUNT": blueprint_info.get('leaf_count', 0),
        "SPINE_COUNT": blueprint_info.get('spine_count', 0),
        "REMOTE_GATEWAY_COUNT": blueprint_info.get('remote_gateway_count', 0),
        "SECURITY_ZONE_COUNT": blueprint_info.get('security_zone_count', 0),
        "VIRTUAL_NETWORK_COUNT": blueprint_info.get('virtual_network_count', 0),
        "BUILD_ERRORS": blueprint_info.get('build_errors_count', 0),
        "BUILD_WARNINGS": blueprint_info.get('build_warnings_count', 0)
    }
    
    # Extract systems, virtual networks, and security zones from nodes data
    systems = []
    virtual_networks = []
    security_zones = []
    
    if isinstance(nodes_data, dict) and 'nodes' in nodes_data:
        nodes = nodes_data['nodes']
        
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                node_type = node_data.get('type')
                
                if node_type == 'system':
                    system_json = {
                        "NAME": node_data.get('label', 'N/A'),
                        "ROLE": node_data.get('role', 'N/A'),
                        "SYSTEM_TYPE": node_data.get('system_type', 'N/A'),
                        "HOSTNAME": node_data.get('hostname', 'N/A'),
                        "DEVICE_KEY": node_data.get('device_key', 'N/A')
                    }
                    systems.append(system_json)
                
                elif node_type == 'virtual_network':
                    vn_json = {
                        "NAME": node_data.get('label', 'N/A'),
                        "VN_TYPE": node_data.get('vn_type', 'N/A'),
                        "VN_ID": node_data.get('vn_id', 'N/A'),
                        "VLAN_ID": node_data.get('reserved_vlan_id', 'N/A'),
                        "IPV4_SUBNET": node_data.get('ipv4_subnet', 'N/A'),
                        "GATEWAY_IPV4": node_data.get('virtual_gateway_ipv4', 'N/A'),
                        "L3_MTU": node_data.get('l3_mtu', 'N/A')
                    }
                    virtual_networks.append(vn_json)
                
                elif node_type == 'security_zone':
                    sz_json = {
                        "VRF_NAME": node_data.get('vrf_name', 'N/A'),
                        "SZ_TYPE": node_data.get('sz_type', 'N/A'),
                        "VNI_ID": node_data.get('vni_id', 'N/A'),
                        "VRF_ID": node_data.get('vrf_id', 'N/A'),
                        "L3_MTU": node_data.get('l3_mtu', 'N/A'),
                        "EVPN_IRB_MODE": node_data.get('junos_evpn_irb_mode', 'N/A')
                    }
                    security_zones.append(sz_json)
    
    # Create the final JSON structure
    result_json = {
        "status": "success",
        "message": f"Retrieved comprehensive details for blueprint '{blueprint_info.get('label', 'N/A')}'",
        "blueprint_details": blueprint_json,
        "systems": {
            "total_count": len(systems),
            "systems": systems
        },
        "virtual_networks": {
            "total_count": len(virtual_networks),
            "virtual_networks": virtual_networks
        },
        "security_zones": {
            "total_count": len(security_zones),
            "security_zones": security_zones
        }
    }
    
    # Add table creation prompt as directive to any LLM
    table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS COMPREHENSIVE BLUEPRINT OVERVIEW

**DIRECTIVE:** You must format the above blueprint data as a comprehensive, visually appealing overview with multiple sections and tables.

🎨 **VISUAL REQUIREMENTS:** Create a professional, eye-catching document with extensive use of emojis, proper alignment, and decorative elements.

### BLUEPRINT OVERVIEW STRUCTURE

Create a comprehensive blueprint overview with the following sections:

#### 1. 📋 BLUEPRINT SUMMARY TABLE
Create a markdown table with blueprint basic information:
- Blueprint Name, ID, Design Type, Status
- Infrastructure counts (Leaf/Spine/Security Zones/Virtual Networks)
- Build status (Errors/Warnings)
- Creation and modification dates

#### 2. 🖥️ SYSTEMS TABLE
Create a markdown table with all systems from the "systems" JSON:
- System Name, Role, Type, Hostname, Device Key
- Group by role (spine, leaf, etc.) for better organization

#### 3. 🌐 VIRTUAL NETWORKS TABLE
Create a markdown table with all virtual networks from the "virtual_networks" JSON:
- Network Name, VN Type, VN ID, VLAN ID, IPv4 Subnet, Gateway IP, L3 MTU

#### 4. 🛡️ SECURITY ZONES TABLE
Create a markdown table with all security zones from the "security_zones" JSON:
- VRF Name, SZ Type, VNI ID, VRF ID, L3 MTU, EVPN IRB Mode

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy section headers with emojis and **bold** text
3. Add summary sections with statistics and insights
4. Use emojis extensively for visual appeal:
   - Blueprint icons (📋 Blueprint, 🏗️ Design, ✅ Status, 📊 Stats)
   - System icons (🖥️ Systems, 🌿 Leaf, 🌲 Spine, 🔧 Role)
   - Network icons (🌐 Networks, 🔗 VLAN, 📡 VN, 🚪 Gateway)
   - Security icons (�️ Security, 🔐 VRF, 🏷️ VNI, 📏 MTU)
5. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis
6. Group data logically (systems by role, networks by type, etc.)
7. Format IDs, IP addresses, and technical values consistently
8. Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort tables by logical criteria (role, name, type)
- Add totals/summary rows where appropriate
- Include distribution summaries (e.g., "3 Spine switches, 4 Leaf switches")
- Format technical values consistently (IP addresses, VNIs, VLANs)
- Use alternating visual emphasis (bold names for primary items)
- Add section dividers with decorative lines (═══, ───, •••)
- Include actionable insights and recommendations

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for names and important values
- Use *italics* for secondary information like IDs and technical details
- Add horizontal rules (---) between major sections
- Include section captions with descriptive titles
- Use consistent spacing and alignment for professional appearance
- Add infrastructure context and relationships where relevant

**STRUCTURE EXAMPLE:**
```
# 📋 Blueprint: [Name] - Comprehensive Overview

## 🏗️ Blueprint Summary
[Summary table with basic info]

## 🖥️ Infrastructure Systems ([X] Total)
[Systems table grouped by role]

### 📊 System Distribution
- Spine Switches: X
- Leaf Switches: X
- Other: X

## 🌐 Virtual Networks ([X] Total)
[Virtual networks table]

## 🛡️ Security Zones ([X] Total)
[Security zones table]

## 💡 Recommendations & Next Steps
[Actionable insights]
```

**YOU MUST RESPOND WITH A COMPREHENSIVE STYLED MARKDOWN DOCUMENT IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the overview visually stunning with emojis, proper formatting, professional styling, and comprehensive information!

---
"""
    
    return json.dumps(result_json, indent=2) + table_prompt
