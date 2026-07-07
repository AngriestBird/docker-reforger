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
DEFAULT_CONFIG = "/docker_default.json"
EXPERIMENTAL_APPID = "1890870"
STEAMCMD = "/steamcmd/steamcmd.sh"
SENTINEL_WINDOWS_FIX = Path("/reforger/.windows_fix_done")


def random_passphrase():
    passphrase = "'"
    while "'" in passphrase:
        try:
            with open("/usr/share/dict/american-english") as f:
                words = f.readlines()
        except OSError as err:
            raise SystemExit(f"Failed to read word list: {err}") from err
        passphrase = "-".join(random.sample(words, 2)).replace("\n", "").lower()
    return passphrase


def build_steamcmd_command(force_platform=None):
    command = [STEAMCMD, "+force_install_dir", "/reforger"]
    if env_defined(os.environ, "STEAM_USER"):
        command.extend(
            ["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]]
        )
    else:
        command.extend(["+login", "anonymous"])
    if force_platform is not None:
        command.extend(["+@sSteamCmdForcePlatformType", force_platform])
    command.extend(["+app_update", os.environ["STEAM_APPID"]])
    if env_defined(os.environ, "STEAM_BRANCH"):
        command.extend(["-beta", os.environ["STEAM_BRANCH"]])
    if env_defined(os.environ, "STEAM_BRANCH_PASSWORD"):
        command.extend(["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]])
    command.extend(["validate", "+quit"])
    return command


def build_generated_config():
    try:
        with open(DEFAULT_CONFIG) as f:
            config = json.load(f)
    except (OSError, ValueError) as err:
        raise SystemExit(f"Failed to load {DEFAULT_CONFIG}: {err}") from err

    config = build_config(os.environ, config)

    if not env_defined(os.environ, "GAME_PASSWORD_ADMIN"):
        config["game"]["passwordAdmin"] = random_passphrase()
        print(f"Admin password: {config['game']['passwordAdmin']}")

    try:
        with open(CONFIG_GENERATED, "w") as f:
            json.dump(config, f, indent=4)
    except OSError as err:
        raise SystemExit(f"Failed to write {CONFIG_GENERATED}: {err}") from err

    return CONFIG_GENERATED


is_experimental = os.environ["STEAM_APPID"] == EXPERIMENTAL_APPID

# Clear Windows fix sentinel if switching away from experimental appId
if SENTINEL_WINDOWS_FIX.exists() and not is_experimental:
    SENTINEL_WINDOWS_FIX.unlink()

if os.environ["SKIP_INSTALL"] in ["", "false"]:
    # Warm up SteamCMD first. Its initial run self-updates and can exit non-zero,
    # so we get that out of the way here before the real app_update calls below.
    subprocess.call([STEAMCMD, "+login", "anonymous", "+quit"])

    if is_experimental:
        if not SENTINEL_WINDOWS_FIX.exists():
            subprocess.call(build_steamcmd_command("windows"))
            SENTINEL_WINDOWS_FIX.touch()

        subprocess.call(build_steamcmd_command("linux"))
    else:
        subprocess.call(build_steamcmd_command())

if os.environ["ARMA_CONFIG"] != "docker_generated":
    config_path = f"/reforger/Configs/{os.environ['ARMA_CONFIG']}"
else:
    config_path = build_generated_config()

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
    sys.exit(proc.wait())
except KeyboardInterrupt:
    proc.send_signal(signal.SIGINT)
    sys.exit(proc.wait())
except SystemExit:
    raise
except BaseException:
    proc.kill()
    raise
