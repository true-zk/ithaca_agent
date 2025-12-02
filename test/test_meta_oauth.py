import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.oauth.auth import auth_manager
from ithaca.tools.meta_api.meta_ads_api import make_api_request


def test_meta_oauth():
    """Test Meta OAuth authentication flow"""
    print("=" * 60)
    print("Testing Meta OAuth Authentication")
    print("=" * 60)
    
    # Authenticate (will wait for user to authorize in browser)
    auth_manager.authenticate(force_refresh=True)
    access_token = auth_manager.get_access_token()
    print(f"Access Token: {access_token[:30]}...")
    print(f"Expires in: {auth_manager.token.expires_in}")
    print(f"Token Type: {auth_manager.token.token_type}")
    print(f"Created At: {auth_manager.token.created_at}")
    
    if not access_token:
        print("❌ Authentication failed!")
        return
    
    print(f"\n✅ Authentication successful!")
    print(f"Access Token: {access_token[:30]}...")
    
    # Test API call with the token
    print("\n" + "=" * 60)
    print("Testing API Call")
    print("=" * 60)
    return access_token


if __name__ == "__main__":
    access_token = test_meta_oauth()
    try:
        res = asyncio.run(make_api_request("me", access_token, {}))
        print(f"\n✅ API call successful!")
        print(f"Authenticated as: {res.get('name', 'Unknown')}")
        print(f"User ID: {res.get('id', 'Unknown')}")
    except Exception as e:
        print(f"\n❌ API call failed: {e}")