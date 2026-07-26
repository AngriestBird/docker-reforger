import pytest

from launch_config import load_json_file


@pytest.fixture
def base_config():
    return load_json_file("docker_default.json")
