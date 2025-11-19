"""
Global settings
"""
# TODO: for dev, hardcode here. This should be structured as a config file.

# Meta Ads API
META_GRAPH_API_VERSION = "v24.0"
META_GRAPH_API_BASE = f"https://graph.facebook.com/{META_GRAPH_API_VERSION}"
USER_AGENT = "ithaca/1.0"

# meta ads oauth
META_APP_ID = "295659632199168"
META_APP_SECRET = "7781f7c36bb73839866856340ff3c762"

# New meta app can not set redirect url, so we use the old app id and secret
# META_APP_ID = "1928081404776564"
# META_APP_SECRET = "af89cecd54b7091ee8f92c12b92de2c5"

# llms
GEMINI_API_KEY = "AIzaSyBRJL6Gw3DJjn8linIKIdgXVf5DeoGFSOM"
