#!/usr/bin/env python3
"""Entry point for the ASUS TUF keyboard lighting controller."""

from controller import AsusKeyboardController
from ui import AsusLightingApp
from utils import setup_logging


def main() -> None:
    setup_logging()
    controller = AsusKeyboardController()
    app = AsusLightingApp(controller)
    app.run()


if __name__ == "__main__":
    main()
