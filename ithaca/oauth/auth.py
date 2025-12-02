"""
Meta oauth.
Cite from: https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
"""
from typing import Optional, Dict, Any
import json
import time
import webbrowser
import requests

from ithaca.logger import logger
from ithaca.utils import get_cache_dir
from ithaca.settings import META_APP_ID, META_APP_SECRET, META_GRAPH_API_BASE, META_OAUTH_BASE
from ithaca.oauth.callback_server import start_callback_server, shutdown_callback_server


logger.info("OAuth manager initialized")


class OAuthToken:
    """Stores OAuth token including expiration"""
    def __init__(
        self,
        access_token: str,
        expires_in: Optional[int] = None,
        token_type: Optional[str] = None,
    ):
        self.access_token = access_token
        self.expires_in = expires_in
        self.token_type = token_type
        self.created_at = int(time.time())
        logger.debug(f"TokenInfo created. Expires in: {expires_in if expires_in else 'Not specified'}")
    
    def is_expired(self) -> bool:
        """Check if the token is expired"""
        if not self.expires_in:
            return False  # If no expiration is set, assume it's not expired
        
        current_time = int(time.time())
        return current_time > (self.created_at + self.expires_in)
    
    def serialize(self) -> Dict[str, Any]:
        """Convert to a dictionary for storage"""
        return {
            "access_token": self.access_token,
            "expires_in": self.expires_in,
            "token_type": self.token_type,
            "created_at": self.created_at
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'OAuthToken':
        """Create from a stored dictionary"""
        token = cls(
            access_token=data.get("access_token", ""),
            expires_in=data.get("expires_in"),
            token_type=data.get("token_type")
        )
        token.created_at = data.get("created_at", int(time.time()))
        return token


class OAuthManager:
    """
    Manager for OAuth authentication. This should be used as a singleton.
    """
    AUTH_SCOPE = "business_management,public_profile,pages_show_list,pages_read_engagement"
    AUTH_RESPONSE_TYPE = "code" # if 'token', will use implicit flow (data not response to server)

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        """
        Initialize the OAuth manager
        """
        self.app_id = app_id or META_APP_ID
        self.app_secret = app_secret or META_APP_SECRET
        self.redirect_uri = None

        self.token: Optional[OAuthToken] = None
        self.cache_file = get_cache_dir() / "meta_ads_token.json"
        self._load_cached_token()
        if self.token is None:
            self.authenticate(force_refresh=True)
    
    def _load_cached_token(self) -> None:
        #  TODO: Token expiration check
        if self.cache_file.exists():
            with self.cache_file.open("r") as f:
                data = json.load(f)
                token = OAuthToken.deserialize(data)
                logger.info(f"Cached token loaded from {self.cache_file}")
                if token.is_expired():
                    logger.info("Cached token is expired.")
                    self.token = None
                else:
                    logger.info(f"Cached token is valid. Expires in: {token.expires_in} seconds")
                    self.token = token
                
    
    def _save_cached_token(self) -> None:
        if self.token:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                with self.cache_file.open("w") as f:
                    json.dump(self.token.serialize(), f)
                logger.info(f"Cached token saved to {self.cache_file}")
            except IOError as e:
                logger.error(f"Failed to save cached token: {e}")

    def get_auth_url(self) -> str:
        return (
            f"{META_OAUTH_BASE}/dialog/oauth?"
            f"client_id={self.app_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={self.AUTH_SCOPE}&"
            f"response_type={self.AUTH_RESPONSE_TYPE}"
        )
    
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[OAuthToken]:
        """
        Exchange authorization code for access token
        """
        try:
            logger.debug(f"Exchanging code with redirect_uri: {redirect_uri}")
            
            response = requests.post(
                f"{META_GRAPH_API_BASE}/oauth/access_token",
                data={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": redirect_uri,  # ✅ 添加 redirect_uri
                    "code": code
                }
            )
            
            # Check response before raising
            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Meta API error: {error_data}")
                logger.error(f"Status code: {response.status_code}")
                response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Successfully exchanged code for token")
            logger.debug(f"Token data: {data}")
            
            return OAuthToken(
                access_token=data["access_token"],
                expires_in=data.get("expires_in"),
                token_type=data.get("token_type")
            )
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error exchanging code: {e}")
            try:
                error_detail = e.response.json()
                logger.error(f"Error details: {error_detail}")
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def authenticate(self, force_refresh: bool = False, wait_for_token: bool = True, timeout: int = 180):
        """
        Authenticate with Meta APIs
        
        Args:
            force_refresh: Force token refresh even if cached token exists
            wait_for_token: Whether to wait for user authorization (default: True)
            timeout: Maximum time to wait for authorization in seconds (default: 180)
            
        Returns:
            Access token if successful, None otherwise
        """
        # Check if we already have a valid token
        if not force_refresh and self.token and not self.token.is_expired():
            logger.info("Using cached token")
            return self.token.access_token
        
        # Authenticate with Meta APIs
        try:
            from ithaca.oauth.callback_server import token_container
            
            # Clear previous token if any
            token_container.pop("token", None)
            
            port = start_callback_server()
            
            # Update redirect URI with the actual port for callback server
            self.redirect_uri = f"http://localhost:{port}/callback"
            
            # Generate the auth URL for user to authorize
            auth_url = self.get_auth_url()
            
            # Open browser with auth URL
            logger.info(f"Opening browser for authorization...")
            logger.info(f"Auth URL: {auth_url}")
            webbrowser.open(auth_url)
            
            if not wait_for_token:
                logger.info("Not waiting for token (wait_for_token=False)")
                return None
            
            # Wait for authorization code
            logger.info(f"Waiting for user authorization (timeout: {timeout}s)...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if "auth_code" in token_container:
                    code = token_container["auth_code"]
                    logger.info(f"✅ Received authorization code: {code[:10]}...")
                    
                    # Exchange code for token
                    logger.info("Exchanging code for access token...")
                    # exchange_redirect_uri = f"http://localhost:{port}/token_exchange"
                    token = self.exchange_code_for_token(code, redirect_uri=self.redirect_uri)
                    if token:
                        logger.info("✅ Authentication successful!")
                        self.token = token
                        self._save_cached_token()

                        shutdown_callback_server()
                        return token.access_token, token.expires_in, token.token_type
                    else:
                        logger.error("❌ Failed to exchange code for token")
                        return None
                
                # Check every 0.5 seconds
                time.sleep(0.5)
            
            logger.error(f"❌ Timeout waiting for authorization ({timeout}s)")
            return None
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def invalidate_token(self) -> None:
        """Invalidate the current token"""
        logger.info(f"Token invalidated: {self.token.access_token[:10]}...")
        self.token = None
        self.cache_file.unlink(missing_ok=True)
        logger.info(f"Cached token file removed: {self.cache_file}")
    
    def get_access_token(self) -> Optional[str]:
        """Get the access token"""
        if self.token and not self.token.is_expired():
            return self.token.access_token
        else:
            return None
        

auth_manager = OAuthManager()