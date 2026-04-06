from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

import easygradients as eg
import requests

__version__ = "1.0.0"
__product_name__ = "MuskDTA Launcher"
__description__ = "Launcher/wrapper for MuskServices DTA"
__company__ = "DraxonV1 / MuskServices"
__copyright__ = "Copyright (c) 2025 DraxonV1"
__author__ = "DraxonV1"

GITHUB_REPO = "DraxonV1/MuskServices-DTA"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
DISCORD_LINK = "https://discord.gg/dpk45Be2e3"

DATA_DIR = Path(os.path.expanduser("~")) / ".muskdta"
META_PATH = DATA_DIR / "meta.json"
CONFIG_PATH = DATA_DIR / "config.json"
AUTOUPD_PATH = DATA_DIR / "autoupdate"

DATA_DIR.mkdir(parents=True, exist_ok=True)

RESET = "\033[0m"
DIM = "\033[90m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

COLORS = [
    "\033[38;2;61;167;108m",
    "\033[38;2;61;175;112m",
    "\033[38;2;61;183;118m",
    "\033[38;2;61;191;124m",
    "\033[38;2;61;199;130m",
    "\033[38;2;61;207;134m",
]

def _visible_len(text):
    return len(ANSI_RE.sub("", text))

def _strip_ansi(text):
    return ANSI_RE.sub("", text)

def info(msg):    print(f"{COLORS[1]}[~]{RESET} {DIM}{msg}{RESET}")
def success(msg): print(f"{COLORS[3]}[+]{RESET} {COLORS[2]}{msg}{RESET}")
def warn(msg):    print(f"\033[38;2;255;170;0m[!]{RESET} {msg}")
def error(msg):   print(f"\033[38;2;255;68;68m[-]{RESET} {msg}")

_OS_MAP = {
    "Windows": ("windows", ".exe"),
    "Linux":   ("linux",   "-linux"),
    "Darwin":  ("macos",   "-macos"),
}

def _detect_os():
    sys_name = platform.system()
    return _OS_MAP.get(sys_name, (sys_name.lower(), ""))

def _tool_path_for_os():
    _, suffix = _detect_os()
    return DATA_DIR / f"tool{suffix}"

def _find_asset_for_os(release):
    _, suffix = _detect_os()
    assets = release.get("assets", [])
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(suffix.lower()):
            return asset
    return None

def _available_platforms(release):
    names = [a.get("name", "") for a in release.get("assets", [])]
    platforms = []
    for p, (key, suffix) in _OS_MAP.items():
        if any(n.lower().endswith(suffix.lower()) for n in names):
            platforms.append(p)
    return platforms

def print_banner():
    term_width = shutil.get_terminal_size((80, 20)).columns
    ascii_logo_raw = [
        "                    \u2593\u2593         \u2593\u2593                   ",
        "                  \u2593\u2593\u2593\u2593\u2593       \u2593\u2593\u2593\u2593                  ",
        "                 \u2593\u2593\u2593\u2593\u2593\u2593\u2593    \u2593\u2593\u2593\u2593\u2593\u2593\u2593                 ",
        "                \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593               ",
        "               \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593              ",
        "              \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593             ",
        "            \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593            ",
        "           \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593 \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593           ",
        "          \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593   \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593          ",
        "         \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593   \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593        ",
        "        \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2591  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593       ",
        "       \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593   \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593      ",
        "      \u2591\u2593\u2593\u2593\u2593\u2593\u2593\u2593   \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2593  \u2592\u2593\u2593\u2593\u2593\u2593\u2593\u2593      ",
    ]
    max_ascii_width = max(len(line) for line in ascii_logo_raw)
    available_width = term_width - 6
    if available_width < max_ascii_width:
        scale = available_width / max_ascii_width
        scaled = []
        for line in ascii_logo_raw:
            new_len = int(len(line) * scale)
            left_trim = (len(line) - new_len) // 2
            right_trim = len(line) - new_len - left_trim
            scaled.append(line[left_trim:len(line)-right_trim] if right_trim > 0 else line[left_trim:])
        ascii_logo_raw = scaled
        max_ascii_width = max(len(line) for line in ascii_logo_raw)
    inner_width = min(max_ascii_width + 4, term_width - 4)
    def box_line(text=""):
        clean_len = _visible_len(text)
        if clean_len > inner_width:
            text = _strip_ansi(text)[:inner_width]
            clean_len = len(text)
        pad_left = (inner_width - clean_len) // 2
        pad_right = inner_width - clean_len - pad_left
        return f"{DIM}\u2502{RESET} {' ' * pad_left}{text}{' ' * pad_right} {DIM}\u2502{RESET}"
    top    = f"{DIM}\u256d{'─' * (inner_width + 2)}\u256e{RESET}"
    bottom = f"{DIM}\u2570{'─' * (inner_width + 2)}\u256f{RESET}"
    ascii_logo = [f"{COLORS[i % len(COLORS)]}{line}{RESET}" for i, line in enumerate(ascii_logo_raw)]
    prefix = f"{DIM}[~]{RESET}"
    s1 = f"{prefix} {COLORS[1]}MuskServices.one DTA v7 {DIM}[Launcher v{__version__}]{RESET}"
    s2 = f"{prefix} {COLORS[1]}Worker & Private Mode{RESET}"
    s3 = f"{prefix} {DIM}discord.muskservices.one{RESET}"
    banner = "\n".join([top, box_line()] + [box_line(l) for l in ascii_logo] + [box_line(), box_line(s1), box_line(s2), box_line(s3), bottom])
    for line in banner.split("\n"):
        print(line.center(term_width))
    print()

