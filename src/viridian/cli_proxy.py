import subprocess
import sys

import subprocess
from viridian.config import parse_args_app
from viridian.utils import run, select_engine, cmd_install, cmd_container, cmd_info


def main() -> int:
    try:
        args = parse_args_app()

        if args.command == "install":
            cmd_install(app_name="proxy")
            return 0

        if args.command == "info":
            cmd_info(app_name="proxy")
            return 0

        engine = select_engine(args.container_engine)
        cmd_container(args, app_name="proxy", engine=engine)
        return 0
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        return exc.returncode
