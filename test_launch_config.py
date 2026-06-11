import json

import pytest

from launch_config import bool_str, build_config, env_defined


@pytest.fixture
def base_config():
    with open("docker_default.json") as f:
        return json.load(f)


def test_env_defined():
    assert env_defined({"FOO": "bar"}, "FOO")
    assert not env_defined({"FOO": ""}, "FOO")
    assert not env_defined({}, "FOO")


def test_bool_str():
    assert bool_str("true")
    assert bool_str("TRUE")
    assert bool_str("True")
    assert not bool_str("false")
    assert not bool_str("")
    assert not bool_str("yes")


def test_defaults_preserved(base_config):
    env = {}
    config = build_config(env, base_config)
    assert config["game"]["name"] == "Arma Reforger Docker Server"
    assert config["game"]["maxPlayers"] == 64
    assert config["bindPort"] == 2001


def test_server_overrides(base_config):
    env = {
        "SERVER_BIND_ADDRESS": "127.0.0.1",
        "SERVER_BIND_PORT": "3001",
        "SERVER_PUBLIC_ADDRESS": "1.2.3.4",
        "SERVER_PUBLIC_PORT": "3002",
    }
    config = build_config(env, base_config)
    assert config["bindAddress"] == "127.0.0.1"
    assert config["bindPort"] == 3001
    assert config["publicAddress"] == "1.2.3.4"
    assert config["publicPort"] == 3002


def test_a2s_config(base_config):
    env = {
        "SERVER_A2S_ADDRESS": "0.0.0.0",
        "SERVER_A2S_PORT": "17777",
    }
    config = build_config(env, base_config)
    assert config["a2s"]["address"] == "0.0.0.0"
    assert config["a2s"]["port"] == 17777


def test_a2s_removed_when_partial(base_config):
    env = {"SERVER_A2S_ADDRESS": "0.0.0.0"}
    config = build_config(env, base_config)
    assert "a2s" not in config


def test_rcon_config(base_config):
    env = {
        "RCON_ADDRESS": "0.0.0.0",
        "RCON_PORT": "19999",
        "RCON_PASSWORD": "secret",
        "RCON_PERMISSION": "admin",
        "RCON_MAX_CLIENTS": "10",
    }
    config = build_config(env, base_config)
    assert config["rcon"]["address"] == "0.0.0.0"
    assert config["rcon"]["port"] == 19999
    assert config["rcon"]["password"] == "secret"
    assert config["rcon"]["permission"] == "admin"
    assert config["rcon"]["maxClients"] == 10


def test_rcon_blacklist(base_config):
    env = {
        "RCON_ADDRESS": "0.0.0.0",
        "RCON_PORT": "19999",
        "RCON_PASSWORD": "secret",
        "RCON_PERMISSION": "admin",
        "RCON_BLACKLIST": "kick,ban",
    }
    config = build_config(env, base_config)
    assert config["rcon"]["blacklist"] == ["kick", "ban"]


def test_rcon_whitelist(base_config):
    env = {
        "RCON_ADDRESS": "0.0.0.0",
        "RCON_PORT": "19999",
        "RCON_PASSWORD": "secret",
        "RCON_PERMISSION": "admin",
        "RCON_WHITELIST": "help,status",
    }
    config = build_config(env, base_config)
    assert config["rcon"]["whitelist"] == ["help", "status"]


def test_rcon_blacklist_and_whitelist_fails(base_config):
    env = {
        "RCON_ADDRESS": "0.0.0.0",
        "RCON_PORT": "19999",
        "RCON_PASSWORD": "secret",
        "RCON_PERMISSION": "admin",
        "RCON_BLACKLIST": "kick",
        "RCON_WHITELIST": "help",
    }
    with pytest.raises(AssertionError, match="cannot both be set"):
        build_config(env, base_config)


def test_game_overrides(base_config):
    env = {
        "GAME_NAME": "My Server",
        "GAME_PASSWORD": "mypassword",
        "GAME_SCENARIO_ID": "{FOO}Missions/01.conf",
        "GAME_MAX_PLAYERS": "32",
        "GAME_VISIBLE": "false",
        "GAME_CROSS_PLATFORM": "true",
    }
    config = build_config(env, base_config)
    assert config["game"]["name"] == "My Server"
    assert config["game"]["password"] == "mypassword"
    assert config["game"]["scenarioId"] == "{FOO}Missions/01.conf"
    assert config["game"]["maxPlayers"] == 32
    assert config["game"]["visible"] is False
    assert config["game"]["crossPlatform"] is True


