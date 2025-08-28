import requests
import json
from urllib.parse import urlparse
from datetime import datetime

def _api_request(session, base_url, username, password, action, params=None):
    """Xtream Companion - A centralized and robust function for all API requests."""
    try:
        parsed_url = urlparse(base_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return {"error": "Invalid URL format."}
        
        api_url = f"{parsed_url.scheme}://{parsed_url.netloc}/player_api.php"
        
        payload = {'username': username, 'password': password, 'action': action}
        if params:
            payload.update(params)
        
        response = session.post(api_url, data=payload, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"Server error ({e.response.status_code}). Check credentials."}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed. Check URL and internet."}
    except requests.exceptions.Timeout:
        return {"error": "Connection timed out."}
    except json.JSONDecodeError:
        return {"error": "Invalid server response."}

def check_account_status(url, username, password):
    """Xtream Companion - Checks the main status of a user account and fetches server info."""
    session = requests.Session()
    session.headers.update({'User-Agent': 'XtreamCompanion/1.0'})
    response = _api_request(session, url, username, password, 'get_user_info')

    if not response or "error" in response or 'user_info' not in response:
        return {"Status": "Failed", "Details": response.get("error", "Invalid credentials.")}

    user_data = response.get('user_info', {})
    server_data = response.get('server_info', {})
    status = user_data.get('status', 'Error')
    
    result = {
        "Status": status.capitalize(),
        "Active Connections": user_data.get('active_cons', 'N/A'),
        "Max Connections": user_data.get('max_connections', 'N/A'),
        "Expiry Date": datetime.fromtimestamp(int(user_data['exp_date'])).strftime('%Y-%m-%d') if user_data.get('exp_date') else "No Expiry",
        "Details": "OK",
        "Timezone": server_data.get('timezone', 'N/A'),
        "Server URL": server_data.get('url', 'N/A'),
        "Port": server_data.get('port', 'N/A')
    }
    
    if status.lower() != 'active':
        result["Details"] = "Account is not active."
    
    return result

def get_live_categories(session, base_url, username, password):
    """Xtream Companion - Fetches all live TV channel categories (groups)."""
    return _api_request(session, base_url, username, password, 'get_live_categories')

def get_live_streams(session, base_url, username, password, category_id):
    """Xtream Companion - Fetches all live streams (channels) for a given category ID."""
    return _api_request(session, base_url, username, password, 'get_live_streams', {'category_id': category_id})

def get_full_epg_for_stream(session, base_url, username, password, stream_id):
    """Xtream Companion - Fetches the full EPG (program guide) for a single stream ID."""
    return _api_request(session, base_url, username, password, 'get_simple_data_table', {'stream_id': stream_id})