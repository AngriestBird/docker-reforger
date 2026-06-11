import json
import os
import re


def env_defined(env, key):
    return key in env and len(env[key]) > 0


def bool_str(text):
    return text.lower() == "true"


def build_config(env, base_config):
    config = json.loads(json.dumps(base_config))

    if env_defined(env, "SERVER_BIND_ADDRESS"):
        config["bindAddress"] = env["SERVER_BIND_ADDRESS"]
    if env_defined(env, "SERVER_BIND_PORT"):
        config["bindPort"] = int(env["SERVER_BIND_PORT"])
    if env_defined(env, "SERVER_PUBLIC_ADDRESS"):
        config["publicAddress"] = env["SERVER_PUBLIC_ADDRESS"]
    if env_defined(env, "SERVER_PUBLIC_PORT"):
        config["publicPort"] = int(env["SERVER_PUBLIC_PORT"])
    if env_defined(env, "SERVER_A2S_ADDRESS") and env_defined(env, "SERVER_A2S_PORT"):
        config["a2s"] = {
            "address": env["SERVER_A2S_ADDRESS"],
            "port": int(env["SERVER_A2S_PORT"]),
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
            "port": int(env["RCON_PORT"]),
            "password": env["RCON_PASSWORD"],
            "permission": env["RCON_PERMISSION"],
        }
        if env_defined(env, "RCON_MAX_CLIENTS"):
            rcon["maxClients"] = int(env["RCON_MAX_CLIENTS"])
        if env_defined(env, "RCON_BLACKLIST"):
            rcon["blacklist"] = [
                cmd.strip()
                for cmd in env["RCON_BLACKLIST"].split(",")
                if cmd.strip()
            ]
        if env_defined(env, "RCON_WHITELIST"):
            rcon["whitelist"] = [
                cmd.strip()
                for cmd in env["RCON_WHITELIST"].split(",")
                if cmd.strip()
            ]
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
        admins = env["GAME_ADMINS"].split(",")
        admins[:] = [admin for admin in admins if admin]
        config["game"]["admins"] = admins
    if env_defined(env, "GAME_SCENARIO_ID"):
        config["game"]["scenarioId"] = env["GAME_SCENARIO_ID"]
    if env_defined(env, "GAME_MAX_PLAYERS"):
        config["game"]["maxPlayers"] = int(env["GAME_MAX_PLAYERS"])
    if env_defined(env, "GAME_VISIBLE"):
        config["game"]["visible"] = bool_str(env["GAME_VISIBLE"])
    if env_defined(env, "GAME_SUPPORTED_PLATFORMS"):
        config["game"]["supportedPlatforms"] = env[
            "GAME_SUPPORTED_PLATFORMS"
        ].split(",")
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
        config["game"]["gameProperties"]["serverMaxViewDistance"] = int(
            env["GAME_PROPS_SERVER_MAX_VIEW_DISTANCE"]
        )
    if env_defined(env, "GAME_PROPS_SERVER_MIN_GRASS_DISTANCE"):
        config["game"]["gameProperties"]["serverMinGrassDistance"] = int(
            env["GAME_PROPS_SERVER_MIN_GRASS_DISTANCE"]
        )
    if env_defined(env, "GAME_PROPS_NETWORK_VIEW_DISTANCE"):
        config["game"]["gameProperties"]["networkViewDistance"] = int(
            env["GAME_PROPS_NETWORK_VIEW_DISTANCE"]
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
        with open(env["GAME_MISSION_HEADER_JSON_FILE_PATH"]) as f:
            config["game"]["gameProperties"]["missionHeader"] = json.load(f)

    config["game"]["mods"] = []
    config_mod_ids = []
    if env_defined(env, "GAME_MODS_IDS_LIST"):
        reg = re.compile(r"^[A-Z\d,=.]+$")
        assert reg.match(
            env["GAME_MODS_IDS_LIST"]
        ), "Illegal characters in GAME_MODS_IDS_LIST env"
        mods = env["GAME_MODS_IDS_LIST"].split(",")
        mods[:] = [mod for mod in mods if mod]
        reg = re.compile(r"^\d+\.\d+\.\d+$")
        for mod in mods:
            mod_details = mod.split("=")
            assert 0 < len(mod_details) < 3, f"{mod} mod not defined properly"
            mod_id = mod_details[0]
            if mod_id in config_mod_ids:
                continue
            mod_config = {"modId": mod_id}
            if len(mod_details) == 2:
                assert reg.match(
                    mod_details[1]
                ), f"{mod} mod version does not match the pattern"
                mod_config["version"] = mod_details[1]
            if mods_required_by_default is not None:
                mod_config["required"] = mods_required_by_default
            config_mod_ids.append(mod_id)
            config["game"]["mods"].append(mod_config)
    if env_defined(env, "GAME_MODS_JSON_FILE_PATH"):
        with open(env["GAME_MODS_JSON_FILE_PATH"]) as f:
            json_mods = json.load(f)
            allowed_keys = ["modId", "name", "version", "required"]
            for provided_mod in json_mods:
                assert (
                    "modId" in provided_mod
                ), f"Entry in GAME_MODS_JSON_FILE_PATH file does not contain modId: {provided_mod}"
                if provided_mod["modId"] in config_mod_ids:
                    continue
                valid_mod = {
                    key: provided_mod[key]
                    for key in allowed_keys
                    if key in provided_mod
                }
                if mods_required_by_default is not None and "required" not in valid_mod:
                    valid_mod["required"] = mods_required_by_default
                config_mod_ids.append(provided_mod["modId"])
                config["game"]["mods"].append(valid_mod)

    persistence_defined = (
        env_defined(env, "PERSISTENCE_AUTO_SAVE_INTERVAL")
        or env_defined(env, "PERSISTENCE_SAVE_RETENTION")
        or env_defined(env, "PERSISTENCE_LOAD_SESSION_SAVE")
        or env_defined(env, "PERSISTENCE_KEEP_SESSION_SAVE")
        or env_defined(env, "PERSISTENCE_HIVE_ID")
        or env_defined(env, "PERSISTENCE_JSON_FILE_PATH")
    )
    if persistence_defined:
        persistence = {}
        if env_defined(env, "PERSISTENCE_AUTO_SAVE_INTERVAL"):
            persistence["autoSaveInterval"] = int(
                env["PERSISTENCE_AUTO_SAVE_INTERVAL"]
            )
        if env_defined(env, "PERSISTENCE_SAVE_RETENTION"):
            persistence["saveRetention"] = int(
                env["PERSISTENCE_SAVE_RETENTION"]
            )
        if env_defined(env, "PERSISTENCE_LOAD_SESSION_SAVE"):
            persistence["loadSessionSave"] = bool_str(
                env["PERSISTENCE_LOAD_SESSION_SAVE"]
            )
        if env_defined(env, "PERSISTENCE_KEEP_SESSION_SAVE"):
            persistence["keepSessionSave"] = bool_str(
                env["PERSISTENCE_KEEP_SESSION_SAVE"]
            )
        if env_defined(env, "PERSISTENCE_HIVE_ID"):
            persistence["hiveId"] = int(env["PERSISTENCE_HIVE_ID"])
        if env_defined(env, "PERSISTENCE_JSON_FILE_PATH"):
            with open(env["PERSISTENCE_JSON_FILE_PATH"]) as f:
                persistence_json = json.load(f)
                allowed_keys = ["databases", "storages"]
                for key in allowed_keys:
                    if key in persistence_json:
                        persistence[key] = persistence_json[key]
        config["game"]["gameProperties"]["persistence"] = persistence

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
            operating["disableNavmeshStreaming"] = [
                name.strip() for name in val.split(",") if name.strip()
            ]
    if env_defined(env, "OPERATING_DISABLE_SERVER_SHUTDOWN"):
        operating["disableServerShutdown"] = bool_str(
            env["OPERATING_DISABLE_SERVER_SHUTDOWN"]
        )
    if env_defined(env, "OPERATING_DISABLE_AI"):
        operating["disableAI"] = bool_str(
            env["OPERATING_DISABLE_AI"]
        )
    if env_defined(env, "OPERATING_PLAYER_SAVE_TIME"):
        operating["playerSaveTime"] = int(env["OPERATING_PLAYER_SAVE_TIME"])
    if env_defined(env, "OPERATING_AI_LIMIT"):
        operating["aiLimit"] = int(env["OPERATING_AI_LIMIT"])
    if env_defined(env, "OPERATING_SLOT_RESERVATION_TIMEOUT"):
        operating["slotReservationTimeout"] = int(
            env["OPERATING_SLOT_RESERVATION_TIMEOUT"]
        )
    if env_defined(env, "OPERATING_JOIN_QUEUE_MAX_SIZE"):
        operating["joinQueue"] = {
            "maxSize": int(env["OPERATING_JOIN_QUEUE_MAX_SIZE"])
        }
    if operating:
        config["operating"] = operating

    return config
