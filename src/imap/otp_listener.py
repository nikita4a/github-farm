"""
IMAP Real-Time OTP Listener
Connects to secure SSL IMAP endpoints and extracts verification codes using Regex.
Author: D4NNBOZ
License: MIT
"""

import imaplib
import email
import re
import time
from typing import Optional

class ImapOtpListener:
    def __init__(self, server: str, username: str, password: str, port: int = 993):
        self.server = server
        self.port = port
        self.username = username
        self.password = password.replace(" ", "").strip()

    def connect(self) -> imaplib.IMAP4_SSL:
        mail = imaplib.IMAP4_SSL(self.server, self.port)
        mail.login(self.username, self.password)
        return mail

    def listen_github_otp(self, target_email: Optional[str] = None, timeout_sec: int = 120, poll_interval: int = 4) -> Optional[str]:
        """Polls IMAP inbox for GitHub verification emails and extracts 8-digit OTP code."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                mail = self.connect()
                mail.select("INBOX")
                status, messages = mail.search(None, '(FROM "github.com")')
                if status == "OK" and messages[0]:
                    msg_ids = messages[0].split()
                    for msg_id in reversed(msg_ids[-3:]):
                        _, msg_data = mail.fetch(msg_id, "(RFC822)")
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() in ["text/plain", "text/html"]:
                                    body += part.get_payload(decode=True).decode(errors="ignore")
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")

                        if target_email:
                            to_field = msg.get("To", "") + msg.get("Delivered-To", "")
                            if target_email.replace(".", "") not in to_field.replace(".", ""):
                                continue

                        otp_match = re.search(r"\b(\d{8})\b", body) or re.search(r"\b(\d{6})\b", body)
                        if otp_match:
                            code = otp_match.group(1)
                            mail.close()
                            mail.logout()
                            return code
                            
                mail.close()
                mail.logout()
            except Exception:
                pass
                
            time.sleep(poll_interval)
            
        return None
