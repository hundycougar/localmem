"""Configuration management for localmem."""

import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LOCALMEM_CONFIG_DIR", Path.home() / ".config" / "localmem"))
CONFIG_FILE = CONFIG_DIR / "config"


def get_api_key() -> str:
    """Get the mem.ai API key from env var or config file."""
    key = os.environ.get("MEM_API_KEY")
    if key:
        return key

    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("api_key="):
                return line.split("=", 1)[1].strip()

    raise SystemExit(
        "No API key found. Set MEM_API_KEY env var or run: localmem config set-key YOUR_KEY"
    )


def set_api_key(key: str) -> None:
    """Save the API key to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(f"api_key={key}\n")
