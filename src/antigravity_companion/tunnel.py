import socket
import logging
import threading
import time
from typing import Tuple, Optional
from .config import config

logger = logging.getLogger("antigravity_companion.tunnel")

current_tunnel_url: Optional[str] = None
_ngrok_listener = None

def get_local_ip() -> str:
    """Gets the LAN IP address of this desktop machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def _start_ngrok_tunnel(port: int):
    global current_tunnel_url, _ngrok_listener
    try:
        import ngrok
        logger.info("Initializing persistent Ngrok tunnel with user authtoken...")
        _ngrok_listener = ngrok.forward(port, authtoken=config.ngrok_authtoken)
        base_url = _ngrok_listener.url()
        current_tunnel_url = f"{base_url}/?token={config.secret_token}"
        logger.info(f"🚀 Permanent Ngrok Tunnel Active: {current_tunnel_url}")
    except Exception as e:
        logger.error(f"Failed to start ngrok tunnel: {e}. Falling back to Cloudflare...")
        _start_cloudflare_tunnel(port)

def _start_cloudflare_tunnel(port: int):
    global current_tunnel_url
    try:
        from pycloudflared import try_cloudflare
        t = try_cloudflare(port=port)
        tunnel_endpoint = getattr(t, "tunnel", None) or getattr(t, "tunnel_url", None) or str(t)
        current_tunnel_url = f"{tunnel_endpoint}/?token={config.secret_token}"
        logger.info(f"Cloudflare Tunnel ready: {current_tunnel_url}")
    except Exception as e:
        logger.warning(f"Cloudflare tunnel error: {e}")

def start_tunnel(port: int) -> Tuple[str, Optional[str]]:
    local_ip = get_local_ip()
    local_url = f"http://{local_ip}:{port}/?token={config.secret_token}"
    global current_tunnel_url

    if config.enable_tunnel:
        if config.tunnel_provider == "ngrok" and config.ngrok_authtoken:
            _start_ngrok_tunnel(port)
        else:
            t = threading.Thread(target=_start_cloudflare_tunnel, args=(port,), daemon=True)
            t.start()
            for _ in range(24):
                if current_tunnel_url:
                    break
                time.sleep(0.5)

    return local_url, current_tunnel_url
