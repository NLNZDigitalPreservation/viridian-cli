#!/usr/bin/env python3
import argparse
import getpass
import grp
import json
import os
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata, resources
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_DATA_PATH = "/persistent"
DEFAULT_INSTALL_PATH = "/usr/local/fixity"
DEFAULT_CONFIG_SUBDIR = "fixity"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_REGISTRY = "acrdiaanlnznsbx.azurecr.io"
DEFAULT_MASTER_IMAGE = "fixity-master"
SIMULATORS_PROJECT = "viridian-dev"
MASTER_PROJECT = "viridian-fixity"
SIMULATORS_COMPOSE = "docker-compose-dev.yml"
MASTER_COMPOSE = "docker-compose-fixity.yml"
MASTER_ENV = ".env"
FIXITY_KEY = "fixity.key"
FIXITY_CERT = "fixity.cer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fixity", description="Viridian fixity master helper"
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {metadata.version('fixity-cli')}",
    )
    parser.add_argument(
        "--container-engine",
        choices=["auto", "podman", "docker"],
        default="auto",
        help="Container engine to use",
    )
    parser.add_argument(
        "--data-path",
        default=DEFAULT_DATA_PATH,
        help="Persistent storage root for master data",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Viridian repository root for build-related commands",
    )
    parser.add_argument(
        "--install-path",
        default=None,
        help="Fixity installation directory (defaults to persisted config or /usr/local/fixity)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── install / info ────────────────────────────────────────────────────────
    install_parser = subparsers.add_parser(
        "install", help="Install compose files, db scripts, and .env templates"
    )
    install_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Accept the default installation directory without prompting",
    )
    subparsers.add_parser(
        "info", help="Show resolved installation path and persistent directory status"
    )

    # ── master service commands ───────────────────────────────────────────────
    for name in ("up", "down", "build", "push"):
        subparsers.add_parser(name, help=f"{name} fixity master service")

    logs_cmd = subparsers.add_parser("logs", help="Follow fixity master logs")
    logs_cmd.add_argument(
        "--no-follow", action="store_true", help="Do not follow log output"
    )

    exec_cmd = subparsers.add_parser(
        "exec", help="Open a shell in the running fixity_master container"
    )
    exec_cmd.add_argument(
        "--shell",
        default="bash",
        help="Shell executable to run inside fixity_master",
    )

    return parser.parse_args()


