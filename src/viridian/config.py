import argparse
from importlib import metadata

from viridian import __version__ as _viridian_version

DEFAULT_INSTALL_PATH = "/usr/local/viridian"
DEFAULT_DATA_PATH = "/data/viridian"


def _get_version() -> str:
    """Return the package version, falling back to the module constant."""
    try:
        return metadata.version("viridian-cli")
    except metadata.PackageNotFoundError:
        return _viridian_version


def parse_args_app(app_name: str = "") -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=app_name, description=f"Viridian {app_name} helper"
    )
    parser.add_argument("--app-name", default=app_name, help="Name of the application")

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )
    parser.add_argument(
        "--container-engine",
        choices=["auto", "podman", "docker"],
        default="auto",
        help="Container engine to use",
    )
    parser.add_argument(
        "--data-path",
        default=f"{DEFAULT_DATA_PATH}/{app_name}",
        help=f"Persistent storage root for {app_name} data",
    )
    parser.add_argument(
        "--install-path",
        default=f"{DEFAULT_INSTALL_PATH}/{app_name}",
        help=f"Installation directory (defaults to persisted config or {DEFAULT_INSTALL_PATH})",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("up", "down", "build", "push"):
        subparsers.add_parser(name, help=f"{name} {app_name} services")

    logs_cmd = subparsers.add_parser("logs", help=f"Follow {app_name} logs")
    logs_cmd.add_argument(
        "--no-follow", action="store_true", help="Do not follow log output"
    )

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

    return parser.parse_args()
