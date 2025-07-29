"""Apstra API client module for handling all API interactions.

Author: Vivekananda Shenoy (https://github.com/pvs2401)
"""

import logging
import os
import requests
import urllib3

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def get_apstra_config():
    """Get Apstra configuration from environment variables."""
    base_url = os.getenv('APSTRA_BASE_URL')
    api_token = os.getenv('APSTRA_API_TOKEN')
    
    if not base_url:
        raise ValueError("APSTRA_BASE_URL environment variable is required")
    if not api_token:
        raise ValueError("APSTRA_API_TOKEN environment variable is required")
    
    # Ensure base_url doesn't end with slash
    base_url = base_url.rstrip('/')
    
    return base_url, api_token


def make_apstra_api_call(endpoint: str, method: str = 'GET', data: dict = None):
    """Make an API call to Apstra server."""
    try:
        base_url, api_token = get_apstra_config()
        
        # Construct full URL
        url = f"{base_url}{endpoint}"
        
        # Prepare headers
        headers = {
            'AUTHTOKEN': f'{api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Make the API call
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30, verify=False)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30, verify=False)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check if request was successful
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error making Apstra API call: {e}")
        raise