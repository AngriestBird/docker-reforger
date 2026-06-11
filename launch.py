import json
import os
import random
import shlex
import signal
import subprocess
import sys
from pathlib import Path

from launch_config import build_config, env_defined

# On SIGTERM, raise KeyboardInterrupt instead of exiting abruptly.
signal.signal(signal.SIGTERM, signal.default_int_handler)

CONFIG_GENERATED = "/reforger/Configs/docker_generated.json"


def random_passphrase():
    password = "'"
    while "'" in password:
        with open("/usr/share/dict/american-english") as f:
            words = f.readlines()
        password = "-".join(random.sample(words, 2)).replace("\n", "").lower()
    return password


SENTINEL_WINDOWS_FIX = "/reforger/.windows_fix_done"

# Clear Windows fix sentinel if switching away from experimental appId
if Path(SENTINEL_WINDOWS_FIX).exists() and os.environ["STEAM_APPID"] != "1890870":
    Path(SENTINEL_WINDOWS_FIX).unlink()

if os.environ["SKIP_INSTALL"] in ["", "false"]:
    # Warm up SteamCMD (first run self-updates and may exit non-zero).
    subprocess.call(["/steamcmd/steamcmd.sh", "+login", "anonymous", "+quit"])

    # Special handling for experimental appId 1890870
    if os.environ["STEAM_APPID"] == "1890870":
        # Only run the Windows pass once; subsequent launches use Linux.
        run_windows_pass = not Path(SENTINEL_WINDOWS_FIX).exists()

        if run_windows_pass:
            steamcmd_win = ["/steamcmd/steamcmd.sh"]
            steamcmd_win.extend(["+force_install_dir", "/reforger"])
            if env_defined(os.environ, "STEAM_USER"):
                steamcmd_win.extend(
                    ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
                )
            else:
                steamcmd_win.extend(["+login", "anonymous"])
            steamcmd_win.extend(["+@sSteamCmdForcePlatformType", "windows"])
            steamcmd_win.extend(["+app_update", os.environ["STEAM_APPID"]])
            if env_defined(os.environ, "STEAM_BRANCH"):
                steamcmd_win.extend(["-beta", os.environ["STEAM_BRANCH"]])
            if env_defined(os.environ, "STEAM_BRANCH_PASSWORD"):
                steamcmd_win.extend(
                    ["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]]
                )
            steamcmd_win.extend(["validate", "+quit"])
            subprocess.call(steamcmd_win)
            Path(SENTINEL_WINDOWS_FIX).touch()

        # Install with Linux platform
        steamcmd_linux = ["/steamcmd/steamcmd.sh"]
        steamcmd_linux.extend(["+force_install_dir", "/reforger"])
        if env_defined(os.environ, "STEAM_USER"):
            steamcmd_linux.extend(
                ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
            )
        else:
            steamcmd_linux.extend(["+login", "anonymous"])
        steamcmd_linux.extend(["+@sSteamCmdForcePlatformType", "linux"])
        steamcmd_linux.extend(["+app_update", os.environ["STEAM_APPID"]])
        if env_defined(os.environ, "STEAM_BRANCH"):
            steamcmd_linux.extend(["-beta", os.environ["STEAM_BRANCH"]])
        if env_defined(os.environ, "STEAM_BRANCH_PASSWORD"):
            steamcmd_linux.extend(
                ["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]]
            )
        steamcmd_linux.extend(["validate", "+quit"])
        subprocess.call(steamcmd_linux)
    else:
        steamcmd = ["/steamcmd/steamcmd.sh"]
        steamcmd.extend(["+force_install_dir", "/reforger"])
        if env_defined(os.environ, "STEAM_USER"):
            steamcmd.extend(
                ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
            )
        else:
            steamcmd.extend(["+login", "anonymous"])
        steamcmd.extend(["+app_update", os.environ["STEAM_APPID"]])
        if env_defined(os.environ, "STEAM_BRANCH"):
            steamcmd.extend(["-beta", os.environ["STEAM_BRANCH"]])
        if env_defined(os.environ, "STEAM_BRANCH_PASSWORD"):
            steamcmd.extend(
                ["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]]
            )
        steamcmd.extend(["validate", "+quit"])
        subprocess.call(steamcmd)

if os.environ["ARMA_CONFIG"] != "docker_generated":
    config_path = f"/reforger/Configs/{os.environ['ARMA_CONFIG']}"
else:
    if os.path.exists(CONFIG_GENERATED):
        with open(CONFIG_GENERATED) as f:
            config = json.load(f)
    else:
        with open("/docker_default.json") as f:
            config = json.load(f)

    config = build_config(os.environ, config)

    # Admin password is generated if not provided, and printed for user reference.
    if not env_defined(os.environ, "GAME_PASSWORD_ADMIN"):
        config["game"]["passwordAdmin"] = random_passphrase()
        print(f"Admin password: {config['game']['passwordAdmin']}")

    with open(CONFIG_GENERATED, "w") as f:
        json.dump(config, f, indent=4)

    config_path = CONFIG_GENERATED

launch = [
    os.environ["ARMA_BINARY"],
    "-config",
    config_path,
    "-backendlog",
    "-nothrow",
    "-maxFPS",
    os.environ["ARMA_MAX_FPS"],
    "-profile",
    os.environ["ARMA_PROFILE"],
    "-addonDownloadDir",
    os.environ["ARMA_WORKSHOP_DIR"],
    "-addonsDir",
    os.environ["ARMA_WORKSHOP_DIR"],
    *shlex.split(os.environ["ARMA_PARAMS"]),
]

print(shlex.join(launch), flush=True)

proc = subprocess.Popen(launch)

try:
    try:
        sys.exit(proc.wait())
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        sys.exit(proc.wait())
except SystemExit:
    raise
except BaseException:
    proc.kill()
    raise
