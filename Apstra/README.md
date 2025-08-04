# Apstra MCP Server

A Model Context Protocol (MCP) server that integrates Apstra network management with Claude Desktop, enabling natural language interactions with your Apstra infrastructure.

## Prerequisites

### System Requirements
- **macOS**: macOS 10.15+ or **Windows**: Windows 10/11
- **Python**: 3.10 or higher
- **uv package manager**: For dependency management
- **Claude Desktop**: Latest version
- **Apstra Server Access**: URL and API token

### Install Prerequisites

#### macOS
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

#### Windows
```powershell
# Install uv using PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/pvs2401/Juniper-MCP-Server-Demos.git
cd Juniper-MCP-Server-Demos/Apstra/Apstra

# Install dependencies
uv sync

# Test the installation
uv run python -c "import apstra.server; print('✅ Apstra MCP Server ready!')"
```

### 2. Get Apstra Credentials
You need two pieces of information from your Apstra administrator:
- **APSTRA_BASE_URL**: Your Apstra server URL (e.g., `https://apstra.example.com`)
- **APSTRA_API_TOKEN**: Your API authentication token

### 3. Test the Server
```bash
# Set environment variables (replace with your actual values)
export APSTRA_BASE_URL="https://your-apstra-server.com"
export APSTRA_API_TOKEN="your-api-token-here"

# Test the server connection
uv run apstra
# Press Ctrl+C to stop after seeing "Starting Apstra MCP Server in stdio mode..."
```

### 4. Configure Claude Desktop

#### Find Claude Desktop Config Location
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Add Configuration
Create or edit the `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "apstra": {
      "command": "uv",
      "args": ["run", "--directory", "/FULL/PATH/TO/YOUR/Apstra", "apstra"],
      "env": {
        "APSTRA_BASE_URL": "https://your-apstra-server.com",
        "APSTRA_API_TOKEN": "your-api-token-here"
      }
    }
  }
}
```

**⚠️ Important**: Replace `/FULL/PATH/TO/YOUR/Apstra` with the complete path to your Apstra directory.

#### Example Paths:
- **macOS**: `/Users/johndoe/Juniper-MCP-Server-Demos/Apstra/Apstra`
- **Windows**: `C:\Users\johndoe\Juniper-MCP-Server-Demos\Apstra\Apstra`

### 5. Restart Claude Desktop
1. Completely quit Claude Desktop
2. Restart Claude Desktop
3. Look for the 🔧 tool icon in Claude - this confirms MCP servers are loaded

## Available Features

Once configured, you can ask Claude to:

- **"List all blueprints in my Apstra system"** - View all network blueprints
- **"Show details for the datacenter blueprint"** - Get detailed blueprint information  
- **"Check for anomalies in blueprint X"** - Identify network issues and problems
- **"List devices in the production blueprint"** - View all network devices
- **"Get system details for blueprint Y"** - View system node information
- **"Show virtual networks in blueprint Z"** - List virtual network configurations
- **"Check security zones in my blueprint"** - View security zone configurations

## Troubleshooting

### Server Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check uv installation
uv --version

# Reinstall dependencies
uv sync --force

# Test imports
uv run python -c "import apstra.server; print('OK')"
```

### Claude Desktop Issues
1. **No tools visible**: Check that the path in `claude_desktop_config.json` is correct and absolute
2. **Connection errors**: Verify `APSTRA_BASE_URL` and `APSTRA_API_TOKEN` are correct
3. **Permission errors**: Ensure Claude Desktop can access the project directory

### API Connection Issues
```bash
# Test API connectivity manually
export APSTRA_BASE_URL="https://your-server.com"
export APSTRA_API_TOKEN="your-token"

# Test connection
curl -H "Authorization: Bearer $APSTRA_API_TOKEN" "$APSTRA_BASE_URL/api/blueprints"
```

### Common Fixes
- **Path errors**: Use forward slashes `/` even on Windows in the JSON config
- **Token expired**: Get a new API token from your Apstra administrator
- **Server unreachable**: Verify VPN connection if Apstra is behind a firewall
- **Permission denied**: Check that your API token has read access to blueprints

## Getting Help

1. **Check Claude Desktop logs** for detailed error messages
2. **Verify environment variables** are set correctly in the config
3. **Test API access** directly using curl or a browser
4. **Ensure all paths are absolute** in the Claude Desktop config

## Project Structure

```
Apstra/
├── apstra/
│   ├── server.py              # Main MCP server
│   └── tools/                 # Individual tool implementations
│       ├── api_client.py      # Apstra API client
│       ├── list_blueprints.py # Blueprint operations
│       ├── get_blueprint_details.py
│       ├── get_system_details.py
│       ├── get_virtual_networks.py
│       ├── get_security_zones.py
│       ├── get_config_audits.py
│       ├── get_blueprint_anomalies.py
│       └── apply_system_golden_config.py
├── pyproject.toml             # Dependencies and configuration
└── README.md                  # This file
```
