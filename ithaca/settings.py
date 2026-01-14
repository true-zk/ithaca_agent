"""
Global settings
"""
# TODO: for dev, hardcode here. This should be structured as a config file.

# Cache
CACHE_DIR = None
DB_PATH = None

# Meta Ads API
META_GRAPH_API_VERSION = "v24.0"
META_OAUTH_BASE = f"https://facebook.com/{META_GRAPH_API_VERSION}"
META_GRAPH_API_BASE = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
USER_AGENT = "ithaca/1.0"

# meta ads oauth
META_APP_ID = "" # yours
META_APP_SECRET = "" # yours
# CALLBACK_SERVER_URL = "https://slinky-workless-rueben.ngrok-free.dev/"   # use ngrok for development
CALLBACK_SERVER_URL = "http://localhost:8080/"

# New meta app can not set redirect url, so we use the old app id and secret
# META_APP_ID = "" 
# META_APP_SECRET = ""

# llms
GEMINI_API_KEY = ""  # yours

# agents
AGENT_CONFIG_FILE = ""
