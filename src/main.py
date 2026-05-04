from pathlib import Path

from dotenv import load_dotenv
from pyaz.cli import main

# load_dotenv(dotenv_path=".env")
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


if __name__ == "__main__":
    main()
