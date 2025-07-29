"""List blueprints tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_list_blueprints(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the list_blueprints tool call."""
    try:
        logger.info("📋 Fetching blueprints from Apstra API...")
        
        # Make API call to list blueprints
        blueprints_data = make_apstra_api_call("/api/blueprints")
        
        logger.info(f"✅ Retrieved {len(blueprints_data) if isinstance(blueprints_data, list) else 'unknown number of'} blueprints")
        
        # Format the response as JSON
        result = format_blueprints_json(blueprints_data)
        
        logger.info("📄 Blueprint JSON formatted successfully")
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error listing blueprints: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_blueprints_json(blueprints_data):
    """Format blueprint data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as two separate markdown tables.
    """
    import json
    
    if isinstance(blueprints_data, dict) and 'items' in blueprints_data:
        blueprints = blueprints_data['items']
        if blueprints:
            # Build structured JSON output with requested fields
            formatted_blueprints = []
            formatted_anomalies = []
            
            for blueprint in blueprints:
                # Extract anomaly counts
                anomaly_counts = blueprint.get('anomaly_counts', {})
                
                blueprint_json = {
                    # Basic blueprint information only
                    "NAME": blueprint.get('label', 'N/A'),
                    "ID": blueprint.get('id', 'N/A'),
                    "SPINES": blueprint.get('spine_count', 0),
                    "LEAFS": blueprint.get('leaf_count', 0),
                    "GENERIC_SYSTEMS": blueprint.get('generic_count', 0),
                    "VIRTUAL_NETWORKS": blueprint.get('virtual_network_count', 0),
                    "SECURITY_ZONES": blueprint.get('security_zone_count', 0),
                    "MODIFIED_AT": blueprint.get('last_modified_at', 'N/A'),
                    "BUILD_ERRORS": blueprint.get('build_errors_count', 0)
                }
                
                # Separate anomaly data
                anomaly_json = {
                    "BLUEPRINT_NAME": blueprint.get('label', 'N/A'),
                    "BLUEPRINT_ID": blueprint.get('id', 'N/A'),
                    "ARP": anomaly_counts.get('arp', 0),
                    "MLAG": anomaly_counts.get('mlag', 0),
                    "INTERFACE": anomaly_counts.get('interface', 0),
                    "SERIES": anomaly_counts.get('series', 0),
                    "CONFIG": anomaly_counts.get('config', 0),
                    "HOSTNAME": anomaly_counts.get('hostname', 0),
                    "ROUTE": anomaly_counts.get('route', 0),
                    "ALL": anomaly_counts.get('all', 0),
                    "BGP": anomaly_counts.get('bgp', 0),
                    "LIVENESS": anomaly_counts.get('liveness', 0),
                    "COUNTER": anomaly_counts.get('counter', 0),
                    "BLUEPRINT_RENDERING": anomaly_counts.get('blueprint_rendering', 0),
                    "PROBE": anomaly_counts.get('probe', 0),
                    "DEPLOYMENT": anomaly_counts.get('deployment', 0),
                    "CABLING": anomaly_counts.get('cabling', 0),
                    "LAG": anomaly_counts.get('lag', 0),
                    "MAC": anomaly_counts.get('mac', 0),
                    "STREAMING": anomaly_counts.get('streaming', 0)
                }
                
                formatted_blueprints.append(blueprint_json)
                formatted_anomalies.append(anomaly_json)
            
            # Create the final JSON structure with separate anomalies
            result_json = {
                "status": "success",
                "message": f"Retrieved {len(blueprints)} blueprints from Apstra",
                "blueprints": formatted_blueprints,
                "anomalies": formatted_anomalies
            }
            
            # Add table creation prompts as directives to any LLM
            table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS TWO FANCY MARKDOWN TABLES

**DIRECTIVE:** You must format the above data as TWO separate, visually appealing, and comprehensive markdown tables with enhanced styling and emojis.

🎨 **VISUAL REQUIREMENTS:** Create professional, eye-catching tables with extensive use of emojis, proper alignment, and decorative elements.

### TABLE 1: BLUEPRINT INFRASTRUCTURE

Create a markdown table with the following columns from the "blueprints" JSON:
- Blueprint Name
- Spines
- Leafs  
- Generic Systems
- Virtual Networks
- Security Zones
- Build Errors
- Last Modified

### TABLE 2: ANOMALY ANALYSIS

Create a separate markdown table with the following columns from the "anomalies" JSON:
- Blueprint Name
- Only include anomaly type columns that have non-zero counts in at least one blueprint (ARP, MLAG, INTERFACE, CONFIG, HOSTNAME, ROUTE, BGP, DEPLOYMENT, CABLING, etc.)
- Total Anomalies
- Health Status

**IMPORTANT:** Skip/exclude any anomaly type columns where ALL blueprints have zero count for that anomaly type.

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy table headers with alignment and use **bold** headers
3. Add summary sections below each table with statistics and insights
4. Use emojis extensively for visual appeal:
   - Health status in anomaly table (🟢 Good, 🟡 Warning, 🔴 Critical)
   - Infrastructure icons (🏗️ Spines, 🌿 Leafs, 🖥️ Systems, 🌐 Networks, 🔒 Security Zones)
   - Status indicators (✅ No errors, ⚠️ Build errors, 📅 Last modified)
5. Calculate health status based on total anomaly counts:
   - 🟢 Good: Total anomalies ≤ 5
   - 🟡 Warning: Total anomalies 6-15
   - 🔴 Critical: Total anomalies > 15
6. Calculate total anomalies by summing all anomaly types except "ALL"
7. **CRITICAL:** In the anomaly table, only include columns for anomaly types that have at least one non-zero value across all blueprints. Skip columns where all blueprints show 0 for that anomaly type.
8. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort anomaly table by total anomalies (highest first) with health status indicators
- Add totals row at the bottom of each table with summary calculations
- Include top 3 anomaly types summary for critical blueprints with 🔥 indicators
- Format dates as readable timestamps (e.g., "2 hours ago", "Jan 28, 2025")
- Highlight blueprints with >0 build errors using ⚠️ symbols
- Use alternating visual emphasis (bold names for critical systems)
- Add section dividers with decorative lines (═══, ───, •••)
- Include percentage calculations where relevant (e.g., "30% of total anomalies")
- Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info
- Add network topology hints using connection symbols (⟷, ↔️, 🔗)

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for blueprint names and important values
- Use *italics* for secondary information
- Add horizontal rules (---) between major sections
- Include table captions with descriptive titles
- Use consistent spacing and alignment for professional appearance

**YOU MUST RESPOND WITH BOTH FANCY STYLED MARKDOWN TABLES IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the tables visually stunning with emojis, proper formatting, and professional styling!

---
"""
            
            return json.dumps(result_json, indent=2) + table_prompt
        else:
            # No blueprints found
            return json.dumps({
                "status": "no_data",
                "message": "No blueprints found in the system",
                "total_blueprints": 0,
                "blueprints": [],
                "anomalies": []
            }, indent=2)
    else:
        # If the response format is different, return raw JSON with error status
        return json.dumps({
            "status": "error",
            "message": "Unexpected data format from Apstra API",
            "raw_data": blueprints_data
        }, indent=2)