def parse_args_simulator() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="simulator", description="Viridian simulator helper"
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {metadata.version('fixity-cli')}",
    )
    parser.add_argument(
        "--container-engine",
        choices=["auto", "podman", "docker"],
        default="auto",
        help="Container engine to use",
    )
    parser.add_argument(
        "--data-path",
        default=DEFAULT_DATA_PATH,
        help="Persistent storage root for simulator data",
    )
    parser.add_argument(
        "--install-path",
        default=None,
        help="Fixity installation directory (defaults to persisted config or /usr/local/fixity)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("up", "down"):
        subparsers.add_parser(name, help=f"{name} simulator services")

    logs_cmd = subparsers.add_parser("logs", help="Follow simulator logs")
    logs_cmd.add_argument(
        "--no-follow", action="store_true", help="Do not follow log output"
    )

    return parser.parse_args()


def _run(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, text=True, check=check)


def _select_engine(engine: str) -> str:
    if engine in ("podman", "docker"):
        return engine
    if shutil.which("podman"):
        return "podman"
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError("Neither podman nor docker is installed.")


def _select_compose_command(engine: str) -> List[str]:
    if engine == "podman":
        if shutil.which("podman-compose"):
            return ["podman-compose"]
        return ["podman", "compose"]
    if engine == "docker":
        return ["docker", "compose"]
    raise RuntimeError(f"Unsupported container engine: {engine}")


def _resource_file(*parts: str):
    resource = resources.files("fixity.resources")
    for part in parts:
        resource = resource.joinpath(part)
    return resource


def _config_dir() -> Path:
    xdg_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_home:
        return Path(xdg_home).expanduser() / DEFAULT_CONFIG_SUBDIR
    return Path.home() / ".config" / DEFAULT_CONFIG_SUBDIR


def _config_file() -> Path:
    return _config_dir() / DEFAULT_CONFIG_FILE


def _load_config() -> Dict[str, str]:
    path = _config_file()
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


def _save_config(config: Dict[str, str]) -> None:
    cfg_dir = _config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    with _config_file().open("w", encoding="utf-8") as fp:
        json.dump(config, fp, indent=2, sort_keys=True)
        fp.write("\n")


def _resolve_install_path(cli_value: Optional[str]) -> Path:
    if cli_value:
        return Path(cli_value).expanduser().resolve()
    cfg = _load_config()
    persisted = cfg.get("install_path")
    if persisted:
        return Path(persisted).expanduser().resolve()
    return Path(DEFAULT_INSTALL_PATH).resolve()


def _persist_install_path(path: Path) -> None:
    cfg = _load_config()
    cfg["install_path"] = str(path)
    _save_config(cfg)


def _ensure_directory(
    path: Path, owner: Optional[str] = None, mode: Optional[str] = None
) -> None:
    if path.exists():
        return
    _run(["sudo", "mkdir", "-p", str(path)])
    if owner is not None:
        _run(["sudo", "chown", "-R", owner, str(path)])
    if mode is not None:
        _run(["sudo", "chmod", "-R", mode, str(path)])


def _ensure_simulator_paths(data_path: Path) -> None:
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    _ensure_directory(data_path / "containers", owner=f"{username}:{group_name}")
    _ensure_directory(data_path / "azurite", owner=f"{username}:{group_name}")
    _ensure_directory(data_path / "oracle", owner="54321:54321", mode="777")


def _ensure_master_paths(data_path: Path) -> None:
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    _ensure_directory(data_path / "containers", owner=f"{username}:{group_name}")
    _ensure_directory(data_path / "fixity", owner=f"{username}:{group_name}")


def _run_installed_compose(
    engine: str,
    install_path: Path,
    compose_name: str,
    env_name: Optional[str],
    project_name: str,
    extra: List[str],
) -> None:
    compose_file = install_path / compose_name
    if not compose_file.exists():
        raise FileNotFoundError(
            f"{compose_file} not found. Run 'fixity install' first."
        )
    compose_cmd = _select_compose_command(engine)
    cmd = compose_cmd + ["-p", project_name, "-f", str(compose_file)]
    if env_name is not None:
        env_file = install_path / env_name
        if env_file.exists():
            cmd += ["--env-file", str(env_file)]
    cmd += extra
    _run(cmd)


def _version_from_compose(install_path: Path) -> str:
    """Read the image tag from the installed docker-compose-fixity.yml."""
    compose_file = install_path / MASTER_COMPOSE
    if not compose_file.exists():
        return "latest"
    with compose_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            stripped = line.strip()
            if stripped.startswith("image:") and DEFAULT_MASTER_IMAGE in stripped:
                # e.g. "image: registry/fixity-master:2.0.0"
                tag_part = stripped.split(":")[-1].strip()
                return tag_part if tag_part else "latest"
    return "latest"


def _registry_image(version: str) -> str:
    return f"{DEFAULT_REGISTRY}/{DEFAULT_MASTER_IMAGE}:{version}"


def _path_state(path: Path) -> str:
    return "exists" if path.exists() else "missing"


def cmd_info(args: argparse.Namespace) -> None:
    config_file = _config_file()
    config = _load_config()
    install_path = _resolve_install_path(args.install_path)
    data_path = Path(args.data_path).expanduser().resolve()

    print("Fixity Info")
    print(f"Config file: {config_file}")
    print(f"Config state: {_path_state(config_file)}")
    print(
        "Install path source: "
        + ("--install-path" if args.install_path else "persisted/default")
    )
    print(f"Install path: {install_path} ({_path_state(install_path)})")

    install_targets = [
        SIMULATORS_COMPOSE,
        MASTER_COMPOSE,
        MASTER_ENV,
        "db",
    ]
    print("Install directory contents:")
    for item in install_targets:
        target = install_path / item
        print(f"  - {target}: {_path_state(target)}")

    print(f"Persistent root: {data_path} ({_path_state(data_path)})")
    print("Persistent directories:")
    for dirname in ("containers", "azurite", "oracle", "fixity"):
        target = data_path / dirname
        print(f"  - {target}: {_path_state(target)}")


# ── install ───────────────────────────────────────────────────────────────────


def _prompt(message: str, default: str) -> str:
    try:
        answer = input(f"{message} [{default}]: ").strip()
    except EOFError:
        answer = ""
    return answer if answer else default


def _install_packaged_assets(install_path: Path) -> None:
    """Install bundled compose and db assets from fixity.resources."""
    for fname in (SIMULATORS_COMPOSE, MASTER_COMPOSE):
        traversable = _resource_file(fname)
        if not traversable.is_file():
            raise FileNotFoundError(
                f"Bundled resource missing: {fname}. "
                "Rebuild/reinstall fixity-cli with setup.py resource injection."
            )
        with resources.as_file(traversable) as src:
            shutil.copy2(src, install_path / fname)
        print(f"  Installed: {install_path / fname}")

    db_traversable = _resource_file("db")
    if not db_traversable.is_dir():
        raise FileNotFoundError(
            "Bundled resource missing: db/. "
            "Rebuild/reinstall fixity-cli with setup.py resource injection."
        )
    with resources.as_file(db_traversable) as db_src:
        db_dst = install_path / "db"
        if db_dst.exists():
            shutil.rmtree(db_dst)
        shutil.copytree(db_src, db_dst)
    print(f"  Installed: {db_dst}/")


def _generate_fixity_certificate_assets(data_path: Path) -> None:
    persistent_fixity_path = data_path / DEFAULT_CONFIG_SUBDIR
    persistent_fixity_path.mkdir(parents=True, exist_ok=True)

    key_path = persistent_fixity_path / FIXITY_KEY
    cert_path = persistent_fixity_path / FIXITY_CERT

    if key_path.exists() and cert_path.exists():
        print(f"  Skipped (already exists): {key_path}")
        print(f"  Skipped (already exists): {cert_path}")
        return

    if shutil.which("openssl") is None:
        raise RuntimeError("openssl is required to generate fixity.key and fixity.cer.")

    with tempfile.TemporaryDirectory(dir=str(persistent_fixity_path)) as temp_dir:
        temp_key = Path(temp_dir) / FIXITY_KEY
        temp_cert = Path(temp_dir) / FIXITY_CERT
        _run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-sha256",
                "-days",
                "3650",
                "-nodes",
                "-subj",
                "/CN=fixity",
                "-keyout",
                str(temp_key),
                "-out",
                str(temp_cert),
            ]
        )
        shutil.move(str(temp_key), key_path)
        shutil.move(str(temp_cert), cert_path)

    key_path.chmod(0o600)
    cert_path.chmod(0o644)
    print(f"  Created:  {key_path}")
    print(f"  Created:  {cert_path}")


def cmd_install(args: argparse.Namespace) -> None:
    username = getpass.getuser()
    group_name = grp.getgrgid(os.getgid()).gr_name
    data_path = Path(args.data_path)

    # Determine install directory.
    resolved_default = str(_resolve_install_path(args.install_path))
    if args.yes:
        install_path = Path(resolved_default).expanduser().resolve()
    else:
        chosen = _prompt("Installation directory", resolved_default)
        install_path = Path(chosen).expanduser().resolve()

    print(f"Installing to: {install_path}")

    # Create directory if needed.
    if not install_path.exists():
        print(f"  Creating {install_path} ...")
        _run(["sudo", "mkdir", "-p", str(install_path)])
        _run(["sudo", "chown", f"{username}:{group_name}", str(install_path)])
        print("  Done.")

    # Copy bundled compose files + db/ from package resources.
    _install_packaged_assets(install_path)

    # Create .env from template if it doesn't exist yet.
    env_path = install_path / MASTER_ENV
    if env_path.exists():
        print(f"  Skipped (already exists): {env_path}")
    else:
        with resources.as_file(_resource_file("master.env.template")) as tmpl:
            shutil.copy2(tmpl, env_path)
        print(f"  Created:  {env_path}")

    _persist_install_path(install_path)
    print(f"  Saved config: {_config_file()}")

    # Always initialise fixity master persistent storage.
    print("\nInitialising persistent storage...")
    _ensure_master_paths(data_path)
    print("Initialising fixity certificate assets...")
    _generate_fixity_certificate_assets(data_path)

    # Optionally initialise simulator storage.
    if args.yes:
        enable_simulator = False
    else:
        try:
            answer = input("Enable simulator? [y/N]: ").strip().lower()
        except EOFError:
            answer = ""
        enable_simulator = answer in ("y", "yes")

    if enable_simulator:
        print("Initialising simulator persistent storage...")
        _ensure_simulator_paths(data_path)

    print(
        f"\nInstallation complete.\n"
        f"Edit {install_path / MASTER_ENV} as needed, then run:\n"
        + ("  simulator up\n" if enable_simulator else "")
        + "  fixity up"
    )


# ── simulators ────────────────────────────────────────────────────────────────


def cmd_simulators(args: argparse.Namespace, engine: str) -> None:
    data_path = Path(args.data_path)
    install_path = _resolve_install_path(args.install_path)

    if args.command == "up":
        _ensure_simulator_paths(data_path)
        _run_installed_compose(
            engine,
            install_path,
            SIMULATORS_COMPOSE,
            None,
            SIMULATORS_PROJECT,
            ["up", "--detach"],
        )
        return
    if args.command == "down":
        _run_installed_compose(
            engine,
            install_path,
            SIMULATORS_COMPOSE,
            None,
            SIMULATORS_PROJECT,
            ["down"],
        )
        return
    if args.command == "logs":
        compose_args = ["logs"]
        if not args.no_follow:
            compose_args.append("-f")
        _run_installed_compose(
            engine,
            install_path,
            SIMULATORS_COMPOSE,
            None,
            SIMULATORS_PROJECT,
            compose_args,
        )
        return
    raise RuntimeError(f"Unsupported simulators command: {args.command}")


# ── master ────────────────────────────────────────────────────────────────────


def cmd_master(args: argparse.Namespace, engine: str) -> None:
    data_path = Path(args.data_path)
    install_path = _resolve_install_path(args.install_path)

    if args.command == "build":
        project_root = Path(args.project_root).resolve()
        dockerfile = project_root / "deployment" / "master" / "Dockerfile"
        if not dockerfile.exists():
            raise FileNotFoundError(f"Missing Dockerfile: {dockerfile}")
        version = _version_from_compose(install_path)
        _run(
            [
                engine,
                "build",
                "-f",
                str(dockerfile),
                "--tag",
                f"{DEFAULT_MASTER_IMAGE}:{version}",
                str(project_root),
            ]
        )
        _run(
            [
                engine,
                "tag",
                f"{DEFAULT_MASTER_IMAGE}:{version}",
                _registry_image(version),
            ]
        )
        return
    if args.command == "push":
        version = _version_from_compose(install_path)
        _run([engine, "push", _registry_image(version)])
        return
    if args.command == "up":
        _ensure_master_paths(data_path)
        _run_installed_compose(
            engine,
            install_path,
            MASTER_COMPOSE,
            MASTER_ENV,
            MASTER_PROJECT,
            ["up", "--detach"],
        )
        return
    if args.command == "down":
        _run_installed_compose(
            engine,
            install_path,
            MASTER_COMPOSE,
            MASTER_ENV,
            MASTER_PROJECT,
            ["down"],
        )
        return
    if args.command == "logs":
        compose_args = ["logs"]
        if not args.no_follow:
            compose_args.append("-f")
        _run_installed_compose(
            engine,
            install_path,
            MASTER_COMPOSE,
            MASTER_ENV,
            MASTER_PROJECT,
            compose_args,
        )
        return
    if args.command == "exec":
        _run([engine, "exec", "-it", "fixity_master", args.shell])
        return
    raise RuntimeError(f"Unsupported master command: {args.command}")


# ── entry points ──────────────────────────────────────────────────────────────


def main() -> int:
    try:
        args = parse_args()

        if args.command == "install":
            cmd_install(args)
            return 0
        if args.command == "info":
            cmd_info(args)
            return 0

        engine = _select_engine(args.container_engine)
        cmd_master(args, engine)
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode


def main_simulator() -> int:
    try:
        args = parse_args_simulator()
        engine = _select_engine(args.container_engine)
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


def _entrypoint(entry: callable) -> None:
    try:
        raise SystemExit(entry())
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode)


if __name__ == "__main__":
    _entrypoint(main)