def test_game_admins(base_config):
    env = {"GAME_ADMINS": "admin1,admin2,,admin3"}
    config = build_config(env, base_config)
    assert config["game"]["admins"] == ["admin1", "admin2", "admin3"]


def test_game_supported_platforms(base_config):
    env = {"GAME_SUPPORTED_PLATFORMS": "PLATFORM_PC,PLATFORM_XBL"}
    config = build_config(env, base_config)
    assert config["game"]["supportedPlatforms"] == ["PLATFORM_PC", "PLATFORM_XBL"]


def test_mods_required_by_default(base_config):
    env = {"GAME_MODS_REQUIRED_BY_DEFAULT": "true"}
    config = build_config(env, base_config)
    assert config["game"]["modsRequiredByDefault"] is True


def test_mods_ids_list(base_config):
    env = {"GAME_MODS_IDS_LIST": "12345=1.0.0,67890"}
    config = build_config(env, base_config)
    assert len(config["game"]["mods"]) == 2
    assert config["game"]["mods"][0] == {"modId": "12345", "version": "1.0.0"}
    assert config["game"]["mods"][1] == {"modId": "67890"}


def test_mods_ids_list_with_required(base_config):
    env = {
        "GAME_MODS_IDS_LIST": "12345=1.0.0",
        "GAME_MODS_REQUIRED_BY_DEFAULT": "true",
    }
    config = build_config(env, base_config)
    assert config["game"]["mods"][0]["required"] is True


def test_mods_ids_list_invalid_chars(base_config):
    env = {"GAME_MODS_IDS_LIST": "12345=1.0.0;bad"}
    with pytest.raises(AssertionError, match="Illegal characters"):
        build_config(env, base_config)


def test_mods_ids_list_invalid_version(base_config):
    env = {"GAME_MODS_IDS_LIST": "12345=BADVERSION"}
    with pytest.raises(AssertionError, match="version does not match"):
        build_config(env, base_config)


def test_mods_json_file(base_config, tmp_path):
    mods_file = tmp_path / "mods.json"
    mods_file.write_text(
        json.dumps(
            [
                {"modId": "12345", "name": "Test Mod", "version": "1.0.0"},
                {"modId": "67890", "required": False},
            ]
        )
    )
    env = {"GAME_MODS_JSON_FILE_PATH": str(mods_file)}
    config = build_config(env, base_config)
    assert len(config["game"]["mods"]) == 2
    assert config["game"]["mods"][0]["name"] == "Test Mod"
    assert config["game"]["mods"][1]["required"] is False


def test_mods_json_missing_modId(base_config, tmp_path):
    mods_file = tmp_path / "mods.json"
    mods_file.write_text(json.dumps([{"name": "Bad Mod"}]))
    env = {"GAME_MODS_JSON_FILE_PATH": str(mods_file)}
    with pytest.raises(AssertionError, match="does not contain modId"):
        build_config(env, base_config)


def test_mods_deduplication(base_config, tmp_path):
    """Mod IDs from GAME_MODS_IDS_LIST should skip duplicates from JSON."""
    mods_file = tmp_path / "mods.json"
    mods_file.write_text(json.dumps([{"modId": "12345", "name": "From JSON"}]))
    env = {
        "GAME_MODS_IDS_LIST": "12345",
        "GAME_MODS_JSON_FILE_PATH": str(mods_file),
    }
    config = build_config(env, base_config)
    assert len(config["game"]["mods"]) == 1


def test_persistence_config(base_config):
    env = {
        "PERSISTENCE_AUTO_SAVE_INTERVAL": "300",
        "PERSISTENCE_SAVE_RETENTION": "5",
        "PERSISTENCE_LOAD_SESSION_SAVE": "true",
        "PERSISTENCE_KEEP_SESSION_SAVE": "false",
        "PERSISTENCE_HIVE_ID": "123",
    }
    config = build_config(env, base_config)
    p = config["game"]["gameProperties"]["persistence"]
    assert p["autoSaveInterval"] == 300
    assert p["saveRetention"] == 5
    assert p["loadSessionSave"] is True
    assert p["keepSessionSave"] is False
    assert p["hiveId"] == 123


