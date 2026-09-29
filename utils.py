"""Shared helpers for logging and safe sysfs access."""

from __future__ import annotations

import logging
from pathlib import Path


LOG_FILE = Path("rgb_controller.log")


def setup_logging() -> None:
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logging.debug("Could not read %s: %s", path, exc)
        return None


def write_text(path: Path, value: str | int) -> bool:
    try:
        path.write_text(f"{value}\n", encoding="utf-8")
        return True
    except PermissionError as exc:
        logging.error("Permission denied writing %s: %s", path, exc)
        return False
    except OSError as exc:
        logging.error("Could not write %s: %s", path, exc)
        return False


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("RGB color must be a 6-digit hex string")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
