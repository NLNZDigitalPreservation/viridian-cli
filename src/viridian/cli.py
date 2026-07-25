import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

from viridian.config import parse_args_app

DEFAULT_DATA_PATH = "/persistent"
SIMULATORS_PROJECT = "viridian-dev"
MASTER_PROJECT = "viridian-fixity"
MASTER_ENV = ".env"

from viridian.utils import select_engine, cmd_install

# ── entry points ──────────────────────────────────────────────────────────────


def main() -> int:
    try:
        args = parse_args_app()

        if args.command == "install":
            cmd_install(args)
            return 0
        # if args.command == "info":
        #     cmd_info(args)
        #     return 0

        # engine = select_engine(args.container_engine)
        # cmd_master(args, engine)
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
