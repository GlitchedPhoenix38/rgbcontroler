# ASUS TUF Keyboard RGB Controller

A lightweight Python 3 Tkinter app for controlling keyboard lighting on ASUS TUF laptops on Linux, including Zorin OS and Ubuntu-based distributions.

The app uses Linux sysfs LED interfaces under `/sys/class/leds/` and detects exposed ASUS keyboard capabilities dynamically. Many ASUS laptops expose only keyboard brightness through `asus-nb-wmi` or `asus-wmi`; in that case the app keeps brightness control enabled and disables RGB controls.

## Files

- `main.py` - entry point
- `ui.py` - Tkinter dark-theme GUI
- `controller.py` - hardware discovery and sysfs writes
- `effects.py` - threaded non-blocking animations
- `utils.py` - logging and helper functions
- `setup.sh` - dependency check helper

## Features

- Static RGB color selection
- Rainbow animation
- Breathing/fade animation
- Color cycle, pulse, and wave animations
- Brightness slider
- Dynamic capability detection
- Error logging to `rgb_controller.log`

## Install

```bash
chmod +x setup.sh
./setup.sh
```

Tkinter is included with many Python installations. If it is missing on Ubuntu/Zorin:

```bash
sudo apt update
sudo apt install python3 python3-tk
```

## Run

Try normal user mode first:

```bash
python3 main.py
```

If brightness or color writes fail due to permissions, run with sudo:

```bash
sudo python3 main.py
```

## Hardware Notes

Linux support varies by ASUS model and kernel version.

- If RGB color paths are exposed, static color and software animations are enabled.
- If only brightness is exposed, the app shows: `Only brightness or limited modes supported on this device`.
- If kernel LED triggers are exposed through a `trigger` file, the controller can detect available modes, though most ASUS TUF laptops expose brightness only through standard sysfs.

Useful checks:

```bash
ls /sys/class/leds/
lsmod | grep -E 'asus_nb_wmi|asus_wmi'
```

Common keyboard LED names include `asus::kbd_backlight`, `input*::capslock`, and model-specific ASUS/Aura entries.

## Safety

This project writes only to sysfs files discovered under `/sys/class/leds/`. It does not install kernel modules or change boot configuration.
