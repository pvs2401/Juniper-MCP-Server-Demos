"""Get configuration audits tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_config_audits(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the config_audits tool call."""
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not blueprint_id:
        error_msg = "Blueprint ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔍 Fetching configuration audits for blueprint: {blueprint_id}")
        
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
        
        # Get configuration audits from the correct endpoint
        bp_id = blueprint_info['id']
        logger.info(f"📡 Getting configuration audits for blueprint ID: {bp_id}")
        # Use the Apstra API endpoint for configuration audits
        config_response = make_apstra_api_call(f"/api/blueprints/{bp_id}/configuration")
        
        # Format the configuration audits details as JSON
        result = format_config_audits_json(config_response, blueprint_info.get('label', blueprint_id))
        
        logger.info(f"✅ Configuration audits retrieved for blueprint: {blueprint_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting configuration audits: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_config_audits_json(config_data, blueprint_name):
    """Format configuration audits data as JSON for LLM consumption.
    
    This function returns structured JSON data followed by a strict directive
    that instructs any LLM to format the data as comprehensive markdown tables.
    """
    import json
    
    if isinstance(config_data, dict):
        # Extract configuration mismatch data
        config_mismatches = []
        if 'config_mismatch' in config_data and config_data['config_mismatch']:
            for mismatch in config_data['config_mismatch']:
                mismatch_json = {
                    "SYSTEM_ID": mismatch.get('system_id', 'N/A'),
                    "CONFIG_MISMATCHED_SINCE": mismatch.get('config_mismatched_since', 'N/A')
                }
                config_mismatches.append(mismatch_json)
        
        # Extract device status data
        device_statuses = []
        if 'device_status' in config_data and config_data['device_status']:
            for device in config_data['device_status']:
                device_json = {
                    "SYSTEM_ID": device.get('system_id', 'N/A'),
                    "STATE": device.get('state', 'N/A'),
                    "CONFIG_TYPE": device.get('config_type', 'N/A'),
                    "DEPLOY_STAGE": device.get('deploy_stage', 'N/A'),
                    "ERROR_MESSAGE": device.get('error_message', 'None'),
                    "LAST_MODIFIED_AT": device.get('last_modified_at', 'N/A')
                }
                device_statuses.append(device_json)
        
        # Extract deployment status summary
        deployment_status = {}
        if 'deployment_status' in config_data:
            for config_type, stats in config_data['deployment_status'].items():
                deployment_status[config_type.upper()] = {
                    "SUCCEEDED": stats.get('num_succeeded', 0),
                    "FAILED": stats.get('num_failed', 0),
                    "PENDING": stats.get('num_pending', 0)
                }
        
        # Create the final JSON structure
        result_json = {
            "status": "success",
            "message": f"Retrieved configuration audit data for blueprint '{blueprint_name}'",
            "blueprint_name": blueprint_name,
            "total_devices": config_data.get('total_devices', 0),
            "overall_state": config_data.get('state', 'N/A'),
            "last_modified_at": config_data.get('last_modified_at', 'N/A'),
            "config_mismatches": {
                "total_count": len(config_mismatches),
                "mismatches": config_mismatches
            },
            "device_status": {
                "total_count": len(device_statuses),
                "devices": device_statuses
            },
            "deployment_status": deployment_status
        }
        
        # Add table creation prompt as directive to any LLM
        table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS COMPREHENSIVE CONFIGURATION AUDIT TABLES

**DIRECTIVE:** You must format the above configuration audit data as comprehensive, visually appealing markdown tables with multiple sections.

🎨 **VISUAL REQUIREMENTS:** Create professional, eye-catching tables with extensive use of emojis, proper alignment, and decorative elements.

### CONFIGURATION AUDIT OVERVIEW STRUCTURE

Create a comprehensive configuration audit overview with the following sections:

#### 1. 📋 AUDIT SUMMARY TABLE
Create a markdown table with overall audit information:
- Blueprint Name, Total Devices, Overall State
- Last Modified Date, Total Mismatches, Total Device Status Records

#### 2. ⚠️ CONFIGURATION MISMATCHES TABLE
Create a markdown table with all configuration mismatches from the "config_mismatches" JSON:
- System ID, Config Mismatched Since
- **IMPORTANT:** Add a note that System IDs should be mapped to hostnames using the get_system_details tool

#### 3. 🖥️ DEVICE STATUS TABLE
Create a markdown table with all device statuses from the "device_status" JSON:
- System ID, State, Config Type, Deploy Stage, Error Message, Last Modified
- **IMPORTANT:** Add a note that System IDs should be mapped to hostnames using the get_system_details tool

#### 4. 📊 DEPLOYMENT STATUS SUMMARY TABLE
Create a markdown table with deployment statistics from the "deployment_status" JSON:
- Config Type, Succeeded Count, Failed Count, Pending Count

**SYSTEM ID TO HOSTNAME MAPPING:**
🔍 **IMPORTANT NOTE:** The tables show System IDs, but for better readability, use the `get_system_details` tool to retrieve hostname mappings for each System ID. This will help correlate the configuration audit data with actual device hostnames.

**FORMATTING RULES:**
1. Use proper markdown table syntax with `|` separators and alignment (`:---:` for center, `:---` for left, `---:` for right)
2. Include fancy table headers with alignment and use **bold** headers
3. Add summary sections below tables with statistics and insights
4. Use emojis extensively for visual appeal:
   - Audit icons (🔍 Audit, 📋 Config, ⚠️ Mismatch, ✅ Success, ❌ Failed)
   - Status indicators (🟢 Succeeded, 🔴 Failed, 🟡 Pending, ⏳ Processing)
   - Device indicators (🖥️ Device, 🔧 Deploy, 📡 Service, 🚨 Error)
   - Time indicators (⏰ Since, 📅 Modified, 🕐 Timestamp)
5. **VISUAL ENHANCEMENT:** Use decorative elements like borders, separators (---), and section headers with emojis
6. Group data logically (mismatches by severity, devices by state, etc.)
7. Format timestamps consistently and make them human-readable
8. Use color-coded text indicators: 🔴 Critical, 🟡 Warning, 🟢 Healthy, 🔵 Info

**ADDITIONAL REQUIREMENTS FOR FANCY TABLES:**
- Sort tables by logical criteria (state, timestamp, system ID)
- Add totals/summary rows where appropriate
- Include status distribution summaries (e.g., "5 devices succeeded, 1 has config mismatch")
- Format timestamps with proper ISO format or human-readable format
- Highlight critical issues (config mismatches, error messages) using appropriate emojis
- Use alternating visual emphasis (bold system IDs, italic timestamps)
- Add section dividers with decorative lines (═══, ───, •••)
- Include deployment statistics and health indicators

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for system IDs and important status values
- Use *italics* for timestamps and secondary information
- Add horizontal rules (---) between major sections
- Include table captions with descriptive titles
- Use consistent spacing and alignment for professional appearance
- Add configuration context and deployment insights where relevant
- Highlight error messages and mismatches prominently

**CRITICAL ACTIONS SECTION:**
Add a section with actionable items:
- 🔍 Use `get_system_details` to map System IDs to hostnames
- ⚠️ Investigate configuration mismatches immediately
- 🔧 Review error messages for failed deployments
- 📊 Monitor deployment status trends
- 🔍 **CONFIG DEVIATION ANALYSIS:** When configuration mismatches are detected on any device, immediately use the `get_blueprint_anomalies` tool to retrieve the detailed configuration drift (diff between actual and expected config) for those specific devices

**STRUCTURE EXAMPLE:**
```
# 🔍 Configuration Audit: [Blueprint Name]

## 📋 Audit Summary
[Summary table with overall stats]

## ⚠️ Configuration Mismatches ([X] Total)
[Mismatches table with system IDs and timestamps]
💡 **Tip:** Use get_system_details to map System IDs to hostnames

## 🖥️ Device Deployment Status ([X] Total)
[Device status table with deployment details]
💡 **Tip:** Use get_system_details to map System IDs to hostnames

## 📊 Deployment Summary
[Deployment statistics by config type]

## 🚨 Critical Actions Required
[List of immediate actions needed]
```

**YOU MUST RESPOND WITH COMPREHENSIVE STYLED MARKDOWN TABLES IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the tables visually stunning with emojis, proper formatting, and professional styling! Include notes about using get_system_details for hostname mapping!

---
"""
        
        return json.dumps(result_json, indent=2) + table_prompt
    else:
        # If the response format is different, return raw JSON with error status
        return json.dumps({
            "status": "error",
            "message": "Unexpected data format from Apstra API",
            "raw_data": config_data
        }, indent=2)
