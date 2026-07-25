import subprocess
import sys
from importlib import metadata, resources

import shutil
import subprocess
import tempfile
from pathlib import Path
from viridian import __version__ as _viridian_version
from viridian.config import parse_args_app
from viridian.utils import run, select_engine, cmd_install, cmd_container

FIXITY_KEY = "fixity.key"
FIXITY_CERT = "fixity.cer"


def _get_version() -> str:
    """Return the package version, falling back to the module constant."""
    try:
        return metadata.version("viridian-cli")
    except metadata.PackageNotFoundError:
        return _viridian_version


def generate_fixity_certificate_assets(install_path: Path) -> None:
    persistent_fixity_path = install_path / "ssl"
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
        run(
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


def main() -> int:
    try:
        args = parse_args_app()

        if args.command == "install":
            cmd_install(args, app_name="fixity")
            print("Initialising fixity certificate assets...")
            generate_fixity_certificate_assets(Path(args.install_path))
            return 0

        # if args.command == "info":
        #     cmd_info(args)
        #     return 0

        engine = select_engine(args.container_engine)
        cmd_container(args, engine)
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode
