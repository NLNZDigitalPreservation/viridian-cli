import argparse
import getpass
import grp
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import List, Optional

DEFAULT_DATA_PATH = "/persistent"
SIMULATORS_PROJECT = "viridian-dev"
MASTER_PROJECT = "viridian-fixity"
MASTER_ENV = ".env"

from viridian.config import parse_args_app
from viridian.utils import (
    run,
    select_engine,
    select_compose_command,
    resource_file,
    config_dir,
    _config_file,
    load_config,
    save_config,
    resolve_install_path,
    persist_install_path,
    ensure_directory,
    ensure_simulator_paths,
    ensure_master_paths,
    run_installed_compose,
    version_from_compose,
    registry_image,
    path_state,
    prompt,
    install_packaged_assets,
    generate_fixity_certificate_assets,
    DEFAULT_CONFIG_SUBDIR,
    DEFAULT_CONFIG_FILE,
    DEFAULT_INSTALL_PATH,
    DEFAULT_MASTER_IMAGE,
    DEFAULT_REGISTRY,
    FIXITY_KEY,
    FIXITY_CERT,
    MASTER_COMPOSE,
    SIMULATORS_COMPOSE,
)


def ensure_directory(
    path: Path, owner: Optional[str] = None, mode: Optional[str] = None
) -> None:
    if path.exists():
        return
    run(["sudo", "mkdir", "-p", str(path)])
    if owner is not None:
        run(["sudo", "chown", "-R", owner, str(path)])
    if mode is not None:
        run(["sudo", "chmod", "-R", mode, str(path)])


def ensure_simulator_paths(data_path: Path) -> None:
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    ensure_directory(data_path / "containers", owner=f"{username}:{group_name}")
    ensure_directory(data_path / "azurite", owner=f"{username}:{group_name}")
    ensure_directory(data_path / "oracle", owner="54321:54321", mode="777")


def main() -> int:
    try:
        args = parse_args_app("simulator")

        engine = select_engine(args.container_engine)
        cmd_simulators(args, engine)
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode
