"""Apply system golden config tool for Apstra MCP Server.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
from typing import Any
from mcp.types import TextContent

from .api_client import make_apstra_api_call
from .get_blueprint_anomalies import format_blueprint_anomalies_json

logger = logging.getLogger(__name__)


async def handle_apply_system_golden_config(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle the apply_system_golden_config tool call."""
    system_id = arguments.get("system_id", "")
    confirmation = arguments.get("confirmation", "").lower()
    
    if not system_id:
        error_msg = "System ID is required"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]

    try:
        logger.info(f"🔧 Processing golden config application for system: {system_id}")
        
        # Step 1: Get current config anomalies to show diff
        anomalies_data = make_apstra_api_call(f"/api/systems/{system_id}/anomalies")
        
        # Check if there are config anomalies
        has_config_anomalies = False
        if isinstance(anomalies_data, dict) and 'items' in anomalies_data:
            for anomaly in anomalies_data['items']:
                if anomaly.get('anomaly_type') == 'config':
                    has_config_anomalies = True
                    break
        
        if not has_config_anomalies:
            # No config anomalies found
            result = format_no_config_anomalies_response(system_id)
            logger.info(f"✅ No config anomalies found for system: {system_id}")
            return [TextContent(type="text", text=result)]
        
        # Step 2: If no confirmation provided, show diff and ask for confirmation
        if not confirmation or confirmation not in ['yes', 'y', 'confirm', 'apply']:
            result = format_config_confirmation_request(anomalies_data, system_id)
            logger.info(f"⚠️ Showing config diff and requesting confirmation for system: {system_id}")
            return [TextContent(type="text", text=result)]
        
        # Step 3: User confirmed, apply the golden config
        logger.info(f"🚀 Applying golden config for system: {system_id}")
        apply_response = make_apstra_api_call(
            f"/api/systems/{system_id}/apply-full-config",
            method="POST"
        )
        
        # Format the application result
        result = format_config_application_result(apply_response, system_id)
        
        logger.info(f"✅ Golden config application completed for system: {system_id}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        error_msg = f"Error applying golden config: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return [TextContent(type="text", text=error_msg)]


def format_no_config_anomalies_response(system_id):
    """Format response when no config anomalies are found."""
    import json
    
    result_json = {
        "status": "no_action_needed",
        "message": f"System '{system_id}' has no configuration anomalies",
        "system_id": system_id,
        "config_status": "in_sync",
        "action_required": False
    }
    
    info_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT NO-ACTION-NEEDED RESPONSE

**DIRECTIVE:** You must format the above response as a clear status message indicating no action is required.

🎨 **VISUAL REQUIREMENTS:** Create a clean, informative message with appropriate emojis and professional formatting.

### STATUS MESSAGE STRUCTURE

Create a status message with the following sections:

#### 1. ✅ CONFIGURATION STATUS SUMMARY
- System ID and current configuration status
- Clear indication that no action is needed
- Configuration sync status

#### 2. 📋 VERIFICATION DETAILS
- Confirmation that no config anomalies were detected
- Current configuration state is aligned with golden config
- No drift detected

**FORMATTING RULES:**
1. Use clear, positive language indicating healthy state
2. Include system identification prominently
3. Use status emojis: ✅ Good, 📋 Info, 🔧 Config
4. **VISUAL ENHANCEMENT:** Use decorative elements and clear section headers
5. Professional formatting with consistent spacing

**STRUCTURE EXAMPLE:**
```
# ✅ Configuration Status: [System ID]

## 📋 System Configuration Status
✅ **Status**: Configuration In Sync
🔧 **Action Required**: None
📊 **Config Anomalies**: None detected

## 💡 Summary
The system configuration is properly aligned with the golden configuration. No configuration drift detected.
```

**YOU MUST RESPOND WITH A CLEAR STATUS MESSAGE IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the message clear that no action is required and the system is healthy!

---
"""
    
    return json.dumps(result_json, indent=2) + info_prompt


def format_config_confirmation_request(anomalies_data, system_id):
    """Format confirmation request with config diff display."""
    import json
    
    # Use the existing anomaly formatting to show config diff
    context_info = f"system '{system_id}'"
    anomaly_analysis = format_blueprint_anomalies_json(anomalies_data, system_id, context_info)
    
    # Extract just the JSON part (before the LLM prompt)
    anomaly_json_part = anomaly_analysis.split('\n---\n')[0]
    
    confirmation_json = {
        "status": "confirmation_required",
        "message": f"Configuration anomalies detected for system '{system_id}' - confirmation required before applying golden config",
        "system_id": system_id,
        "action_pending": "apply_golden_config",
        "config_anomalies": json.loads(anomaly_json_part)
    }
    
    confirmation_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT CONFIGURATION CONFIRMATION REQUEST

**DIRECTIVE:** You must format the above data as a comprehensive configuration change confirmation request.

🎨 **VISUAL REQUIREMENTS:** Create a professional, cautionary message with configuration diff display and clear confirmation request.

### CONFIRMATION REQUEST STRUCTURE

Create a confirmation request with the following sections:

#### 1. ⚠️ CONFIGURATION DRIFT DETECTED
- System ID and current configuration status
- Clear indication that configuration changes will be applied
- Warning about the nature of configuration changes

#### 2. 📝 CONFIGURATION DIFFERENCES
Use the config anomalies data to show the configuration differences:
- Display the actual configuration diff from ACTUAL_STATE field
- Format as a proper code block with diff syntax highlighting
- Highlight critical configuration changes

#### 3. 🔧 PROPOSED ACTION
- Clear description of what will happen when golden config is applied
- Expected outcome and system behavior
- Potential impact warnings

#### 4. 🚨 CONFIRMATION REQUIRED
- **CRITICAL**: Ask user to explicitly confirm before proceeding
- Provide clear instruction on how to confirm (use "yes", "confirm", or "apply")
- Warning about service impact

**FORMATTING RULES:**
1. Use cautionary language and appropriate warning emojis
2. Include system identification prominently
3. Use warning emojis: ⚠️ Warning, 🚨 Critical, 📝 Config, 🔧 Action
4. **VISUAL ENHANCEMENT:** Use decorative elements and clear section headers
5. Format configuration diffs in proper code blocks with diff syntax
6. Make confirmation request very clear and prominent

**SPECIAL CONFIG DIFF HANDLING:**
- Extract the configuration diff from the config anomalies ACTUAL_STATE
- Display in a code block with proper diff formatting
- Add summary of what configuration sections will change
- Highlight critical changes that may affect service

**STRUCTURE EXAMPLE:**
```
# ⚠️ Configuration Change Confirmation Required: [System ID]

## 📝 Configuration Drift Detected
🚨 **Warning**: Configuration anomalies detected that require golden config application

## 📋 Configuration Differences
The following configuration changes will be applied:

```diff
[Show actual diff from anomaly data]
```

## 🔧 Proposed Action
Applying golden configuration will:
- Restore configuration to expected state
- May cause brief service interruption
- Align system with network standards

## 🚨 CONFIRMATION REQUIRED
⚠️ **This action will modify system configuration and may impact services.**

To proceed with applying the golden configuration, please respond with:
- "yes" or "confirm" or "apply"

To cancel this operation, respond with "no" or "cancel"
```

**YOU MUST RESPOND WITH A DETAILED CONFIRMATION REQUEST IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the confirmation request very clear and show the actual configuration differences!

---
"""
    
    return json.dumps(confirmation_json, indent=2) + confirmation_prompt


def format_config_application_result(apply_response, system_id):
    """Format the result of golden config application."""
    import json
    
    # Determine success based on response
    success = False
    message = "Unknown result"
    
    if isinstance(apply_response, dict):
        # Check for success indicators in the response
        if apply_response.get('status') == 'success' or 'success' in str(apply_response).lower():
            success = True
            message = "Golden configuration applied successfully"
        elif 'error' in apply_response or 'failed' in str(apply_response).lower():
            success = False
            message = f"Failed to apply golden configuration: {apply_response.get('message', str(apply_response))}"
        else:
            success = True  # Assume success if no explicit error
            message = "Golden configuration application initiated"
    else:
        # Non-dict response, assume success if no exception was thrown
        success = True
        message = "Golden configuration application completed"
    
    result_json = {
        "status": "applied" if success else "failed",
        "message": message,
        "system_id": system_id,
        "action_completed": "apply_golden_config",
        "success": success,
        "response_data": apply_response if isinstance(apply_response, dict) else str(apply_response)
    }
    
    result_prompt = """

---

## 📊 LLM INSTRUCTION: FORMAT CONFIGURATION APPLICATION RESULT

**DIRECTIVE:** You must format the above result as a comprehensive configuration application status report.

🎨 **VISUAL REQUIREMENTS:** Create a professional status report with clear success/failure indication and next steps.

### APPLICATION RESULT STRUCTURE

Create a result report with the following sections:

#### 1. 🎯 APPLICATION STATUS
- System ID and action performed
- Clear success or failure indication
- Timestamp and completion status

#### 2. 📋 RESULT DETAILS
- Detailed message about the application result
- Any response data from the system
- Configuration sync status

#### 3. 🔄 POST-APPLICATION ACTIONS
- Recommended verification steps
- Monitoring suggestions
- Next actions to take

**FORMATTING RULES:**
1. Use clear success (✅) or failure (❌) indicators
2. Include system identification prominently
3. Use result emojis: ✅ Success, ❌ Failed, 🔄 In Progress, 📋 Info
4. **VISUAL ENHANCEMENT:** Use decorative elements and clear status headers
5. Professional formatting with consistent spacing
6. If successful, include positive language and next steps
7. If failed, include troubleshooting guidance

**SUCCESS STRUCTURE EXAMPLE:**
```
# ✅ Golden Configuration Applied Successfully: [System ID]

## 🎯 Application Status
✅ **Status**: Configuration Applied
🔧 **Action**: Golden Config Deployment
📊 **Result**: Success

## 📋 Details
[Result details and response information]

## 🔄 Recommended Next Steps
1. Verify configuration sync status
2. Check system connectivity
3. Monitor for any service impacts
4. Validate network functionality
```

**FAILURE STRUCTURE EXAMPLE:**
```
# ❌ Golden Configuration Application Failed: [System ID]

## 🎯 Application Status
❌ **Status**: Configuration Application Failed
🔧 **Action**: Golden Config Deployment
📊 **Result**: Error

## 📋 Error Details
[Error details and response information]

## 🔄 Troubleshooting Steps
1. Check system connectivity
2. Verify system permissions
3. Review configuration syntax
4. Retry operation if appropriate
```

**YOU MUST RESPOND WITH A DETAILED STATUS REPORT IMMEDIATELY - NO OTHER TEXT**

🎯 **FINAL REMINDER:** Make the result status very clear and provide appropriate next steps!

---
"""
    
    return json.dumps(result_json, indent=2) + result_prompt