def _fetch_latest_release():
    try:
        r = requests.get(GITHUB_API, timeout=10, headers={"User-Agent": "muskdta-launcher"})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        warn(f"Could not reach GitHub: {e}")
        return None

def _load_meta():
    try:
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_meta(data):
    META_PATH.write_text(json.dumps(data, indent=4), encoding="utf-8")

def _download_tool(asset, tag, tool_path):
    url = asset["browser_download_url"]
    filename = asset["name"]
    info(f"Downloading {filename} ({tag})")
    try:
        with requests.get(url, stream=True, timeout=120, headers={"User-Agent": "muskdta-launcher"}) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(tool_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = int(downloaded / total * 100)
                            bar = "\u2588" * (pct // 5) + "\u2591" * (20 - pct // 5)
                            sys.stdout.write(f"\r  {COLORS[2]}{bar}{RESET} {pct}%")
                            sys.stdout.flush()
        if platform.system() != "Windows":
            os.chmod(tool_path, 0o755)
        print()
        _save_meta({"version": tag, "asset": filename})
        success(f"Downloaded {filename} ({tag})")
    except Exception as e:
        error(f"Download failed: {e}")
        sys.exit(1)

def check_and_update(force=False):
    release = _fetch_latest_release()
    if release is None:
        return False

    tag = release.get("tag_name", "unknown")
    asset = _find_asset_for_os(release)

    if asset is None:
        current_os = platform.system()
        available = _available_platforms(release)
        available_str = ", ".join(available) if available else "none"
        error(f"No {current_os} binary detected.")
        error(f"Currently supported: {available_str}")
        sys.exit(1)

    tool_path = _tool_path_for_os()
    meta = _load_meta()

    if not tool_path.exists():
        info("Binary not found. Downloading ...")
        _download_tool(asset, tag, tool_path)
        return True
    if force:
        info(f"Forcing update to {tag} ...")
        _download_tool(asset, tag, tool_path)
        return True
    if meta.get("version") != tag:
        print(f"\n{COLORS[3]}[~] New update available: {tag}  Updating ...{RESET}\n")
        _download_tool(asset, tag, tool_path)
        return True
    success(f"Binary is up-to-date ({tag})")
    return False

TOOL_DEPS = ["requests", "pillow", "colorama"]

def install_deps():
    info("Checking dependencies ...")
    missing = []
    for dep in TOOL_DEPS:
        mod = dep.replace("-", "_").split("[")[0]
        try:
            __import__(mod)
        except ImportError:
            missing.append(dep)
    if not missing:
        success("All dependencies present.")
        return
    warn(f"Missing: {', '.join(missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + missing)
        success("Dependencies installed.")
    except subprocess.CalledProcessError as e:
        error(f"pip install failed: {e}")

def _ask(prompt, default=None, choices=None):
    if choices:
        hint = f" [{'/'.join(choices)}]"
    elif default is not None:
        hint = f" (default: {default})"
    else:
        hint = ""
    sys.stdout.write(f"  {COLORS[1]}{prompt}{DIM}{hint}{RESET}{DIM}: {RESET}")
    sys.stdout.flush()
    try:
        val = input().strip()
    except (EOFError, KeyboardInterrupt):
        val = ""
    if not val and default is not None:
        return str(default)
    if choices and val.lower() not in [c.lower() for c in choices]:
        warn(f"Invalid — using default: {default}")
        return str(default)
    return val or str(default or "")

def run_config_wizard():
    print(f"\n{COLORS[2]}[~] Config Setup{RESET}\n")
    ip_rotation = _ask("IP rotation mode", default="none", choices=["none", "adb", "vpn", "proxy"]).lower()
    mode = _ask("Account mode", default="worker", choices=["worker", "private"]).lower()
    http_lib = _ask("HTTP library", default="curl", choices=["curl", "requests", "rnet"]).lower()
    adb_rotate_every = 2
    if ip_rotation == "adb":
        try:
            adb_rotate_every = int(_ask("Rotate ADB IP every N accounts", default="2"))
        except ValueError:
            adb_rotate_every = 2
    proxy_mode = "http"
    if ip_rotation == "proxy":
        proxy_mode = _ask("Proxy protocol", default="http", choices=["http", "https", "socks5", "socks5h"]).lower()
    try:
        delay_between_accs = int(_ask("Delay between accounts (seconds)", default="0"))
    except ValueError:
        delay_between_accs = 0
    try:
        after_create_timer = int(_ask("Wait after account created (seconds)", default="0"))
    except ValueError:
        after_create_timer = 0
    return {
        "mode": mode,
        "ip_rotation": ip_rotation,
        "http_lib": http_lib,
        "adb_rotate_every": adb_rotate_every,
        "proxy_mode": proxy_mode,
        "delay_between_accs": delay_between_accs,
        "after_create_timer": after_create_timer,
        "notify": False,
        "notification_icon": "",
    }

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    success(f"Config saved to {CONFIG_PATH}")

def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def open_config_in_editor():
    if not CONFIG_PATH.exists():
        error("No config.json found. Run: muskdta config")
        return
    system = platform.system()
    if system == "Windows":
        os.startfile(str(CONFIG_PATH))
    elif system == "Darwin":
        subprocess.Popen(["open", "-e", str(CONFIG_PATH)])
    else:
        for ed in ["xdg-open", "nano", "vim", "vi"]:
            if shutil.which(ed):
                subprocess.Popen([ed, str(CONFIG_PATH)])
                break
    info(f"Opened {CONFIG_PATH}")

def is_auto_update_on():
    return AUTOUPD_PATH.exists()

def set_auto_update(state):
    if state:
        AUTOUPD_PATH.touch()
        success("Auto-update enabled.")
    else:
        AUTOUPD_PATH.unlink(missing_ok=True)
        success("Auto-update disabled.")

def launch_tool():
    tool_path = _tool_path_for_os()
    if not tool_path.exists():
        error(f"Binary not found ({tool_path.name}). Run: muskdta update")
        sys.exit(1)
    cfg = load_config()
    if cfg is None:
        error("config.json missing. Run: muskdta config")
        sys.exit(1)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
    info(f"Launching {tool_path.name} ...")
    try:
        result = subprocess.run([str(tool_path)], cwd=str(DATA_DIR))
        sys.exit(result.returncode)
    except FileNotFoundError:
        error(f"Could not execute {tool_path.name}.")
        sys.exit(1)
    except PermissionError:
        error("Permission denied. Try running as Administrator / sudo.")
        sys.exit(1)

def _print_status():
    meta = _load_meta()
    tool_path = _tool_path_for_os()
    print(f"\n{COLORS[2]}[~] MuskDTA Status{RESET}\n")
    print(f"  {DIM}Platform      {RESET}{platform.system()}")
    print(f"  {DIM}Binary        {RESET}{tool_path.name}")
    print(f"  {DIM}Version       {RESET}{COLORS[1]}{meta.get('version', 'not installed')}{RESET}")
    cfg_state = f"{COLORS[3]}present{RESET}" if CONFIG_PATH.exists() else f"\033[38;2;255;68;68mmissing{RESET}"
    print(f"  {DIM}Config        {RESET}{cfg_state}")
    au_state = f"{COLORS[3]}ON{RESET}" if is_auto_update_on() else f"\033[38;2;255;170;0mOFF{RESET}"
    print(f"  {DIM}Auto-update   {RESET}{au_state}")
    print(f"  {DIM}Data dir      {RESET}{DATA_DIR}")
    print()

def main():
    parser = argparse.ArgumentParser(prog="muskdta", description="MuskServices DTA launcher", add_help=True)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("update", help="Force download latest binary")
    sub.add_parser("discord", help="Open the MuskServices Discord")
    sub.add_parser("status", help="Show install status")
    cfg_p = sub.add_parser("config", help="Edit configuration")
    cfg_p.add_argument("mode", nargs="?", choices=["manual"], help="manual = open in editor")
    au_p = sub.add_parser("auto-update", help="Toggle automatic updates")
    au_p.add_argument("state", choices=["on", "off"])
    args = parser.parse_args()
    print_banner()
    if args.cmd == "discord":
        info("Opening Discord ...")
        webbrowser.open(DISCORD_LINK)
        return
    if args.cmd == "status":
        _print_status()
        return
    if args.cmd == "auto-update":
        set_auto_update(args.state == "on")
        return
    if args.cmd == "update":
        check_and_update(force=True)
        install_deps()
        return
    if args.cmd == "config":
        if args.mode == "manual":
            open_config_in_editor()
        else:
            save_config(run_config_wizard())
        return
    info("Running startup checks ...\n")
    if is_auto_update_on():
        check_and_update()
    else:
        tool_path = _tool_path_for_os()
        if not tool_path.exists():
            warn(f"Binary missing. Downloading ...")
            check_and_update()
        else:
            info(f"Auto-update is OFF. Installed: {_load_meta().get('version', 'unknown')}")
    install_deps()
    if not CONFIG_PATH.exists():
        warn("No config found.")
        save_config(run_config_wizard())
    else:
        cfg = load_config()
        if cfg is None:
            error("config.json is corrupted. Regenerating ...")
            save_config(run_config_wizard())
        else:
            success("Config OK")
    print()
    launch_tool()

if __name__ == "__main__":
    main()
