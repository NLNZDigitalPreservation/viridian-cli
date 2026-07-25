from pathlib import Path

from dotenv import load_dotenv
from viridian.config import parse_args_app

# load_dotenv(dotenv_path=".env")
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


def main():
    args = parse_args_app()
    print(f"App Name: {args.app_name}")
    print(f"Install Path: {args.install_path}")
    print(f"Data Path: {args.data_path}")
    print(f"Container Engine: {args.container_engine}")
    print(f"Command: {args.command}")


if __name__ == "__main__":
    main()
