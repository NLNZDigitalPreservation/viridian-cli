import argparse
import getpass
import grp
import json
import os
import shutil
import subprocess
import tempfile
from importlib import resources
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CONFIG_SUBDIR = "viridian"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_INSTALL_PATH = "/usr/local/viridian"
DEFAULT_DATA_PATH = "/data/viridian"


def run(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, text=True, check=check)


def select_engine(engine: str) -> str:
    if engine in ("podman", "docker"):
        return engine
    if shutil.which("podman"):
        return "podman"
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError("Neither podman nor docker is installed.")


def select_compose_command(engine: str) -> List[str]:
    if engine == "podman":
        if shutil.which("podman-compose"):
            return ["podman-compose"]
        return ["podman", "compose"]
    if engine == "docker":
        return ["docker", "compose"]
    raise RuntimeError(f"Unsupported container engine: {engine}")


def resource_file(app_name: str, *parts: str):
    """Return a Traversable for a path inside viridian.resources/<app_name>."""
    resource = resources.files("viridian.resources").joinpath(app_name)
    for part in parts:
        resource = resource.joinpath(part)
    return resource


def config_dir() -> Path:
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home).expanduser() / DEFAULT_CONFIG_SUBDIR
    return Path.home() / ".config" / DEFAULT_CONFIG_SUBDIR


def config_file() -> Path:
    return config_dir() / DEFAULT_CONFIG_FILE


def load_config() -> Dict[str, str]:
    path = config_file()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {k: str(v) for k, v in payload.items()}


def save_config(config: Dict[str, str]) -> None:
    cfg_dir = config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    with config_file().open("w", encoding="utf-8") as fp:
        json.dump(config, fp, indent=2, sort_keys=True)
        fp.write("\n")


def resolve_install_path(cli_value: Optional[str]) -> Path:
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    cfg = load_config()
    persisted = cfg.get("install_path")
    if persisted:
        return Path(persisted).expanduser().resolve()
    return Path(DEFAULT_INSTALL_PATH).resolve()


def persist_path(path_key: str, path: Path) -> None:
    cfg = load_config()
    cfg[path_key] = str(path)
    save_config(cfg)


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


def ensure_master_paths(data_path: Path) -> None:
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    ensure_directory(data_path / "containers", owner=f"{username}:{group_name}")
    ensure_directory(data_path / "fixity", owner=f"{username}:{group_name}")


def run_installed_compose(
    engine: str,
    install_path: Path,
    project_name: str,
    extra: List[str],
) -> None:
    compose_file = install_path / "docker-compose.yml"
    if not compose_file.exists():
        raise FileNotFoundError(
            f"{compose_file} not found. Run 'fixity install' first."
        )
    compose_cmd = select_compose_command(engine)
    cmd = compose_cmd + ["-p", project_name, "-f", str(compose_file)]
    env_file = install_path / ".env"
    if env_file.exists():
        cmd += ["--env-file", str(env_file)]
    cmd += extra
    run(cmd)


def version_from_compose(install_path: Path) -> str:
    """Read the image tag from the installed docker-compose-fixity.yml."""
    compose_file = install_path / "docker-compose.yml"
    if not compose_file.exists():
        return "latest"
    with compose_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            stripped = line.strip()
            if stripped.startswith("image:"):
                # e.g. "image: registry/fixity-master:2.0.0"
                tag_part = stripped.split(":")[-1].strip()
                return tag_part if tag_part else "latest"
    return "latest"


def path_state(path: Path) -> str:
    return "exists" if path.exists() else "missing"


def prompt(message: str, default: str) -> str:
    try:
        answer = input(f"{message} [{default}]: ").strip()
    except EOFError:
        answer = ""
    return answer if answer else default


def install_packaged_assets(install_path: Path, app_name: str) -> None:
    """Copy every file and sub-directory from the app's resources folder to *install_path*."""
    app_resources = resource_file(app_name)

    if not app_resources.is_dir():
        raise FileNotFoundError(
            f"Bundled resource directory missing: resources/{app_name}/. "
            "Rebuild/reinstall viridian-cli."
        )

    with resources.as_file(app_resources) as src_dir:
        for entry in src_dir.iterdir():
            dst = install_path / entry.name
            if entry.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(entry, dst)
            else:
                shutil.copy2(entry, dst)
            print(f"  Installed: {dst}")


def resolve_path(
    app_name: str,
    input_path: str,
    input_path_key: str,
    default_path: str,
    accept_default: bool,
    prompt_desc: str,
) -> Path:
    # Determine install directory.
    resolved_default = (
        Path(input_path, app_name)
        if accept_default and input_path
        else Path(default_path, app_name)
    )
    if accept_default:
        resolved_path = Path(resolved_default).expanduser().resolve()
    else:
        chosen = prompt(prompt_desc, resolved_default)
        resolved_path = Path(chosen).expanduser().resolve()

    print(f"{prompt_desc}: {resolved_path}")

    # Create directory if needed.
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    if not resolved_path.exists():
        print(f"  Creating {resolved_path} ...")
        run(["sudo", "mkdir", "-p", str(resolved_path)])
        run(["sudo", "chown", f"{username}:{group_name}", str(resolved_path)])
        print("  Done.")

    persist_path(input_path_key, resolved_path)
    print(f"  Saved config: {config_file()}")

    return resolved_path


def cmd_install(args: argparse.Namespace, app_name: str) -> None:
    install_path = resolve_path(
        app_name,
        args.install_path,
        "install_path",
        DEFAULT_INSTALL_PATH,
        args.yes,
        "Installation directory",
    )
    args.install_path = str(install_path)

    # Copy bundled compose resources files.
    install_packaged_assets(install_path, app_name)

    data_path = resolve_path(
        app_name,
        args.data_path,
        "data_path",
        DEFAULT_DATA_PATH,
        args.yes,
        "Persistent storage root",
    )
    args.data_path = str(data_path)

    # Always initialise fixity master persistent storage.
    print("\nInitialising persistent storage...")
    ensure_master_paths(data_path)


def cmd_container(args: argparse.Namespace, engine: str) -> None:
    data_path = Path(args.data_path)
    install_path = Path(args.install_path)

    if args.command == "up":
        ensure_master_paths(data_path)
        run_installed_compose(
            engine,
            install_path,
            args.app_name,
            ["up", "--detach"],
        )
        return
    if args.command == "down":
        run_installed_compose(
            engine,
            install_path,
            args.app_name,
            ["down"],
        )
        return
    if args.command == "logs":
        compose_args = ["logs"]
        if not args.no_follow:
            compose_args.append("-f")
        run_installed_compose(
            engine,
            install_path,
            args.app_name,
            compose_args,
        )
        return
    if args.command == "exec":
        run([engine, "exec", "-it", args.app_name, args.shell])
        return
    raise RuntimeError(f"Unsupported {args.app_name} command: {args.command}")
