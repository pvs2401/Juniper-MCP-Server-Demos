"""Get blueprint anomalies tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent
import difflib

from .api_client import make_apstra_api_call

logger = logging.getLogger(__name__)


async def handle_get_blueprint_anomalies(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the get_blueprint_anomalies tool call for system or blueprint-wide anomalies."""
    system_id = arguments.get("system_id", "")
    blueprint_id = arguments.get("blueprint_id", "")
    
    if not system_id and not blueprint_id:
        error_msg = "Either system_id or blueprint_id is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        if system_id:
            logger.info(f"🔍 Fetching anomalies for system: {system_id}")
            # Get anomalies for this specific system
            anomalies_data = make_apstra_api_call(f"/api/systems/{system_id}/anomalies")
            context_info = f"system '{system_id}'"
        else:
            logger.info(f"🔍 Fetching anomalies for blueprint: {blueprint_id}")
            # Get all anomalies for the blueprint
            anomalies_data = make_apstra_api_call(f"/api/blueprints/{blueprint_id}/anomalies")
            context_info = f"blueprint '{blueprint_id}'"
        
        # Format the anomalies details as JSON grouped by type
        result = format_blueprint_anomalies_json(anomalies_data, system_id or blueprint_id, context_info)
        
        logger.info(f"✅ Anomalies retrieved for {context_info}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error getting anomalies: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_blueprint_anomalies_json(anomalies_data, identifier, context_info):
    """Format anomalies data as JSON for LLM consumption.
    
    This function returns structured JSON data grouped by anomaly type followed by 
    a strict directive that instructs any LLM to format the data as comprehensive 
    markdown tables based on anomaly type.
    """
    import json
    
    if isinstance(anomalies_data, dict) and 'items' in anomalies_data:
        anomalies = anomalies_data['items']
        
        # Group anomalies by type (not by node)
        anomalies_by_type = {}
        system_node_mapping = {}  # Track which systems have which anomalies
        
        for anomaly in anomalies:
            anomaly_type = anomaly.get('anomaly_type', 'unknown')
            
            if anomaly_type not in anomalies_by_type:
                anomalies_by_type[anomaly_type] = []
            
            # Extract all relevant information including node and system details
            anomaly_json = {
                "SEVERITY": anomaly.get('severity', 'N/A'),
                "ANOMALY_TYPE": anomaly_type,
                "ANOMALOUS_NODE_ID": anomaly.get('anomalous_node_id', 'N/A'),
                "SYSTEM_ID": anomaly.get('identity', {}).get('system_id', 'N/A'),
                "HOSTNAME": anomaly.get('identity', {}).get('hostname', 'N/A'),
                "ANOMALY_METADATA": anomaly.get('identity', {}),
                "EXPECTED_STATE": anomaly.get('expected', {}).get('value', 'N/A'),
                "ACTUAL_STATE": anomaly.get('actual', {}).get('value', 'N/A'),
                "LAST_MODIFIED": anomaly.get('last_modified_at', 'N/A'),
                "ROLE": anomaly.get('role', 'N/A'),
                "ANOMALY_ID": anomaly.get('id', 'N/A')
            }
            
            # Add route-specific information for better visibility
            if anomaly_type == 'route':
                # Extract route details from metadata
                route_info = anomaly.get('identity', {})
                anomaly_json["ROUTE_PREFIX"] = route_info.get('prefix', 'N/A')
                anomaly_json["VRF_NAME"] = route_info.get('vrf_name', 'N/A')
                anomaly_json["ROUTE_TYPE"] = route_info.get('route_type', 'N/A')
                
                # Better formatting for route anomalies
                expected_val = anomaly.get('expected', {}).get('value', '')
                actual_val = anomaly.get('actual', {}).get('value', '')
                if expected_val or actual_val:
                    anomaly_json["EXPECTED_STATE"] = expected_val if expected_val else "Route should be present"
                    anomaly_json["ACTUAL_STATE"] = actual_val if actual_val else "Route missing or incorrect"
            
            # Special handling for config anomalies
            elif anomaly_type == 'config':
                expected_config = anomaly.get('expected', {}).get('config', '')
                actual_config = anomaly.get('actual', {}).get('config', '')
                
                if expected_config and actual_config:
                    # Generate Unix-style diff
                    diff = generate_config_diff(expected_config, actual_config)
                    anomaly_json["EXPECTED_STATE"] = "Working config"
                    anomaly_json["ACTUAL_STATE"] = diff
                else:
                    anomaly_json["EXPECTED_STATE"] = "Working config"
                    anomaly_json["ACTUAL_STATE"] = "Config deviation detected"
            
            # Add BGP-specific information
            elif anomaly_type == 'bgp':
                bgp_info = anomaly.get('identity', {})
                anomaly_json["PEER_IP"] = bgp_info.get('peer_ip', 'N/A')
                anomaly_json["ASN"] = bgp_info.get('asn', 'N/A')
                anomaly_json["VRF_NAME"] = bgp_info.get('vrf_name', 'N/A')
                anomaly_json["ADDRESS_FAMILY"] = bgp_info.get('address_family', 'N/A')
            
            # Track system-to-node mapping for better insights
            sys_id = anomaly_json["SYSTEM_ID"]
            node_id = anomaly_json["ANOMALOUS_NODE_ID"]
            if sys_id != 'N/A' and node_id != 'N/A':
                if sys_id not in system_node_mapping:
                    system_node_mapping[sys_id] = set()
                system_node_mapping[sys_id].add(node_id)
            
            anomalies_by_type[anomaly_type].append(anomaly_json)
        
        # Create the final JSON structure with enhanced information
        result_json = {
            "status": "success",
            "message": f"Retrieved {len(anomalies)} anomalies for {context_info}",
            "context": context_info,
            "identifier": identifier,
            "total_anomalies": len(anomalies),
            "anomalies_by_type": anomalies_by_type,
            "anomaly_type_counts": {atype: len(items) for atype, items in anomalies_by_type.items()},
            "system_node_mapping": {sys_id: list(nodes) for sys_id, nodes in system_node_mapping.items()},
            "affected_systems": len(system_node_mapping),
            "affected_nodes": sum(len(nodes) for nodes in system_node_mapping.values())
        }
        
        # Add enhanced table creation prompt as directive to any LLM
        table_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT OUTPUT AS COMPREHENSIVE ANOMALY ANALYSIS

**DIRECTIVE:** You must format the above anomaly data as comprehensive, visually appealing markdown tables grouped by anomaly type showing ALL anomalies across ALL systems.

🎨 **VISUAL REQUIREMENTS:** Create professional, eye-catching tables with extensive use of emojis, proper alignment, and decorative elements specific to each anomaly type.

### ENHANCED ANOMALY OVERVIEW STRUCTURE

Create a comprehensive anomaly overview with the following sections:

#### 1. 📋 ANOMALY SUMMARY DASHBOARD
Create a markdown table with overall anomaly statistics:
- Context, Total Anomalies, Affected Systems, Affected Nodes
- Anomaly type distribution with counts
- Severity distribution (Critical, Major, Minor)

#### 2. COMPREHENSIVE TYPE-SPECIFIC ANOMALY TABLES
**CRITICAL**: Show ALL anomalies for each type - do not summarize or group by system

**🛣️ ROUTE ANOMALIES TABLE** (if present):
- **SHOW ALL ROUTE ANOMALIES** including 0.0.0.0/0 and specific routes like 192.168.1.11/32
- Columns: Severity, System ID, Hostname, Node ID, Route Prefix, VRF, Expected State, Actual State, Role
- **IMPORTANT**: Include separate row for each system/node with the same route anomaly
- Group by route prefix but show all affected systems
- Use route-specific emojis: 🛣️ for default routes, 🎯 for specific routes

**🔀 BGP ANOMALIES TABLE** (if present):
- Columns: Severity, System ID, Hostname, Node ID, Peer IP, ASN, VRF, Address Family, Expected/Actual State
- Include BGP-specific metadata like session state, peer details
- Show all BGP sessions across all systems

**⚙️ CONFIG ANOMALIES TABLE** (if present):
- Columns: Severity, System ID, Hostname, Node ID, Expected State, Config Diff Summary
- **SPECIAL**: Show config differences in a code block with proper diff formatting
- Highlight changed lines and provide summary of configuration changes

**🔌 INTERFACE ANOMALIES TABLE** (if present):
- Columns: Severity, System ID, Hostname, Node ID, Interface Name, Expected/Actual State, Role
- Include interface-specific metadata

**🔍 OTHER ANOMALY TYPES** (if present):
- Generic table with Severity, System ID, Hostname, Node ID, Metadata, Expected/Actual State

**ENHANCED FORMATTING RULES:**
1. **SHOW ALL ANOMALIES**: Never summarize or skip anomalies - show every single one
2. Include System ID, Hostname, and Node ID for complete identification
3. Use type-specific emojis and consistent formatting
4. **For route anomalies**: Group by route prefix but show all affected systems
5. Use severity-based emojis: 🔴 Critical, 🟡 Major/Medium, 🟢 Minor/Low, ⚪ Unknown
6. Add summary sections with affected system counts for each type
7. Format technical values consistently (IPs, ASNs, interfaces, routes)

**ROUTE ANOMALY SPECIAL HANDLING:**
- For default route (0.0.0.0/0) anomalies: Show all systems affected
- For specific route anomalies: Show exact route prefix and all affected systems
- Include VRF information and route type
- Highlight widespread route issues affecting multiple systems

**SYSTEM CORRELATION:**
- Use the system_node_mapping to show which systems are affected
- Highlight patterns (e.g., "All leaf switches affected by 0.0.0.0/0 route anomaly")
- Show hostname mapping when available

**VISUAL STYLING REQUIREMENTS:**
- Use **bold** for critical severity and system identifiers
- Use *italics* for timestamps and secondary information
- Add horizontal rules (---) between major sections
- Include system count summaries for each anomaly type
- Format IP addresses, routes, and technical identifiers consistently
- Use table headers with appropriate emojis for each anomaly type

**STRUCTURE EXAMPLE:**
```
# 🚨 Network Anomaly Analysis: [Context]

## 📊 Anomaly Dashboard
| Metric | Value |
|--------|-------|
| Total Anomalies | X |
| Affected Systems | Y |
| Route Anomalies | Z |

## 🛣️ Route Anomalies (X Total - Y Systems Affected)
| Severity | System ID | Hostname | Route Prefix | VRF | Expected | Actual | Node ID |
|----------|-----------|----------|--------------|-----|----------|--------|---------|
| [Show all route anomalies with complete system information]

### 🎯 Route Anomaly Patterns
- **0.0.0.0/0 Default Route**: Affecting X systems (list systems)
- **192.168.1.11/32 Specific Route**: Affecting Y systems (list systems)

## � BGP Anomalies (if any)
[Similar comprehensive table]

## ⚙️ Configuration Anomalies (if any)
[Similar comprehensive table with config diffs]
```

**YOU MUST RESPOND WITH COMPLETE ANOMALY TABLES SHOWING ALL SYSTEMS IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER**: Show EVERY single anomaly, especially route anomalies across ALL affected systems. Never summarize or group - show the complete picture!

---
"""
        
        return json.dumps(result_json, indent=2) + table_prompt
    else:
        # If no anomalies or different format
        return json.dumps({
            "status": "no_data",
            "message": f"No anomalies found for {context_info} or unexpected data format",
            "context": context_info,
            "identifier": identifier,
            "total_anomalies": 0,
            "anomalies_by_type": {},
            "raw_data": anomalies_data
        }, indent=2)


def generate_config_diff(expected_config, actual_config):
    """Generate Unix-style diff between expected and actual configurations."""
    try:
        # Split configs into lines for diff
        expected_lines = expected_config.splitlines(keepends=True)
        actual_lines = actual_config.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            expected_lines, 
            actual_lines,
            fromfile='Expected Config',
            tofile='Actual Config',
            lineterm=''
        ))
        
        if diff_lines:
            # Join the diff lines and return
            diff_output = '\n'.join(diff_lines)
            # Limit diff size for readability
            if len(diff_output) > 5000:
                diff_output = diff_output[:5000] + '\n... [diff truncated for readability] ...'
            return diff_output
        else:
            return "No differences detected in configuration comparison"
            
    except Exception as e:
        logger.warning(f"Error generating config diff: {e}")
        return f"Config difference detected but unable to generate diff: {str(e)}"
