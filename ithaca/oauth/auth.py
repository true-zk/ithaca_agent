"""
Meta oauth
For now, only supports meta ads oauth
"""
from typing import Optional, Dict, Any
import json
import time
import webbrowser
import requests

from ithaca.logger import logger
from ithaca.utils import get_cache_dir
from ithaca.settings import META_APP_ID, META_APP_SECRET
from ithaca.oauth.callback_server import start_callback_server


logger.info("OAuth manager initialized")


class OAuthToken:
    """Stores OAuth token including expiration"""
    def __init__(
        self,
        access_token: str,
        expires_in: Optional[int] = None,
        user_id: Optional[str] = None,
    ):
        self.access_token = access_token
        self.expires_in = expires_in
        self.user_id = user_id
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
            "user_id": self.user_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'OAuthToken':
        """Create from a stored dictionary"""
        token = cls(
            access_token=data.get("access_token", ""),
            expires_in=data.get("expires_in"),
            user_id=data.get("user_id")
        )
        token.created_at = data.get("created_at", int(time.time()))
        return token


class OAuthManager:
    """
    Manager for OAuth authentication
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
    
    def _load_cached_token(self) -> None:
        #  TODO: Token expiration check
        if self.cache_file.exists():
            with self.cache_file.open("r") as f:
                data = json.load(f)
                self.token = OAuthToken.deserialize(data)
                logger.info(f"Cached token loaded from {self.cache_file}")
    
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
            f"https://www.facebook.com/v22.0/dialog/oauth?"
            f"client_id={self.app_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={self.AUTH_SCOPE}&"
            f"response_type={self.AUTH_RESPONSE_TYPE}"
        )
    
    def exchange_code_for_token(self, code: str) -> Optional[OAuthToken]:
        """
        Exchange authorization code for access token
        """
        try:
            response = requests.post(
                "https://graph.facebook.com/v22.0/oauth/access_token",
                data={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "grant_type": "authorization_code",
                    "code": code
                }
            )
            response.raise_for_status()
            data = response.json()
            return OAuthToken(
                access_token=data["access_token"],
                expires_in=data["expires_in"],
                user_id=data["user_id"]
            )
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None
    
    def authenticate(self, force_refresh: bool = False) -> Optional[str]:
        """
        Authenticate with Meta APIs
        
        Args:
            force_refresh: Force token refresh even if cached token exists
            
        Returns:
            Access token if successful, None otherwise
        """
        # Check if we already have a valid token
        if not force_refresh and self.token and not self.token.is_expired():
            return self.token.access_token
        
        # Authenticate with Meta APIs
        try:
            port = start_callback_server()
            
            # Update redirect URI with the actual port for callback server
            self.redirect_uri = f"http://localhost:{port}/callback"
            
            # Generate the auth URL for user to authorize
            auth_url = self.get_auth_url()
            
            # Open browser with auth URL
            logger.info(f"Opening browser with URL: {auth_url}")
            webbrowser.open(auth_url)
            
            # We don't wait for the token here anymore
            # The token will be processed by the **callback server**
            # Just return None to indicate we've started the flow
            return None
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            logger.info("Callback server disabled. OAuth authentication flow cannot be used.")
            return None
