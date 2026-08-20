"""
Universal 9Router SQLite Database Injector
Handles additive insertion without wiping existing pools.
Author: D4NNBOZ
License: MIT
"""

import sqlite3
import os
import json
import uuid
import datetime
from typing import Dict, Any, Optional

class DatabaseInjector:
    def __init__(self, db_path: str = "~/.9router/db/data.sqlite"):
        self.db_path = os.path.expanduser(db_path)

    def inject_session(self, parsed_data: Dict[str, Any], custom_name: Optional[str] = None) -> Dict[str, Any]:
        if not parsed_data.get("valid"):
            return {"success": False, "error": parsed_data.get("error", "Invalid session data")}

        provider = parsed_data["provider"]
        token = parsed_data["access_token"]
        email = parsed_data.get("email", "unknown")
        auth_type = parsed_data.get("auth_type", "oauth")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Deduplication check
        cur.execute("SELECT id, name FROM providerConnections WHERE provider = ? AND json_extract(data, '$.accessToken') = ?", (provider, token))
        existing = cur.fetchone()
        if existing:
            conn.close()
            return {"success": True, "status": "duplicate", "name": existing[1], "email": email}

        # Calculate max account index
        cur.execute("SELECT name FROM providerConnections WHERE provider = ?", (provider,))
        max_idx = 0
        for row in cur.fetchall():
            nm = row[0] or ""
            parts = nm.split()
            if len(parts) >= 2 and parts[1].isdigit():
                val = int(parts[1])
                if val > max_idx:
                    max_idx = val

        next_name = custom_name or f"Account {max_idx + 1}"
        new_id = str(uuid.uuid4())
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

        data_json = json.dumps({
            "accessToken": token,
            "refreshToken": token,
            "expiresAt": parsed_data.get("expires_at"),
            "testStatus": "active",
            "consecutiveUseCount": 0,
            "user": {
                "email": email,
                "sub": parsed_data.get("user_id")
            }
        })

        cur.execute("""
            INSERT INTO providerConnections (id, provider, authType, name, email, priority, isActive, data, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?, ?)
        """, (new_id, provider, auth_type, next_name, email, data_json, now_iso, now_iso))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "status": "inserted",
            "id": new_id,
            "name": next_name,
            "provider": provider,
            "email": email
        }
