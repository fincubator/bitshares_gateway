from src.config import Config, project_root_dir
import os
from shutil import copyfile


def test_config():
    c = Config()
    assert c.http_port == 9999


def test_config_with_env():
    if os.path.isfile(str(project_root_dir) + "/.env"):
        c = Config()
        c.with_environment()
    else:
        copyfile(
            str(project_root_dir) + "/.env.example", str(project_root_dir) + "/.env"
        )
        c = Config()
        c.with_environment()
        os.remove(str(project_root_dir) + "/.env")

    assert c.is_test_env != Config.is_test_env
