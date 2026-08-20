"""
CLI Entrypoint for GitHub OAuth Harvester Suite
Author: D4NNBOZ
License: MIT
"""

import argparse
import sys
import os
import json
from src.generator.email_engine import generate_dot_trick_emails, generate_plus_address_emails
from src.imap.otp_listener import ImapOtpListener
from src.adapters.adapters import CodeBuddyAdapter, GoRouterAdapter, TabiAIAdapter
from src.injector.db_injector import DatabaseInjector

def main():
    parser = argparse.ArgumentParser(description="GitHub OAuth Multi-Platform Harvesting Framework")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: generate
    p_gen = subparsers.add_parser("generate", help="Generate Dot-Trick or Plus-Addressing email aliases")
    p_gen.add_argument("--user", required=True, help="Base username")
    p_gen.add_argument("--domain", default="gmail.com", help="Email domain (e.g. gmail.com, proton.me)")
    p_gen.add_argument("--type", choices=["dot", "plus"], default="dot", help="Aliasing algorithm")
    p_gen.add_argument("--count", type=int, default=20, help="Number of email variations")
    p_gen.add_argument("--json", action="store_true", help="Output pure JSON array")

    # Command: listen-otp
    p_otp = subparsers.add_parser("listen-otp", help="Real-time IMAP listener for GitHub 8-digit verification OTP")
    p_otp.add_argument("--user", required=True, help="Master IMAP email address")
    p_otp.add_argument("--password", required=True, help="16-digit Google App Password")
    p_otp.add_argument("--server", default="imap.gmail.com", help="IMAP server hostname")
    p_otp.add_argument("--target", help="Specific alias email filter")
    p_otp.add_argument("--timeout", type=int, default=60, help="Polling timeout in seconds")
    p_otp.add_argument("--json", action="store_true", help="Output pure JSON response")

    # Command: inject
    p_inj = subparsers.add_parser("inject", help="Inject harvested OAuth session into 9Router SQLite")
    p_inj.add_argument("--platform", choices=["codebuddy", "gorouter", "tabiai"], required=True, help="Target platform")
    p_inj.add_argument("--token", required=True, help="Raw JWT / Access Token")
    p_inj.add_argument("--email", default="user@oauth", help="Account email identifier")
    p_inj.add_argument("--json", action="store_true", help="Output pure JSON response")

    args = parser.parse_args()

    if args.command == "generate":
        if args.type == "dot":
            emails = generate_dot_trick_emails(args.user, args.domain, args.count)
        else:
            emails = generate_plus_address_emails(args.user, args.domain, "gh", args.count)

        if args.json:
            print(json.dumps({"status": "ok", "count": len(emails), "emails": emails}, indent=2))
        else:
            print(f"\n[+] Generated {len(emails)} {args.type.upper()} email variations for '{args.user}@{args.domain}':\n")
            for idx, em in enumerate(emails, 1):
                print(f" {idx:2d}. {em}")

    elif args.command == "listen-otp":
        listener = ImapOtpListener(args.server, args.user, args.password)
        code = listener.listen_github_otp(target_email=args.target, timeout_sec=args.timeout)
        if args.json:
            print(json.dumps({"status": "ok" if code else "timeout", "otp_code": code}, indent=2))
        else:
            if code:
                print(f"\n[SUCCESS] GitHub OTP Verification Code Captured: {code}")
            else:
                print(f"\n[!] Polling timed out. No new GitHub OTP email detected.")

    elif args.command == "inject":
        if args.platform == "codebuddy":
            adapter = CodeBuddyAdapter()
            parsed = adapter.parse_session(args.token)
        elif args.platform == "gorouter":
            adapter = GoRouterAdapter()
            parsed = adapter.parse_session(args.token, args.email)
        elif args.platform == "tabiai":
            adapter = TabiAIAdapter()
            parsed = adapter.parse_session(args.token, args.email)

        injector = DatabaseInjector()
        res = injector.inject_session(parsed)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res.get("success"):
                print(f"\n[SUCCESS] Injected {res.get('provider')} -> {res.get('name')} ({res.get('email')}) [{res.get('status').upper()}]")
            else:
                print(f"\n[ERROR] Injection failed: {res.get('error')}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
