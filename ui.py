"""Tkinter GUI for the ASUS keyboard lighting controller."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from controller import AsusKeyboardController
from effects import EffectRunner
from utils import hex_to_rgb, rgb_to_hex


LOGGER = logging.getLogger(__name__)


class AsusLightingApp:
    def __init__(self, controller: AsusKeyboardController) -> None:
        self.controller = controller
        self.effects = EffectRunner(controller)
        self.root = tk.Tk()
        self.root.title("ASUS TUF Keyboard Lighting")
        self.root.geometry("520x430")
        self.root.minsize(460, 390)
        self.root.configure(bg="#171a21")

        self.selected_color = (0, 170, 255)
        self.status_var = tk.StringVar(value="")
        self.color_var = tk.StringVar(value=rgb_to_hex(self.selected_color))
        self.brightness_var = tk.IntVar(value=0)
        self.mode_var = tk.StringVar(value="")

        self._configure_style()
        self._build()
        self._apply_capabilities()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        self.root.mainloop()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background="#171a21", foreground="#e8edf2", fieldbackground="#222733")
        style.configure("TFrame", background="#171a21")
        style.configure("Panel.TFrame", background="#20242e")
        style.configure("TLabel", background="#171a21", foreground="#e8edf2")
        style.configure("Panel.TLabel", background="#20242e", foreground="#e8edf2")
        style.configure("Muted.TLabel", background="#171a21", foreground="#a8b0bd")
        style.configure("TButton", background="#2d3442", foreground="#e8edf2", padding=8)
        style.map("TButton", background=[("active", "#3b4658"), ("disabled", "#252a34")])
        style.configure("Horizontal.TScale", background="#171a21", troughcolor="#303746")

    def _build(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill="both", expand=True)

        title = ttk.Label(container, text="ASUS TUF Keyboard Lighting", font=("TkDefaultFont", 16, "bold"))
        title.pack(anchor="w")

        self.device_label = ttk.Label(container, text="", style="Muted.TLabel")
        self.device_label.pack(anchor="w", pady=(4, 16))

        color_panel = ttk.Frame(container, style="Panel.TFrame", padding=14)
        color_panel.pack(fill="x", pady=(0, 12))

        color_row = ttk.Frame(color_panel, style="Panel.TFrame")
        color_row.pack(fill="x")
        ttk.Label(color_row, text="Static color", style="Panel.TLabel").pack(side="left")
        self.color_preview = tk.Label(
            color_row,
            width=5,
            height=2,
            bg=self.color_var.get(),
            relief="flat",
        )
        self.color_preview.pack(side="right", padx=(8, 0))
        self.color_button = ttk.Button(color_row, text="Choose color", command=self._choose_color)
        self.color_button.pack(side="right")

        self.static_button = ttk.Button(color_panel, text="Apply static color", command=self._apply_static)
        self.static_button.pack(fill="x", pady=(12, 0))

        brightness_panel = ttk.Frame(container, style="Panel.TFrame", padding=14)
        brightness_panel.pack(fill="x", pady=(0, 12))
        ttk.Label(brightness_panel, text="Brightness", style="Panel.TLabel").pack(anchor="w")
        self.brightness_scale = ttk.Scale(
            brightness_panel,
            from_=0,
            to=self.controller.capabilities.max_brightness,
            command=self._brightness_changed,
        )
        self.brightness_scale.pack(fill="x", pady=(10, 0))

        effects_panel = ttk.Frame(container, style="Panel.TFrame", padding=14)
        effects_panel.pack(fill="x", pady=(0, 12))
        ttk.Label(effects_panel, text="Effects", style="Panel.TLabel").pack(anchor="w")

        grid = ttk.Frame(effects_panel, style="Panel.TFrame")
        grid.pack(fill="x", pady=(10, 0))
        self.effect_buttons: list[ttk.Button] = []
        effects = [
            ("Rainbow", "rainbow"),
            ("Breathing", "breathing"),
            ("Color cycle", "color_cycle"),
            ("Pulse", "pulse"),
            ("Wave", "wave"),
        ]
        for index, (label, name) in enumerate(effects):
            button = ttk.Button(grid, text=label, command=lambda effect=name: self._start_effect(effect))
            button.grid(row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4)
            self.effect_buttons.append(button)
        for column in range(3):
            grid.columnconfigure(column, weight=1)

        self.stop_button = ttk.Button(effects_panel, text="Stop animation", command=self._stop_effects)
        self.stop_button.pack(fill="x", pady=(8, 0))

        mode_panel = ttk.Frame(container, style="Panel.TFrame", padding=14)
        mode_panel.pack(fill="x", pady=(0, 12))
        ttk.Label(mode_panel, text="Device modes", style="Panel.TLabel").pack(anchor="w")
        mode_row = ttk.Frame(mode_panel, style="Panel.TFrame")
        mode_row.pack(fill="x", pady=(10, 0))
        self.mode_combo = ttk.Combobox(mode_row, textvariable=self.mode_var, state="disabled")
        self.mode_combo.pack(side="left", fill="x", expand=True)
        self.mode_button = ttk.Button(mode_row, text="Apply mode", command=self._apply_mode, state="disabled")
        self.mode_button.pack(side="right", padx=(8, 0))

        bottom = ttk.Frame(container)
        bottom.pack(fill="x", side="bottom")
        self.refresh_button = ttk.Button(bottom, text="Refresh device", command=self._refresh)
        self.refresh_button.pack(side="right")
        self.status_label = ttk.Label(bottom, textvariable=self.status_var, style="Muted.TLabel", wraplength=330)
        self.status_label.pack(side="left", fill="x", expand=True)

    def _apply_capabilities(self) -> None:
        caps = self.controller.capabilities
        module_text = "asus-wmi loaded" if caps.module_loaded else "asus-wmi not detected"
        self.device_label.configure(text=f"Device: {caps.device_name} | {module_text}")

        self.brightness_scale.configure(to=max(1, caps.max_brightness))
        if caps.supports_brightness:
            self.brightness_scale.state(["!disabled"])
        else:
            self.brightness_scale.state(["disabled"])

        rgb_state = "normal" if caps.supports_rgb else "disabled"
        self.color_button.configure(state=rgb_state)
        self.static_button.configure(state=rgb_state)
        for button in self.effect_buttons:
            button.configure(state=rgb_state)
        self.stop_button.configure(state=rgb_state)

        if caps.supports_modes and caps.available_modes:
            self.mode_combo.configure(values=caps.available_modes, state="readonly")
            if self.mode_var.get() not in caps.available_modes:
                self.mode_var.set(caps.available_modes[0])
            self.mode_button.configure(state="normal")
        else:
            self.mode_combo.configure(values=[], state="disabled")
            self.mode_var.set("")
            self.mode_button.configure(state="disabled")

        if caps.limited_message:
            self.status_var.set(caps.limited_message)
            messagebox.showinfo("Limited support", caps.limited_message)
        elif caps.supports_rgb:
            self.status_var.set("RGB control available")
        elif caps.supports_brightness:
            self.status_var.set("Brightness control available")
        else:
            self.status_var.set("No compatible keyboard LED sysfs device found")

    def _choose_color(self) -> None:
        color = colorchooser.askcolor(color=self.color_var.get(), title="Choose keyboard color")
        if color[1] is None:
            return
        try:
            self.selected_color = hex_to_rgb(color[1])
            self.color_var.set(color[1])
            self.color_preview.configure(bg=color[1])
        except ValueError as exc:
            LOGGER.error("Invalid color selected: %s", exc)
            messagebox.showerror("Invalid color", str(exc))

    def _apply_static(self) -> None:
        self.effects.stop()
        if self.controller.set_rgb(*self.selected_color):
            self.status_var.set(f"Static color applied: {self.color_var.get()}")
        else:
            self.status_var.set("Could not apply color. Try running with sudo.")

    def _start_effect(self, name: str) -> None:
        if self.effects.start(name, self.selected_color):
            self.status_var.set(f"{name.replace('_', ' ').title()} running")
        else:
            self.status_var.set("This device does not expose RGB control")

    def _stop_effects(self) -> None:
        self.effects.stop()
        self.status_var.set("Animation stopped")

    def _apply_mode(self) -> None:
        mode = self.mode_var.get()
        if not mode:
            return
        self.effects.stop()
        if self.controller.set_mode(mode):
            self.status_var.set(f"Device mode applied: {mode}")
        else:
            self.status_var.set("Could not apply device mode. Try running with sudo.")

    def _brightness_changed(self, value: str) -> None:
        if not self.controller.capabilities.supports_brightness:
            return
        level = int(float(value))
        self.brightness_var.set(level)
        if not self.controller.set_brightness(level):
            self.status_var.set("Could not set brightness. Try running with sudo.")

    def _refresh(self) -> None:
        self.effects.stop()
        self.controller.refresh()
        self._apply_capabilities()

    def _on_close(self) -> None:
        self.effects.stop()
        self.root.destroy()
