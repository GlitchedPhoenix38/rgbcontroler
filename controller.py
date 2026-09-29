"""Hardware detection and control for ASUS laptop keyboard LEDs."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
import subprocess

from utils import clamp, read_text, write_text


LOGGER = logging.getLogger(__name__)


@dataclass
class LedDevice:
    name: str
    path: Path
    brightness_path: Path | None = None
    max_brightness: int = 3
    color_paths: dict[str, Path] = field(default_factory=dict)
    multi_intensity_path: Path | None = None
    trigger_path: Path | None = None

    @property
    def supports_brightness(self) -> bool:
        return self.brightness_path is not None

    @property
    def supports_rgb(self) -> bool:
        channels = {"red", "green", "blue"}
        return channels.issubset(self.color_paths) or self.multi_intensity_path is not None

    @property
    def supports_modes(self) -> bool:
        return self.trigger_path is not None


@dataclass
class Capabilities:
    device_name: str = "No keyboard LED device detected"
    supports_brightness: bool = False
    supports_rgb: bool = False
    supports_modes: bool = False
    max_brightness: int = 3
    available_modes: list[str] = field(default_factory=list)
    module_loaded: bool = False
    limited_message: str = ""


class AsusKeyboardController:
    """Controls keyboard LEDs through Linux sysfs LED interfaces."""

    SYSFS_LEDS = Path("/sys/class/leds")
    CANDIDATE_TERMS = ("kbd", "keyboard", "asus", "tuf", "aura")

    def __init__(self) -> None:
        self.device = self._detect_device()
        self.capabilities = self._build_capabilities()

    def refresh(self) -> Capabilities:
        self.device = self._detect_device()
        self.capabilities = self._build_capabilities()
        return self.capabilities

    def _detect_device(self) -> LedDevice | None:
        if not self.SYSFS_LEDS.exists():
            LOGGER.warning("%s does not exist", self.SYSFS_LEDS)
            return None

        devices = sorted(path for path in self.SYSFS_LEDS.iterdir() if path.is_dir())
        candidates = [
            path
            for path in devices
            if any(term in path.name.lower() for term in self.CANDIDATE_TERMS)
        ]
        search_order = candidates or devices

        for path in search_order:
            device = self._inspect_led_device(path)
            if device.supports_rgb or device.supports_brightness:
                LOGGER.info("Using LED device %s", device.name)
                return device

        LOGGER.warning("No usable LED device found")
        return None

    def _inspect_led_device(self, path: Path) -> LedDevice:
        brightness_path = path / "brightness"
        max_value = read_text(path / "max_brightness")
        color_paths = {
            name: path / name
            for name in ("red", "green", "blue")
            if (path / name).exists()
        }

        device = LedDevice(
            name=path.name,
            path=path,
            brightness_path=brightness_path if brightness_path.exists() else None,
            max_brightness=int(max_value) if max_value and max_value.isdigit() else 3,
            color_paths=color_paths,
            multi_intensity_path=(path / "multi_intensity")
            if (path / "multi_intensity").exists()
            else None,
            trigger_path=(path / "trigger") if (path / "trigger").exists() else None,
        )
        return device

    def _build_capabilities(self) -> Capabilities:
        module_loaded = self._module_loaded("asus_nb_wmi") or self._module_loaded("asus_wmi")
        if self.device is None:
            return Capabilities(module_loaded=module_loaded)

        modes = self._read_triggers(self.device.trigger_path)
        limited = ""
        if not self.device.supports_rgb:
            limited = "Only brightness or limited modes supported on this device"

        return Capabilities(
            device_name=self.device.name,
            supports_brightness=self.device.supports_brightness,
            supports_rgb=self.device.supports_rgb,
            supports_modes=self.device.supports_modes,
            max_brightness=self.device.max_brightness,
            available_modes=modes,
            module_loaded=module_loaded,
            limited_message=limited,
        )

    def _module_loaded(self, module_name: str) -> bool:
        try:
            result = subprocess.run(
                ["lsmod"],
                check=False,
                capture_output=True,
                text=True,
            )
            return module_name in result.stdout.replace("-", "_")
        except OSError as exc:
            LOGGER.debug("Could not check kernel modules: %s", exc)
            return False

    def _read_triggers(self, trigger_path: Path | None) -> list[str]:
        if trigger_path is None:
            return []
        text = read_text(trigger_path)
        if not text:
            return []
        return [item.strip("[]") for item in text.split()]

    def set_brightness(self, value: int) -> bool:
        if self.device is None or self.device.brightness_path is None:
            LOGGER.warning("Brightness requested but no brightness path is available")
            return False
        value = clamp(int(value), 0, self.device.max_brightness)
        return write_text(self.device.brightness_path, value)

    def set_rgb(self, red: int, green: int, blue: int) -> bool:
        if self.device is None or not self.device.supports_rgb:
            LOGGER.warning("RGB requested but RGB control is unavailable")
            return False

        red = clamp(int(red), 0, 255)
        green = clamp(int(green), 0, 255)
        blue = clamp(int(blue), 0, 255)

        if self.device.multi_intensity_path is not None:
            return write_text(self.device.multi_intensity_path, f"{red} {green} {blue}")

        results = [
            write_text(self.device.color_paths["red"], red),
            write_text(self.device.color_paths["green"], green),
            write_text(self.device.color_paths["blue"], blue),
        ]
        return all(results)

    def set_mode(self, mode: str) -> bool:
        if self.device is None or self.device.trigger_path is None:
            LOGGER.warning("Mode requested but trigger path is unavailable")
            return False
        if self.capabilities.available_modes and mode not in self.capabilities.available_modes:
            LOGGER.warning("Unsupported mode requested: %s", mode)
            return False
        return write_text(self.device.trigger_path, mode)
