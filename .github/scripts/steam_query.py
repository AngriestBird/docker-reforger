import sys
import time

import a2s

SERVER_ADDRESS = ("127.0.0.1", 17777)

ATTEMPTS = 250
SLEEP = 0.5


def main():
    print(f"Looking for server (will try {ATTEMPTS} attempts)...")
    for _ in range(ATTEMPTS):
        try:
            info = a2s.info(SERVER_ADDRESS)
        except (OSError, a2s.BrokenMessageError) as err:
            print(err)
            time.sleep(SLEEP)
            continue
        print("Server found")
        print(f"Game: {info.game}")
        print(f"Map: {info.map_name}")
        print(f"Version: {info.version}")
        return 0

    print("Server not found")
    return 1


sys.exit(main())
