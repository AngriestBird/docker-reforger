"""Simple A2S_INFO health check for Arma Reforger server.

Sends a minimal A2S_INFO query to localhost and checks for any response.
Uses only the standard library (no pip dependencies).
"""

import socket
import sys

A2S_INFO_REQUEST = b"\xFF\xFF\xFF\xFF\x54Source Engine Query\x00"
SERVER_ADDRESS = ("127.0.0.1", 17777)
TIMEOUT_SECONDS = 5

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT_SECONDS)
    sock.sendto(A2S_INFO_REQUEST, SERVER_ADDRESS)
    data, _ = sock.recvfrom(4096)
    sock.close()
    if len(data) > 0:
        sys.exit(0)
    sys.exit(1)
except Exception:
    sys.exit(1)
