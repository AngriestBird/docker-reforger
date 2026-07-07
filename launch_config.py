import copy
import json
import re


MOD_ID_LIST_RE = re.compile(r"^[A-Z\d,=.]+$")
MOD_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
PERSISTENCE_ENV_KEYS = (
    "PERSISTENCE_AUTO_SAVE_INTERVAL",
    "PERSISTENCE_SAVE_RETENTION",
    "PERSISTENCE_LOAD_SESSION_SAVE",
    "PERSISTENCE_KEEP_SESSION_SAVE",
    "PERSISTENCE_HIVE_ID",
    "PERSISTENCE_JSON_FILE_PATH",
)


def env_defined(env, key):
    return key in env and len(env[key]) > 0


def bool_str(text):
    return text.lower() == "true"


def split_csv(text):
    return [item.strip() for item in text.split(",") if item.strip()]


def parse_int(env, key):
    try:
        return int(env[key])
    except (KeyError, TypeError, ValueError) as err:
        raise ValueError(f"Invalid {key}: {env.get(key)!r}") from err


def load_json_file(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError) as err:
        raise ValueError(f"Failed to load {path}: {err}") from err


def build_config(env, base_config):
    config = copy.deepcopy(base_config)

    if env_defined(env, "SERVER_BIND_ADDRESS"):
        config["bindAddress"] = env["SERVER_BIND_ADDRESS"]
    if env_defined(env, "SERVER_BIND_PORT"):
        config["bindPort"] = parse_int(env, "SERVER_BIND_PORT")
    if env_defined(env, "SERVER_PUBLIC_ADDRESS"):
        config["publicAddress"] = env["SERVER_PUBLIC_ADDRESS"]
    if env_defined(env, "SERVER_PUBLIC_PORT"):
        config["publicPort"] = parse_int(env, "SERVER_PUBLIC_PORT")
    if env_defined(env, "SERVER_A2S_ADDRESS") and env_defined(env, "SERVER_A2S_PORT"):
        config["a2s"] = {
            "address": env["SERVER_A2S_ADDRESS"],
            "port": parse_int(env, "SERVER_A2S_PORT"),
        }
    else:
        config.pop("a2s", None)

    if (
        env_defined(env, "RCON_PASSWORD")
        and env_defined(env, "RCON_ADDRESS")
        and env_defined(env, "RCON_PORT")
    ):
        assert not (
            env_defined(env, "RCON_BLACKLIST") and env_defined(env, "RCON_WHITELIST")
        ), "RCON_BLACKLIST and RCON_WHITELIST cannot both be set"
        rcon = {
            "address": env["RCON_ADDRESS"],
            "port": parse_int(env, "RCON_PORT"),
            "password": env["RCON_PASSWORD"],
            "permission": env.get("RCON_PERMISSION")
            or config.get("rcon", {}).get("permission")
            or "admin",
        }
        if env_defined(env, "RCON_MAX_CLIENTS"):
            rcon["maxClients"] = parse_int(env, "RCON_MAX_CLIENTS")
        if env_defined(env, "RCON_BLACKLIST"):
            rcon["blacklist"] = split_csv(env["RCON_BLACKLIST"])
        if env_defined(env, "RCON_WHITELIST"):
            rcon["whitelist"] = split_csv(env["RCON_WHITELIST"])
        config["rcon"] = rcon
    else:
        config.pop("rcon", None)

    if env_defined(env, "GAME_NAME"):
        config["game"]["name"] = env["GAME_NAME"]
    if env_defined(env, "GAME_PASSWORD"):
        config["game"]["password"] = env["GAME_PASSWORD"]
    if env_defined(env, "GAME_PASSWORD_ADMIN"):
        config["game"]["passwordAdmin"] = env["GAME_PASSWORD_ADMIN"]
    if env_defined(env, "GAME_ADMINS"):
        config["game"]["admins"] = split_csv(env["GAME_ADMINS"])
    if env_defined(env, "GAME_SCENARIO_ID"):
        config["game"]["scenarioId"] = env["GAME_SCENARIO_ID"]
    if env_defined(env, "GAME_MAX_PLAYERS"):
        config["game"]["maxPlayers"] = parse_int(env, "GAME_MAX_PLAYERS")
    if env_defined(env, "GAME_VISIBLE"):
        config["game"]["visible"] = bool_str(env["GAME_VISIBLE"])
    if env_defined(env, "GAME_SUPPORTED_PLATFORMS"):
        config["game"]["supportedPlatforms"] = env["GAME_SUPPORTED_PLATFORMS"].split(
            ","
        )
    if env_defined(env, "GAME_CROSS_PLATFORM"):
        config["game"]["crossPlatform"] = bool_str(env["GAME_CROSS_PLATFORM"])
    mods_required_by_default = None
    if env_defined(env, "GAME_MODS_REQUIRED_BY_DEFAULT"):
        mods_required_by_default = bool_str(env["GAME_MODS_REQUIRED_BY_DEFAULT"])
        config["game"]["modsRequiredByDefault"] = mods_required_by_default
    if env_defined(env, "GAME_PROPS_BATTLEYE"):
        config["game"]["gameProperties"]["battlEye"] = bool_str(
            env["GAME_PROPS_BATTLEYE"]
        )
    if env_defined(env, "GAME_PROPS_DISABLE_THIRD_PERSON"):
        config["game"]["gameProperties"]["disableThirdPerson"] = bool_str(
            env["GAME_PROPS_DISABLE_THIRD_PERSON"]
        )
    if env_defined(env, "GAME_PROPS_FAST_VALIDATION"):
        config["game"]["gameProperties"]["fastValidation"] = bool_str(
            env["GAME_PROPS_FAST_VALIDATION"]
        )
    if env_defined(env, "GAME_PROPS_SERVER_MAX_VIEW_DISTANCE"):
        config["game"]["gameProperties"]["serverMaxViewDistance"] = parse_int(
            env, "GAME_PROPS_SERVER_MAX_VIEW_DISTANCE"
        )
    if env_defined(env, "GAME_PROPS_SERVER_MIN_GRASS_DISTANCE"):
        config["game"]["gameProperties"]["serverMinGrassDistance"] = parse_int(
            env, "GAME_PROPS_SERVER_MIN_GRASS_DISTANCE"
        )
    if env_defined(env, "GAME_PROPS_NETWORK_VIEW_DISTANCE"):
        config["game"]["gameProperties"]["networkViewDistance"] = parse_int(
            env, "GAME_PROPS_NETWORK_VIEW_DISTANCE"
        )
    if env_defined(env, "GAME_PROPS_VON_DISABLE_UI"):
        config["game"]["gameProperties"]["VONDisableUI"] = bool_str(
            env["GAME_PROPS_VON_DISABLE_UI"]
        )
    if env_defined(env, "GAME_PROPS_VON_DISABLE_DIRECT_SPEECH_UI"):
        config["game"]["gameProperties"]["VONDisableDirectSpeechUI"] = bool_str(
            env["GAME_PROPS_VON_DISABLE_DIRECT_SPEECH_UI"]
        )
    if env_defined(env, "GAME_PROPS_VON_CAN_TRANSMIT_CROSS_FACTION"):
        config["game"]["gameProperties"]["VONCanTransmitCrossFaction"] = bool_str(
            env["GAME_PROPS_VON_CAN_TRANSMIT_CROSS_FACTION"]
        )

    if env_defined(env, "GAME_MISSION_HEADER_JSON_FILE_PATH"):
        config["game"]["gameProperties"]["missionHeader"] = load_json_file(
            env["GAME_MISSION_HEADER_JSON_FILE_PATH"]
        )
    else:
        config["game"]["gameProperties"]["missionHeader"] = {}

    config["game"]["mods"] = []
    config_mod_ids = []
    if env_defined(env, "GAME_MODS_IDS_LIST"):
        assert MOD_ID_LIST_RE.match(
            env["GAME_MODS_IDS_LIST"]
        ), "Illegal characters in GAME_MODS_IDS_LIST env"
        for mod in split_csv(env["GAME_MODS_IDS_LIST"]):
            mod_details = mod.split("=")
            assert 0 < len(mod_details) < 3, f"{mod} mod not defined properly"
            mod_id = mod_details[0]
            if mod_id in config_mod_ids:
                continue
            mod_config = {"modId": mod_id}
            if len(mod_details) == 2:
                assert MOD_VERSION_RE.match(
                    mod_details[1]
                ), f"{mod} mod version does not match the pattern"
                mod_config["version"] = mod_details[1]
            if mods_required_by_default is not None:
                mod_config["required"] = mods_required_by_default
            config_mod_ids.append(mod_id)
            config["game"]["mods"].append(mod_config)
    if env_defined(env, "GAME_MODS_JSON_FILE_PATH"):
        json_mods = load_json_file(env["GAME_MODS_JSON_FILE_PATH"])
        allowed_keys = ["modId", "name", "version", "required"]
        for provided_mod in json_mods:
            assert (
                "modId" in provided_mod
            ), f"Entry in GAME_MODS_JSON_FILE_PATH file does not contain modId: {provided_mod}"
            if provided_mod["modId"] in config_mod_ids:
                continue
            valid_mod = {
                key: provided_mod[key] for key in allowed_keys if key in provided_mod
            }
            if mods_required_by_default is not None and "required" not in valid_mod:
                valid_mod["required"] = mods_required_by_default
            config_mod_ids.append(provided_mod["modId"])
            config["game"]["mods"].append(valid_mod)

    persistence_defined = any(env_defined(env, key) for key in PERSISTENCE_ENV_KEYS)
    if persistence_defined:
        persistence = {}
        if env_defined(env, "PERSISTENCE_AUTO_SAVE_INTERVAL"):
            persistence["autoSaveInterval"] = parse_int(
                env, "PERSISTENCE_AUTO_SAVE_INTERVAL"
            )
        if env_defined(env, "PERSISTENCE_SAVE_RETENTION"):
            persistence["saveRetention"] = parse_int(env, "PERSISTENCE_SAVE_RETENTION")
        if env_defined(env, "PERSISTENCE_LOAD_SESSION_SAVE"):
            persistence["loadSessionSave"] = bool_str(
                env["PERSISTENCE_LOAD_SESSION_SAVE"]
            )
        if env_defined(env, "PERSISTENCE_KEEP_SESSION_SAVE"):
            persistence["keepSessionSave"] = bool_str(
                env["PERSISTENCE_KEEP_SESSION_SAVE"]
            )
        if env_defined(env, "PERSISTENCE_HIVE_ID"):
            persistence["hiveId"] = parse_int(env, "PERSISTENCE_HIVE_ID")
        if env_defined(env, "PERSISTENCE_JSON_FILE_PATH"):
            persistence_json = load_json_file(env["PERSISTENCE_JSON_FILE_PATH"])
            allowed_keys = ["databases", "storages"]
            for key in allowed_keys:
                if key in persistence_json:
                    persistence[key] = persistence_json[key]
        config["game"]["gameProperties"]["persistence"] = persistence
    else:
        config["game"]["gameProperties"].pop("persistence", None)

    operating = {}
    if env_defined(env, "OPERATING_LOBBY_PLAYER_SYNCHRONISE"):
        operating["lobbyPlayerSynchronise"] = bool_str(
            env["OPERATING_LOBBY_PLAYER_SYNCHRONISE"]
        )
    if env_defined(env, "OPERATING_DISABLE_CRASH_REPORTER"):
        operating["disableCrashReporter"] = bool_str(
            env["OPERATING_DISABLE_CRASH_REPORTER"]
        )
    if env_defined(env, "OPERATING_DISABLE_NAVMESH_STREAMING"):
        val = env["OPERATING_DISABLE_NAVMESH_STREAMING"]
        if val.lower() == "all":
            operating["disableNavmeshStreaming"] = []
        else:
            operating["disableNavmeshStreaming"] = split_csv(val)
    if env_defined(env, "OPERATING_DISABLE_SERVER_SHUTDOWN"):
        operating["disableServerShutdown"] = bool_str(
            env["OPERATING_DISABLE_SERVER_SHUTDOWN"]
        )
    if env_defined(env, "OPERATING_DISABLE_AI"):
        operating["disableAI"] = bool_str(env["OPERATING_DISABLE_AI"])
    if env_defined(env, "OPERATING_PLAYER_SAVE_TIME"):
        operating["playerSaveTime"] = parse_int(env, "OPERATING_PLAYER_SAVE_TIME")
    if env_defined(env, "OPERATING_AI_LIMIT"):
        operating["aiLimit"] = parse_int(env, "OPERATING_AI_LIMIT")
    if env_defined(env, "OPERATING_SLOT_RESERVATION_TIMEOUT"):
        operating["slotReservationTimeout"] = parse_int(
            env, "OPERATING_SLOT_RESERVATION_TIMEOUT"
        )
    if env_defined(env, "OPERATING_JOIN_QUEUE_MAX_SIZE"):
        operating["joinQueue"] = {
            "maxSize": parse_int(env, "OPERATING_JOIN_QUEUE_MAX_SIZE")
        }
    if operating:
        config["operating"] = operating
    else:
        config.pop("operating", None)

    return config
