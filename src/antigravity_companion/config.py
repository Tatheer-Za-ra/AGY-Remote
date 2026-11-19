import os
import json
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

class CompanionConfig:
    def __init__(self):
        self.port = int(os.getenv("COMPANION_PORT", "8765"))
        # Security Token for PWA access (generated if missing)
        self.secret_token = os.getenv("COMPANION_SECRET_TOKEN", "").strip()
        if not self.secret_token:
            self.secret_token = secrets.token_urlsafe(16)
            
        # Tunnel options: "ngrok", "cloudflare", "none"
        self.enable_tunnel = os.getenv("ENABLE_TUNNEL", "true").lower() in ("true", "1", "yes")
        self.tunnel_provider = os.getenv("TUNNEL_PROVIDER", "ngrok").lower()
        self.ngrok_authtoken = os.getenv("NGROK_AUTHTOKEN", "").strip()
        self.ngrok_domain = os.getenv("NGROK_DOMAIN", "mocha-judo-powdery.ngrok-free.dev").strip()

    def validate(self):
        return True

config = CompanionConfig()