def test_persistence_json_merge(base_config, tmp_path):
    persistence_file = tmp_path / "persistence.json"
    persistence_file.write_text(
        json.dumps(
            {
                "databases": {"foo": "bar"},
                "storages": {"baz": "qux"},
                "ignored": "should not appear",
            }
        )
    )
    env = {"PERSISTENCE_JSON_FILE_PATH": str(persistence_file)}
    config = build_config(env, base_config)
    p = config["game"]["gameProperties"]["persistence"]
    assert p["databases"] == {"foo": "bar"}
    assert p["storages"] == {"baz": "qux"}
    assert "ignored" not in p


def test_persistence_not_set_when_empty(base_config):
    """When no persistence envs are set, key should not be added."""
    env = {}
    config = build_config(env, base_config)
    assert "persistence" not in config["game"]["gameProperties"]


def test_operating_config(base_config):
    env = {
        "OPERATING_LOBBY_PLAYER_SYNCHRONISE": "true",
        "OPERATING_DISABLE_CRASH_REPORTER": "false",
        "OPERATING_DISABLE_SERVER_SHUTDOWN": "true",
        "OPERATING_DISABLE_AI": "false",
        "OPERATING_PLAYER_SAVE_TIME": "120",
        "OPERATING_AI_LIMIT": "50",
        "OPERATING_SLOT_RESERVATION_TIMEOUT": "60",
        "OPERATING_JOIN_QUEUE_MAX_SIZE": "10",
    }
    config = build_config(env, base_config)
    o = config["operating"]
    assert o["lobbyPlayerSynchronise"] is True
    assert o["disableCrashReporter"] is False
    assert o["disableServerShutdown"] is True
    assert o["disableAI"] is False
    assert o["playerSaveTime"] == 120
    assert o["aiLimit"] == 50
    assert o["slotReservationTimeout"] == 60
    assert o["joinQueue"]["maxSize"] == 10


def test_operating_navmesh_all(base_config):
    env = {"OPERATING_DISABLE_NAVMESH_STREAMING": "all"}
    config = build_config(env, base_config)
    assert config["operating"]["disableNavmeshStreaming"] == []


def test_operating_navmesh_list(base_config):
    env = {"OPERATING_DISABLE_NAVMESH_STREAMING": "foo,bar,baz"}
    config = build_config(env, base_config)
    assert config["operating"]["disableNavmeshStreaming"] == ["foo", "bar", "baz"]


def test_operating_not_set_when_empty(base_config):
    """When no operating envs are set, key should not be added."""
    env = {}
    config = build_config(env, base_config)
    assert "operating" not in config


def test_mission_header_json(base_config, tmp_path):
    mission_file = tmp_path / "mission.json"
    mission_file.write_text(json.dumps({"myKey": "myValue"}))
    env = {"GAME_MISSION_HEADER_JSON_FILE_PATH": str(mission_file)}
    config = build_config(env, base_config)
    assert config["game"]["gameProperties"]["missionHeader"] == {"myKey": "myValue"}


def test_game_properties_booleans(base_config):
    env = {
        "GAME_PROPS_BATTLEYE": "false",
        "GAME_PROPS_DISABLE_THIRD_PERSON": "true",
        "GAME_PROPS_FAST_VALIDATION": "false",
        "GAME_PROPS_VON_DISABLE_UI": "true",
        "GAME_PROPS_VON_DISABLE_DIRECT_SPEECH_UI": "true",
        "GAME_PROPS_VON_CAN_TRANSMIT_CROSS_FACTION": "true",
    }
    config = build_config(env, base_config)
    gp = config["game"]["gameProperties"]
    assert gp["battlEye"] is False
    assert gp["disableThirdPerson"] is True
    assert gp["fastValidation"] is False
    assert gp["VONDisableUI"] is True
    assert gp["VONDisableDirectSpeechUI"] is True
    assert gp["VONCanTransmitCrossFaction"] is True


def test_game_properties_integers(base_config):
    env = {
        "GAME_PROPS_SERVER_MAX_VIEW_DISTANCE": "3000",
        "GAME_PROPS_SERVER_MIN_GRASS_DISTANCE": "100",
        "GAME_PROPS_NETWORK_VIEW_DISTANCE": "2000",
    }
    config = build_config(env, base_config)
    gp = config["game"]["gameProperties"]
    assert gp["serverMaxViewDistance"] == 3000
    assert gp["serverMinGrassDistance"] == 100
    assert gp["networkViewDistance"] == 2000
