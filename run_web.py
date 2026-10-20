"""Trình khởi chạy Web App LEO-COORD.
Sử dụng Uvicorn để chạy FastAPI server trên cổng 8000.
"""
import sys
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import socket
import uvicorn


def get_local_ip() -> str:
    """Lấy địa chỉ IP nội bộ của máy trong mạng LAN / Wi-Fi."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port: int = 8098) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
            port += 1
    return start_port


if __name__ == "__main__":
    import os
    env_port = os.getenv("PORT")
    requested_port = int(env_port) if env_port and env_port.isdigit() else 8098
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        requested_port = int(sys.argv[1])
    
    port = find_available_port(requested_port)
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{port}"
    share_url = f"http://{local_ip}:{port}"

    print("=" * 70)
    print("🛰️  KHỞI ĐỘNG HỆ THỐNG LEO-COORD MISSION CONTROL WEB APP")
    if port != requested_port:
        print(f"⚠️  Cổng {requested_port} đang bận, hệ thống tự động chuyển sang cổng: {port}")
    print(f"👉 Truy cập cục bộ trên máy này : {local_url}")
    print(f"👉 ĐỊA CHỈ IP CHIA SẺ (MẠNG LAN/WI-FI): {share_url}")
    print("=" * 70)
    
    try:
        webbrowser.open(local_url)
    except Exception:
        pass
        
    uvicorn.run("web.app:app", host="0.0.0.0", port=port, reload=False)
