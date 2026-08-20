"""
Universal Multi-Platform Adapters (CodeBuddy, GoRouter, Tabi AI)
Author: D4NNBOZ
License: MIT
"""

import json
import base64
import datetime
from typing import Dict, Any, Optional

class BaseOAuthAdapter:
    def __init__(self, platform_id: str, name: str, unit_type: str):
        self.platform_id = platform_id
        self.name = name
        self.unit_type = unit_type

    def parse_session(self, raw_token_data: str) -> Dict[str, Any]:
        raise NotImplementedError

class CodeBuddyAdapter(BaseOAuthAdapter):
    def __init__(self):
        super().__init__("codebuddy-intl", "CodeBuddy Global", "credits")

    def parse_session(self, jwt_token: str) -> Dict[str, Any]:
        parts = jwt_token.split(".")
        if len(parts) < 2:
            return {"valid": False, "error": "Malformed JWT token"}

        payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode("utf-8"))
        
        email = payload.get("email") or payload.get("preferred_username") or "user"
        sub = payload.get("sub")
        exp = payload.get("exp")
        exp_date = datetime.datetime.fromtimestamp(exp, datetime.timezone.utc).isoformat() if exp else None

        return {
            "valid": True,
            "provider": "codebuddy-intl",
            "auth_type": "oauth",
            "email": email,
            "user_id": sub,
            "expires_at": exp_date,
            "allowance": "250 Bonus + 100 Monthly Credits",
            "access_token": jwt_token
        }

class GoRouterAdapter(BaseOAuthAdapter):
    def __init__(self):
        super().__init__("gorouter", "GoRouter", "usd_balance")

    def parse_session(self, session_key: str, email: str = "user@oauth") -> Dict[str, Any]:
        return {
            "valid": True,
            "provider": "gorouter",
            "auth_type": "apikey",
            "email": email,
            "allowance": "$70.00 USD Welcome + $5-$10/Daily Check-in",
            "access_token": session_key
        }

class TabiAIAdapter(BaseOAuthAdapter):
    def __init__(self):
        super().__init__("tabiai", "Tabi AI", "usd_balance")

    def parse_session(self, session_key: str, email: str = "user@oauth") -> Dict[str, Any]:
        return {
            "valid": True,
            "provider": "tabiai",
            "auth_type": "apikey",
            "email": email,
            "allowance": "$120.00 USD Developer Grant + $5-$10/Daily Check-in",
            "access_token": session_key
        }
