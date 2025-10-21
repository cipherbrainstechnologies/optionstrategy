"""
FYERS Token Refresh Module - Automatic Access Token Renewal
Implements FYERS API v3 refresh token flow for 24/7 autonomous operation.

Token Lifecycle:
- Access Token: 12 hours validity
- Refresh Token: 30 days validity
- Auto-refresh: Daily at 08:45 IST (before market hours)
- Manual renewal: Once every 30 days when refresh token expires
"""
import os
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, set_key, find_dotenv

logger = logging.getLogger(__name__)


class FyersTokenRefresh:
    """Handles automatic FYERS token refresh using API v3."""
    
    def __init__(self, settings=None):
        """
        Initialize token refresh handler.
        
        Args:
            settings: Settings object with FYERS credentials (optional)
        """
        if settings:
            self.client_id = settings.FYERS_CLIENT_ID
            self.secret_key = settings.FYERS_SECRET_KEY
            self.refresh_token = getattr(settings, 'FYERS_REFRESH_TOKEN', None)
            self.sandbox = settings.FYERS_SANDBOX
        else:
            load_dotenv()
            self.client_id = os.getenv("FYERS_CLIENT_ID")
            self.secret_key = os.getenv("FYERS_SECRET_KEY")
            self.refresh_token = os.getenv("FYERS_REFRESH_TOKEN")
            self.sandbox = os.getenv("FYERS_SANDBOX", "true").lower() == "true"
        
        # API endpoints
        if self.sandbox:
            self.base_url = "https://api-t1.fyers.in/api/v3"
        else:
            self.base_url = "https://api.fyers.in/api/v3"
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh FYERS access token using refresh token.
        
        Returns:
            Dict with status, new_token, and message
        """
        if not self.refresh_token:
            logger.error("No refresh token available - manual OAuth required")
            return {
                "status": "error",
                "message": "No refresh token available. Complete manual OAuth first."
            }
        
        try:
            url = f"{self.base_url}/validate-refresh-token"
            
            payload = {
                "grant_type": "refresh_token",
                "appIdHash": self._get_app_id_hash(),
                "refresh_token": self.refresh_token,
                "pin": ""  # Not required for refresh token flow
            }
            
            logger.info(f"Requesting token refresh from FYERS API: {url}")
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("s") == "ok":
                    new_access_token = data.get("access_token")
                    
                    # Optionally get new refresh token if provided
                    new_refresh_token = data.get("refresh_token")
                    
                    logger.info(f"✅ FYERS token refreshed successfully")
                    logger.info(f"   Access token: {new_access_token[:20]}...")
                    
                    # Update .env file with new token
                    self._update_env_file("FYERS_ACCESS_TOKEN", new_access_token)
                    
                    if new_refresh_token:
                        logger.info(f"   New refresh token received: {new_refresh_token[:20]}...")
                        self._update_env_file("FYERS_REFRESH_TOKEN", new_refresh_token)
                    
                    return {
                        "status": "success",
                        "new_token": new_access_token,
                        "new_refresh_token": new_refresh_token,
                        "message": "Token refreshed successfully"
                    }
                else:
                    error_msg = data.get("message", "Unknown error")
                    logger.error(f"❌ Token refresh failed: {error_msg}")
                    
                    # Check if refresh token expired
                    if "expired" in error_msg.lower() or "invalid" in error_msg.lower():
                        self._handle_expired_refresh_token()
                    
                    return {
                        "status": "error",
                        "message": error_msg
                    }
            else:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            logger.error(f"❌ Token refresh exception: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _get_app_id_hash(self) -> str:
        """
        Generate app ID hash required by FYERS API.
        
        Returns:
            str: App ID hash
        """
        import hashlib
        
        # FYERS requires appIdHash = SHA256(client_id + ":" + secret_key)
        raw = f"{self.client_id}:{self.secret_key}"
        app_id_hash = hashlib.sha256(raw.encode()).hexdigest()
        
        return app_id_hash
    
    def _update_env_file(self, key: str, value: str) -> bool:
        """
        Update .env file with new token value.
        
        Args:
            key: Environment variable name
            value: New value
            
        Returns:
            bool: Success status
        """
        try:
            env_file = find_dotenv()
            
            if not env_file:
                # Try common locations
                possible_paths = [
                    Path.cwd() / ".env",
                    Path(__file__).parent.parent.parent / ".env"
                ]
                
                for path in possible_paths:
                    if path.exists():
                        env_file = str(path)
                        break
            
            if not env_file:
                logger.warning(f"Could not find .env file to update {key}")
                logger.warning("You may need to manually update the token in Render dashboard")
                return False
            
            # Update the .env file
            set_key(env_file, key, value)
            logger.info(f"✅ Updated {key} in {env_file}")
            
            # Also update environment variable in current process
            os.environ[key] = value
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            return False
    
    def _handle_expired_refresh_token(self):
        """
        Handle expired refresh token by providing manual renewal instructions.
        """
        logger.error("=" * 80)
        logger.error("🔑 FYERS REFRESH TOKEN EXPIRED - MANUAL RENEWAL REQUIRED 🔑")
        logger.error("=" * 80)
        logger.error("❌ Your FYERS refresh token has expired (30-day validity)")
        logger.error("")
        logger.error("📋 STEPS TO RENEW:")
        logger.error("   1. Visit FYERS Developer Portal: https://myapi.fyers.in")
        logger.error("   2. Login with your credentials")
        logger.error("   3. Generate new OAuth tokens (access + refresh)")
        logger.error("   4. Update Render dashboard environment variables:")
        logger.error("      - FYERS_ACCESS_TOKEN=<new_access_token>")
        logger.error("      - FYERS_REFRESH_TOKEN=<new_refresh_token>")
        logger.error("   5. Restart the application")
        logger.error("")
        logger.error("⏰ This is required once every 30 days")
        logger.error("🔄 After renewal, automatic refresh will resume")
        logger.error("=" * 80)
    
    def check_token_expiry(self) -> Dict[str, Any]:
        """
        Check if current access token is still valid.
        
        Returns:
            Dict with status and validity info
        """
        try:
            # Import here to avoid circular dependency
            from .fyers_client import FyersAPI
            
            # Create temporary client to test token
            class TempSettings:
                FYERS_CLIENT_ID = self.client_id
                FYERS_SECRET_KEY = self.secret_key
                FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN")
                FYERS_SANDBOX = self.sandbox
                LOG_PATH = "./data/"
            
            client = FyersAPI(TempSettings())
            
            # Test token with profile API
            is_valid = client.refresh_token_if_needed()
            
            if is_valid:
                return {
                    "status": "valid",
                    "message": "Current token is valid"
                }
            else:
                return {
                    "status": "expired",
                    "message": "Token expired or invalid"
                }
        
        except Exception as e:
            logger.error(f"Error checking token expiry: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


def run_scheduled_refresh():
    """
    Scheduled job to refresh FYERS token daily.
    Run this at 08:45 IST (before market hours).
    """
    logger.info("=" * 80)
    logger.info("🔄 FYERS TOKEN REFRESH - Scheduled Daily Maintenance")
    logger.info("=" * 80)
    logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    try:
        refresher = FyersTokenRefresh()
        
        # Check current token status
        status = refresher.check_token_expiry()
        logger.info(f"📊 Current token status: {status['message']}")
        
        # Refresh token
        result = refresher.refresh_access_token()
        
        if result["status"] == "success":
            logger.info("=" * 80)
            logger.info("✅ TOKEN REFRESH SUCCESSFUL")
            logger.info("=" * 80)
            logger.info(f"   New access token: {result['new_token'][:20]}...")
            logger.info("   Token valid for: 12 hours")
            logger.info("   Next refresh: Tomorrow 08:45 IST")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("❌ TOKEN REFRESH FAILED")
            logger.error("=" * 80)
            logger.error(f"   Error: {result['message']}")
            logger.error("   System will continue with MockExchange until resolved")
            logger.error("=" * 80)
    
    except Exception as e:
        logger.error(f"❌ Token refresh job failed: {e}")
        logger.exception(e)


if __name__ == "__main__":
    """Manual token refresh for testing."""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if "--test" in sys.argv:
        # Test token validity
        refresher = FyersTokenRefresh()
        status = refresher.check_token_expiry()
        print(f"\nToken Status: {status}")
    else:
        # Run refresh
        run_scheduled_refresh()
