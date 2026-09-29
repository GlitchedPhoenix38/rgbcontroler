"""Threaded animation effects for RGB-capable keyboards."""

from __future__ import annotations

import colorsys
import logging
import math
import threading
import time
from typing import Callable

from controller import AsusKeyboardController


LOGGER = logging.getLogger(__name__)
Color = tuple[int, int, int]


class EffectRunner:
    def __init__(self, controller: AsusKeyboardController) -> None:
        self.controller = controller
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self._thread = None
        self._stop_event.clear()

    def start(self, effect_name: str, base_color: Color = (0, 170, 255)) -> bool:
        if not self.controller.capabilities.supports_rgb:
            LOGGER.warning("Cannot start %s: RGB unsupported", effect_name)
            return False

        effects: dict[str, Callable[[Color], None]] = {
            "rainbow": self._rainbow,
            "breathing": self._breathing,
            "color_cycle": self._color_cycle,
            "pulse": self._pulse,
            "wave": self._wave,
        }
        effect = effects.get(effect_name)
        if effect is None:
            LOGGER.error("Unknown effect requested: %s", effect_name)
            return False

        self.stop()
        self._thread = threading.Thread(
            target=self._run_effect,
            args=(effect, base_color),
            daemon=True,
        )
        self._thread.start()
        return True

    def _run_effect(self, effect: Callable[[Color], None], base_color: Color) -> None:
        try:
            effect(base_color)
        except Exception:
            LOGGER.exception("Animation failed")

    def _rainbow(self, _: Color) -> None:
        hue = 0.0
        while not self._stop_event.is_set():
            self.controller.set_rgb(*hsv_to_rgb(hue, 1.0, 1.0))
            hue = (hue + 0.01) % 1.0
            self._stop_event.wait(0.04)

    def _breathing(self, base_color: Color) -> None:
        step = 0.0
        while not self._stop_event.is_set():
            level = (math.sin(step) + 1.0) / 2.0
            self.controller.set_rgb(*scale_color(base_color, level))
            step += 0.12
            self._stop_event.wait(0.05)

    def _color_cycle(self, _: Color) -> None:
        colors: list[Color] = [
            (255, 0, 0),
            (255, 120, 0),
            (255, 255, 0),
            (0, 255, 80),
            (0, 160, 255),
            (90, 0, 255),
        ]
        index = 0
        while not self._stop_event.is_set():
            self.controller.set_rgb(*colors[index % len(colors)])
            index += 1
            self._stop_event.wait(0.5)

    def _pulse(self, base_color: Color) -> None:
        while not self._stop_event.is_set():
            for level in list(range(0, 101, 8)) + list(range(100, -1, -8)):
                if self._stop_event.is_set():
                    break
                self.controller.set_rgb(*scale_color(base_color, level / 100))
                self._stop_event.wait(0.025)
            self._stop_event.wait(0.25)

    def _wave(self, base_color: Color) -> None:
        phase = 0.0
        while not self._stop_event.is_set():
            red = int((math.sin(phase) + 1) * 127.5)
            green = int((math.sin(phase + 2.1) + 1) * 127.5)
            blue = int((math.sin(phase + 4.2) + 1) * 127.5)
            mixed = blend((red, green, blue), base_color, 0.35)
            self.controller.set_rgb(*mixed)
            phase += 0.18
            self._stop_event.wait(0.04)


def hsv_to_rgb(hue: float, saturation: float, value: float) -> Color:
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return int(red * 255), int(green * 255), int(blue * 255)


def scale_color(color: Color, factor: float) -> Color:
    factor = max(0.0, min(1.0, factor))
    return tuple(int(channel * factor) for channel in color)


def blend(first: Color, second: Color, second_weight: float) -> Color:
    first_weight = 1.0 - second_weight
    return tuple(
        int(first[index] * first_weight + second[index] * second_weight)
        for index in range(3)
    )
