import time
import requests
import psutil
import os
from colorama import init
import json
import random
from enum import Enum
import asyncio
import string
import socket
from patchright.async_api import async_playwright
import multiprocessing
import sys
from notifypy import Notify
from datetime import datetime, timedelta, timezone
import shutil
import tempfile
import urllib3
from typing import Optional, Dict
import re
import subprocess
import warnings
import hashlib
import base64
import easygradients as eg
import tls_client
import websocket
import threading

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
init(autoreset=True)

SUPABASE_URL = "https://sohhkehctaakzjtyidjc.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNvaGhrZWhjdGFha3pqdHlpZGpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTI1ODI5NCwiZXhwIjoyMDg2ODM0Mjk0fQ.uVx9Kdjn6zlTvWBWN8uFsvritxJNqDkx1_L0tef2KAA"
SUPABASE_HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
}

GITHUB_BASE = "https://raw.githubusercontent.com/ThatSINEWAVE/Discord-Identity/refs/heads/main/data"

try:
    with open("config.json", "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {
        "mail_type": "outlook_premium",
        "mode": "normal",
        "check_ratelimit": False,
        "limit": 30,
        "after_create_timer": 30,
        "notify": False,
        "notification_icon": "",
        "discord_app_path": r"C:\Users\%USERNAME%\AppData\Local\Discord\app-1.0.9170\Discord.exe",
    }

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r"\033\[[0-9;]*m")


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Console:
    def __init__(
        self,
        log_to_file: bool = False,
        log_file: str = "discord_creator.log",
        log_level: LogLevel = LogLevel.INFO,
        max_file_size: int = 10 * 1024 * 1024,
    ) -> None:
        init(autoreset=True)
        self.print_lock = threading.Lock()
        self.log_to_file = log_to_file
        self.log_file = log_file
        self.log_level = log_level
        self.max_file_size = max_file_size
        if self.log_to_file:
            self._setup_file_logging()

    def _setup_file_logging(self):
        try:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            if (
                os.path.exists(self.log_file)
                and os.path.getsize(self.log_file) > self.max_file_size
            ):
                os.rename(self.log_file, self.log_file + ".old")
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
            self.log_to_file = False

    def _write_to_file(self, level: str, message: str):
        if not self.log_to_file:
            return
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def _log(self, symbol, color, message):
        with self.print_lock:
            timestamp = eg.color(f"[{self.timestamp()}]", "#9D26FF")
            symbol_colored = eg.color(f"[{symbol}]", color)
            msg = f"{timestamp} {symbol_colored} {eg.color(message, '#FFFFFF')}"
            print(msg)
            self._write_to_file(symbol, message)

    def info(self, message: str):
        self._log("!", "#00D9FF", message)

    def success(self, message: str):
        self._log("+", "#00FF88", message)

    def warning(self, message: str):
        self._log("⚠", "#FFD700", message)

    def error(self, message: str):
        self._log("✗", "#FF3366", message)

    def failure(self, message: str):
        self._log("✗", "#FF0000", message)

    def debug(self, message: str):
        self._log("•", "#A0A0A0", message)


log = Console(log_to_file=False, log_level=LogLevel.DEBUG)

LICENSE_FILE = "license.key"


def get_hwid():
    return hashlib.sha256(os.getenv("COMPUTERNAME", "unknown").encode()).hexdigest()


def get_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip", "unknown")
    except Exception:
        return "unknown"


def fetch_keys():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/key", headers=SUPABASE_HEADERS, timeout=10
        )
        response.raise_for_status()
        keys = response.json()
        return {item["key"]: item for item in keys}
    except Exception as e:
        log.error(f"Failed to fetch keys from database: {e}")
        return {}


def validate_key(input_key):
    keys = fetch_keys()
    hwid = get_hwid()

    if input_key not in keys:
        log.error("Invalid license key")
        return False

    key_data = keys[input_key]
    expiry_time = key_data.get("expiry")
    associated_hwid = key_data.get("hwid")

    try:
        if expiry_time:
            expiry_clean = expiry_time.replace("Z", "").split("+")[0].split(".")[0]
            try:
                expiry_date = datetime.strptime(expiry_clean, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    expiry_date = datetime.strptime(expiry_clean, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    expiry_date = datetime.fromisoformat(
                        expiry_time.replace("Z", "+00:00")
                    )
                    expiry_date = expiry_date.replace(tzinfo=None)

            log.success(f"License expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            log.error("No expiry date found for this license")
            return False
    except (ValueError, TypeError, AttributeError) as e:
        log.error(f"Invalid expiry format in database: {e}")
        return False

    current_time = datetime.now()
    if expiry_date < current_time:
        log.error("License has expired")
        return False

    if associated_hwid:
        if associated_hwid != hwid:
            log.error(
                "License is bound to another device. Request HWID reset from owner"
            )
            return False
    else:
        IST = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(IST)

        try:
            ip = get_ip()
            ip_history = key_data.get("ip_history")

            if ip_history:
                try:
                    ip_list = json.loads(ip_history)
                except:
                    ip_list = []
            else:
                ip_list = []

            if ip not in ip_list:
                ip_list.append(ip)

            update_data = {
                "hwid": hwid,
                "ip": ip,
                "last_login": now_ist.isoformat(),
                "ip_count": len(ip_list),
                "ip_history": json.dumps(ip_list),
            }

            res = requests.patch(
                f"{SUPABASE_URL}/rest/v1/key?key=eq.{input_key}",
                headers=SUPABASE_HEADERS,
                data=json.dumps(update_data),
                timeout=10,
            )

            if res.status_code not in [200, 204]:
                log.error(f"Failed to bind HWID: {res.text}")
            else:
                log.success("HWID bound successfully")
        except Exception as e:
            log.error(f"Error updating HWID: {e}")

    return True


def get_license_key():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as f:
            license_key = f.read().strip()
            if license_key:
                log.info(f"Using saved license: {license_key[:8]}...")
                return license_key

    license_key = input(eg.color("Enter License Key: ", "#FFD700")).strip()
    with open(LICENSE_FILE, "w") as f:
        f.write(license_key)
    return license_key


def fetch_zeus_api_key():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/settings?key=eq.zeus_api_key",
            headers=SUPABASE_HEADERS,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                zeus_key = data[0].get("value")
                if zeus_key:
                    log.success("Zeus API key fetched from database")
                    return zeus_key
        log.error("Zeus API key not found in database. Contact administrator")
        return None
    except Exception as e:
        log.error(f"Failed to fetch Zeus API key: {e}")
        return None


def fetch_mail_type():
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/settings?key=eq.mail_type",
            headers=SUPABASE_HEADERS,
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                mail_type = data[0].get("value")
                if mail_type:
                    log.success(f"Mail type from database: {mail_type}")
                    return mail_type
        log.error("Mail type not set in database. Contact administrator")
        return None
    except Exception as e:
        log.error(f"Failed to fetch mail type: {e}")
        return config.get("mail_type", "outlook_premium")


def log_ev_to_supabase(ev_line: str, input_key: str, table: str):
    try:
        payload = {"ev": ev_line, "key": input_key}
        requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=SUPABASE_HEADERS,
            data=json.dumps(payload),
            timeout=10,
        )
        log.success(f"Token logged to {table} table")
    except Exception as e:
        log.error(f"Failed to log token to {table}: {e}")


def fetch_github_json(filename):
    try:
        url = f"{GITHUB_BASE}/{filename}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log.error(f"Failed to fetch {filename}: {e}")
        return None


def get_random_username():
    data = fetch_github_json("usernames.json")
    if data and isinstance(data, list):
        return random.choice(data)
    return "".join(random.choices(string.ascii_letters, k=8))


def get_random_nickname():
    data = fetch_github_json("nicknames.json")
    if data and isinstance(data, list):
        return random.choice(data)
    return "".join(random.choices(string.ascii_letters, k=8))


def get_random_pronouns():
    data = fetch_github_json("pronouns.json")
    if data and isinstance(data, list):
        return random.choice(data)
    return None


def get_random_bio():
    data = fetch_github_json("about_me.json")
    if data and isinstance(data, dict) and "sentences" in data:
        return random.choice(data["sentences"])
    return None


def get_random_avatar_url():
    number = random.randint(1, 1000)
    return f"https://raw.githubusercontent.com/ThatSINEWAVE/Discord-Identity/refs/heads/main/data/images/image_{number:02d}.png"


def generate_random_name():
    return "".join(random.choices(string.ascii_letters, k=8))


def generate_random_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choices(chars, k=14))


_PROBE_PASSWORD = "$TermTUSiCE2169#"


def account_ratelimit(email=None, nam=None):
    try:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "DNT": "1",
            "Host": "discord.com",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/register",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "Asia/Calcutta",
        }
        mailbaba = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
        email = mailbaba + "@gmail.com"
        nam = generate_random_name()
        data = {
            "email": email,
            "password": _PROBE_PASSWORD,
            "date_of_birth": "2000-09-20",
            "username": email,
            "global_name": nam,
            "consent": True,
            "captcha_service": "hcaptcha",
            "captcha_key": None,
            "invite": None,
            "promotional_email_opt_in": False,
            "gift_code_sku_id": None,
        }
        req = requests.post(
            "https://discord.com/api/v9/auth/register", json=data, headers=headers
        )
        try:
            resp_data = req.json()
        except Exception as je:
            return 1
        if req.status_code == 429 or "retry_after" in resp_data:
            limit = resp_data.get("retry_after", 1)
            return int(float(limit)) + 1 if limit else 1
        else:
            return 1
    except Exception as e:
        log.failure(f"Account ratelimit crashed: {e}")
        return 1


def countdown_timer(duration):
    for i in range(duration):
        msg = eg.color(
            f"[{i + 1:02d}/{duration}] Waiting before next account...", "#FFD700"
        )
        print(f"\r{msg}", end="", flush=True)
        time.sleep(1)
    print()


def close_brave(profile_dir):
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = proc.info.get("name")
            cmdline = proc.info.get("cmdline")

            if not name or not cmdline:
                continue

            if "brave" in name.lower():
                cmd = " ".join(cmdline).lower()
                if profile_dir.lower() in cmd:
                    proc.kill()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
            TypeError,
        ):
            continue
    shutil.rmtree(profile_dir, ignore_errors=True)


months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


async def click_dropdown_option(page, expected_text):
    js = f"""
        (() => {{
            const options = document.querySelectorAll('div[role="option"]');
            for (const opt of options) {{
                if (opt.innerText.trim().toLowerCase() === "{expected_text.lower()}") {{
                    opt.click();
                    return true;
                }}
            }}
            return false;
        }})()
    """
    result = await page.evaluate(js)
    return result


def send_notification(title, message):
    if not config.get("notify", False):
        return
    try:
        notification = Notify()
        notification.application_name = "Worker Gen"
        notification.title = title
        notification.message = message
        icon_path = config.get("notification_icon")
        if icon_path and os.path.isfile(icon_path):
            notification.icon = icon_path
        notification.send()
    except Exception as e:
        log.error(f"Notification error: {e}")


class EmailProvider:
    def __init__(self, api_key, mail_type):
        self.session = requests.Session()
        self.api_key = api_key
        self.mail_type = mail_type
        self.api_base = "https://api.zeus-x.ru"

    def _fetch_email(self) -> Optional[Dict]:
        url = f"{self.api_base}/purchase"
        params = {"apikey": self.api_key, "accountcode": self.mail_type, "quantity": 1}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            data = resp.json()
            if resp.status_code == 200:
                if (
                    data.get("Code") == 0
                    and "Data" in data
                    and "Accounts" in data["Data"]
                ):
                    accounts = data["Data"]["Accounts"]
                    if accounts:
                        account = accounts[0]
                        return {
                            "email": account.get("Email", ""),
                            "password": account.get("Password", ""),
                            "token": account.get("RefreshToken", ""),
                            "uuid": account.get("ClientId", "")
                            if account.get("ClientId")
                            else "",
                        }
                    else:
                        log.debug(f"Zeus: No accounts in response")
                elif isinstance(data, dict) and "INSUFFICIENT STOCK" in str(
                    data.get("Message", "")
                ):
                    return "INSUFFICIENT_STOCK"
                else:
                    log.debug(f"Zeus API response: {data}")
            else:
                if isinstance(data, dict) and "INSUFFICIENT STOCK" in str(
                    data.get("Message", "")
                ):
                    return "INSUFFICIENT_STOCK"
                log.debug(f"Zeus HTTP {resp.status_code}: {data}")
        except Exception as e:
            log.debug(f"Zeus request error: {e}")
        return None

    def purchase(self) -> Optional[Dict]:
        start_time = time.time()
        timeout = 20
        while (time.time() - start_time) < timeout:
            account = self._fetch_email()
            if account == "INSUFFICIENT_STOCK":
                log.error("Insufficient stock on Zeus API — exiting")
                return "INSUFFICIENT_STOCK"
            if account:
                return account
            time.sleep(1)
        return None


MS_CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"


class DiscordHumanizer:
    def __init__(self):
        self.session = tls_client.Session(
            client_identifier="chrome_120", random_tls_extension_order=True
        )

    def get_headers(self, token: str) -> dict:
        return {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/channels/@me",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwLjAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ==",
        }

    def go_online(self, token: str):
        try:
            import websocket as ws_module
            import time

            ws = ws_module.WebSocket()
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            hello = json.loads(ws.recv())
            heartbeat_interval = hello["d"]["heartbeat_interval"] / 1000

            status = random.choice(["online", "dnd", "idle"])
            activities = [
                {"name": "Visual Studio Code", "type": 0},
                {"name": "Spotify", "type": 2},
                {"name": "YouTube", "type": 3},
            ]
            gamejson = random.choice(activities) if random.random() > 0.3 else None

            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "Windows",
                        "$browser": "Chrome",
                        "$device": "Windows",
                    },
                    "presence": {
                        "activities": [gamejson] if gamejson else [],
                        "status": status,
                        "since": 0,
                        "afk": False,
                    },
                },
            }
            ws.send(json.dumps(auth))
            time.sleep(1)
            ws.recv()
            return ws, heartbeat_interval
        except Exception as e:
            log.debug(f"WebSocket connection error: {e}")
            return None, None

    def send_heartbeat(self, ws, heartbeat_interval: float):
        import threading
        import time
        import json

        try:
            if not ws or not heartbeat_interval:
                return

            def _heartbeat_loop():
                while True:
                    try:
                        ws.send(json.dumps({"op": 1, "d": None}))
                        time.sleep(heartbeat_interval)
                    except Exception:
                        break  # stop loop if ws closes

            threading.Thread(
                target=_heartbeat_loop,
                daemon=True
            ).start()

        except Exception:
            pass

    def update_avatar(self, token: str, avatar_b64: str) -> bool:
        try:
            headers = self.get_headers(token)
            payload = {"avatar": f"data:image/png;base64,{avatar_b64}"}
            response = self.session.patch(
                "https://discord.com/api/v9/users/@me", headers=headers, json=payload
            )
            if response.status_code == 200:
                log.success("Avatar set successfully")
                return True
            else:
                log.debug(f"Avatar update returned: {response.status_code}")
                return False
        except Exception as e:
            log.debug(f"Avatar error: {e}")
            return False

    def update_profile(self, token: str, pronouns: str = None, bio: str = None) -> bool:
        try:
            headers = self.get_headers(token)
            payload = {}
            if pronouns:
                payload["pronouns"] = pronouns
            if bio:
                payload["bio"] = bio

            if not payload:
                return True

            response = self.session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=headers,
                json=payload,
            )
            if response.status_code == 200:
                log.success("Profile (pronouns/bio) set successfully")
                return True
            else:
                log.debug(f"Profile update returned: {response.status_code}")
                return False
        except Exception as e:
            log.debug(f"Profile error: {e}")
            return False

    def humanize(
        self, token: str, avatar_b64: str = None, pronouns: str = None, bio: str = None
    ) -> bool:
        log.info("Starting account humanization...")

        ws, heartbeat_interval = self.go_online(token)
        time.sleep(random.uniform(1.0, 2.0))

        if ws and heartbeat_interval:
            self.send_heartbeat(ws, heartbeat_interval)

        if avatar_b64:
            time.sleep(random.uniform(1.0, 2.0))
            self.update_avatar(token, avatar_b64)

        if pronouns or bio:
            time.sleep(random.uniform(1.0, 2.0))
            self.update_profile(token, pronouns, bio)

        log.success("Account humanization completed")
        return True


def get_access_token(refresh_token: str, client_id: str = None) -> Optional[str]:
    try:
        cid = client_id or MS_CLIENT_ID
        if refresh_token.endswith("$"):
            refresh_token = refresh_token[:-1]
        response = requests.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": cid,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=30,
            verify=False,
        )
        result = response.json()
        return result.get("access_token")
    except Exception as e:
        return None


def fetch_verification_url(email_data: Dict, timeout: int = 120) -> Optional[str]:
    refresh_token = email_data.get("token", "")
    client_id = email_data.get("uuid", "") or MS_CLIENT_ID
    access_token = get_access_token(refresh_token, client_id)
    if not access_token:
        return None
    start_time = time.time()
    attempt = 0
    while (time.time() - start_time) < timeout:
        attempt += 1
        try:
            response = requests.get(
                "https://graph.microsoft.com/v1.0/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "$top": 5,
                    "$orderby": "receivedDateTime desc",
                    "$select": "subject,body,from,bodyPreview,receivedDateTime",
                },
                timeout=15,
            )
            emails = response.json().get("value", [])
            if attempt % 3 == 0:
                elapsed = int(time.time() - start_time)
            for email in emails:
                subject = email.get("subject", "").lower()
                from_addr = (
                    email.get("from", {})
                    .get("emailAddress", {})
                    .get("address", "")
                    .lower()
                )
                is_verify_email = (
                    "verify" in subject or "confirm" in subject or "email" in subject
                ) and ("discord" in from_addr or "noreply@discord.com" in from_addr)
                if not is_verify_email:
                    continue
                body_html = email.get("body", {}).get("content", "")
                verify_pattern = r'https://discord\.com/verify\?token=[^"\'\>\s]+'
                direct_match = re.search(verify_pattern, body_html)
                if direct_match:
                    return direct_match.group(0)
                click_patterns = [
                    r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                    r'https://links\.discord\.com[^"\'\>\s]+',
                ]
                for pat in click_patterns:
                    for m in re.finditer(pat, body_html):
                        url = m.group(0)
                        try:
                            resp = requests.get(
                                url, allow_redirects=True, timeout=15, verify=False
                            )
                            final_url = resp.url
                            if "discord.com/verify" in final_url:
                                return final_url
                            verify_in_body = re.search(
                                r'https://discord\.com/verify\?token=[^"\'\>\s]+',
                                resp.text,
                            )
                            if verify_in_body:
                                return verify_in_body.group(0)
                        except:
                            pass
        except Exception as e:
            log.error(f"Graph API error: {e}")
        time.sleep(1)
    return None


def gen_username():
    first_names = [
        "Alex",
        "Jordan",
        "Taylor",
        "Casey",
        "Morgan",
        "Riley",
        "Avery",
        "Quinn",
        "Blake",
        "Cameron",
        "Drew",
        "Hayden",
        "Jamie",
        "Kendall",
        "Logan",
        "Parker",
        "Sage",
        "Skylar",
        "Reese",
        "Phoenix",
        "River",
        "Rowan",
        "Dakota",
        "Emery",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
        "Taylor",
        "Moore",
        "Jackson",
        "Martin",
        "Lee",
        "Perez",
        "Thompson",
        "White",
        "Harris",
        "Sanchez",
        "Clark",
        "Ramirez",
        "Lewis",
        "Robinson",
        "Walker",
    ]
    tech_words = [
        "Tech",
        "Code",
        "Byte",
        "Pixel",
        "Data",
        "Neo",
        "Cyber",
        "Digital",
        "Virtual",
        "Alpha",
        "Beta",
        "Prime",
        "Core",
        "Edge",
        "Link",
        "Node",
        "Grid",
        "Wave",
    ]
    style = random.choice(["realistic", "gaming", "mixed"])
    use_underscore = random.choice([True, False, False, False, True])
    if style == "realistic":
        first = random.choice(first_names)
        last = random.choice(last_names)
        num = random.randint(10, 999)
        if use_underscore:
            username = f"{first.lower()}_{last.lower()}{num}___"
        else:
            username = f"{first.lower()}{last.lower()}{num}___"
        display_name = f"{first} {last}"
    elif style == "gaming":
        tech = random.choice(tech_words)
        name = random.choice(first_names)
        num = random.randint(100, 9999)
        if use_underscore:
            username = f"{tech.lower()}_{name.lower()}{num}___"
        else:
            username = f"{tech.lower()}{name.lower()}{num}___"
        display_name = f"{tech} {name}"
    else:
        first = random.choice(first_names)
        tech = random.choice(tech_words)
        num = random.randint(10, 999)
        if use_underscore:
            username = f"{first.lower()}_{tech.lower()}{num}___"
        else:
            username = f"{first.lower()}{tech.lower()}{num}___"
        display_name = f"{first} {tech}"
    return username, display_name


adb_failed = False


def check_adb_available() -> bool:
    try:
        result = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=5
        )
        return "\tdevice" in result.stdout
    except:
        return False


def rotate_ip(mode):
    global adb_failed
    if mode == "adb":
        if adb_failed:
            if check_adb_available():
                adb_failed = False
            else:
                cooldown = account_ratelimit()
                log.warning(f"Rate limited — waiting {cooldown} seconds...")
                return
        try:
            subprocess.run(
                ["adb", "shell", "cmd", "connectivity", "airplane-mode", "enable"],
                check=True,
                capture_output=True,
            )
            time.sleep(1)
            subprocess.run(
                ["adb", "shell", "cmd", "connectivity", "airplane-mode", "disable"],
                check=True,
                capture_output=True,
            )
            time.sleep(4)
            log.success("IP Rotated via ADB")
            time.sleep(3)
        except Exception as e:
            adb_failed = True
            cooldown = account_ratelimit()
            log.warning(f"Rate limited — waiting {cooldown} seconds...")
            countdown_timer(cooldown)
    elif mode == "vpn":
        cooldown = config.get("timer")
        log.info(f"VPN Mode Waiting {cooldown}s for user IP change")
        countdown_timer(cooldown)
    else:
        cooldown = account_ratelimit()
        log.warning(f"Rate limited — waiting {cooldown} seconds...")
        countdown_timer(cooldown)


async def safe_stop(context=None, playwright_instance=None, discord_proc=None, temp_dir=None):
    if context:
        try:
            await asyncio.wait_for(context.close(), timeout=5)
        except Exception:
            pass
    if playwright_instance:
        try:
            await asyncio.wait_for(playwright_instance.stop(), timeout=5)
        except Exception:
            pass
    if discord_proc:
        try:
            discord_proc.terminate()
            discord_proc.wait(timeout=5)
        except Exception:
            try:
                discord_proc.kill()
            except Exception:
                pass
    await asyncio.sleep(0.5)
    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_token_via_login(email: str, password: str) -> Optional[str]:
    try:
        session = tls_client.Session(client_identifier="chrome_120")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/login",
        }
        payload = {"login": email, "password": password}
        response = session.post(
            "https://discord.com/api/v9/auth/login", headers=headers, json=payload
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                log.success(f"Token fetched: {token[:25]}***")
                return token
        log.error(f"Login failed: {response.status_code}")
        return None
    except Exception as e:
        log.error(f"Token fetch error: {e}")
        return None


def check_token_status(token: str) -> str:
    try:
        session = tls_client.Session(client_identifier="chrome_120")
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        response = session.get(
            "https://discord.com/api/v9/users/@me/guilds", headers=headers
        )

        if response.status_code == 200:
            return "valid"
        elif response.status_code == 401:
            return "invalid"
        elif response.status_code in [403, 423]:
            return "locked"
        return "unknown"
    except Exception:
        return "unknown"


def humanize_account(token: str) -> bool:
    try:
        humanizer = DiscordHumanizer()

        avatar_b64 = None
        avatar_url = get_random_avatar_url()
        try:
            avatar_resp = requests.get(avatar_url, timeout=10)
            if avatar_resp.status_code == 200:
                avatar_b64 = base64.b64encode(avatar_resp.content).decode()
        except Exception:
            pass

        pronouns = get_random_pronouns()
        bio = get_random_bio()

        humanizer.humanize(token, avatar_b64, pronouns, bio)
        return True
    except Exception as e:
        log.debug(f"Humanization error: {e}")
        return False

_proxy_lock = threading.Lock()

def get_session_proxy(file_path="proxies.txt"):
    """
    Supports formats:
      host:port
      host:port:username:password   (Zeus-style)
      username:password@host:port   (standard URI style)

    Returns: (proxy_url, username, password)
      proxy_url -> "http://host:port"
      username/password -> None if not required
    """

    with _proxy_lock:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                proxies = [p.strip() for p in f if p.strip()]
        except FileNotFoundError:
            raise Exception("proxies.txt not found")

        if not proxies:
            raise Exception("No proxies left in proxies.txt")

        proxy_line = random.choice(proxies)
        proxies.remove(proxy_line)

        with open(file_path, "w", encoding="utf-8") as f:
            if proxies:
                f.write("\n".join(proxies) + "\n")

    # Detect user:pass@host:port format first
    if "@" in proxy_line:
        credentials, hostport = proxy_line.rsplit("@", 1)
        if ":" in credentials:
            username, password = credentials.split(":", 1)
        else:
            raise ValueError(f"Invalid proxy format (missing password): {proxy_line}")
        return f"http://{hostport}", username, password

    parts = proxy_line.split(":")

    if len(parts) == 2:
        host, port = parts
        return f"http://{host}:{port}", None, None

    elif len(parts) == 4:
        host, port, username, password = parts
        return f"http://{host}:{port}", username, password

    else:
        raise ValueError(f"Invalid proxy format: {proxy_line}")


async def register_and_get_promo(license_key, zeus_api_key, is_last_instance=False):
    discord_proc = None
    context = None
    playwright_instance = None
    page = None
    temp_discord_dir = None

    try:
        proxy_url, proxy_user, proxy_pass = get_session_proxy()

        # Strip scheme to get raw host:port for --proxy-server arg
        proxy_host_port = proxy_url.replace("http://", "").replace("https://", "")

        # Find a free local port for Chrome DevTools Protocol
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _s:
            _s.bind(("127.0.0.1", 0))
            cdp_port = _s.getsockname()[1]

        discord_path = os.path.expandvars(
            config.get(
                "discord_app_path",
                r"C:\Users\%USERNAME%\AppData\Local\Discord\app-1.0.9170\Discord.exe",
            )
        )

        if not os.path.isfile(discord_path):
            raise FileNotFoundError(
                f"Discord executable not found at: {discord_path}\n"
                "Update 'discord_app_path' in config.json"
            )

        # Fresh isolated profile every run — no saved login, cookies, or session
        temp_discord_dir = tempfile.mkdtemp(prefix="discord-fresh-")

        discord_proc = subprocess.Popen(
            [
                discord_path,
                f"--remote-debugging-port={cdp_port}",
                f"--proxy-server={proxy_host_port}",
                f"--user-data-dir={temp_discord_dir}",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-breakpad",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info(f"Launched Discord (PID {discord_proc.pid}) on CDP port {cdp_port} with fresh profile")

        # Poll until the CDP endpoint is ready (up to 45 seconds)
        cdp_url = f"http://127.0.0.1:{cdp_port}"
        startup_deadline = time.time() + 45
        while time.time() < startup_deadline:
            try:
                r = requests.get(f"{cdp_url}/json/version", timeout=2)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError(
                f"Discord CDP endpoint not ready on port {cdp_port} after 45 seconds"
            )

        await asyncio.sleep(2)  # let the renderer finish painting

        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.connect_over_cdp(cdp_url)

        contexts = browser.contexts
        context = contexts[0] if contexts else await browser.new_context()

        pages = context.pages
        page = pages[0] if pages else await context.new_page()

        # Authenticate proxy credentials if present
        if proxy_user and proxy_pass:
            await page.authenticate({"username": proxy_user, "password": proxy_pass})

        await page.goto(
            "https://discord.com/register",
            wait_until="domcontentloaded",
            timeout=60_000,
        )

    except Exception as e:
        log.error(f"Failed to launch Discord app: {e}")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return

    log.info("Loaded Register Page")

    mail_type = fetch_mail_type()
    if not mail_type:
        log.error("Cannot proceed without mail type. Contact administrator")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return
    email_provider = EmailProvider(zeus_api_key, mail_type)
    email_data = email_provider.purchase()

    if email_data == "INSUFFICIENT_STOCK":
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        sys.exit(1)

    if not email_data:
        log.error("Failed to purchase email from Zeus API")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        if not is_last_instance:
            rotate_ip(config.get("mode"))
        return

    email = email_data.get("email")
    password = email_data.get("password")
    refresh_token = email_data.get("token")
    client_id = email_data.get("uuid")

    if not email or not password:
        log.error(f"Invalid email payload received")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return

    log.info(f"Using email: {email}")

    username = get_random_username()
    global_name = get_random_nickname()

    log.info(f"Using username: {username}, global_name: {global_name}")

    discord_password = generate_random_password()

    for name, value in [
        ("email", email),
        ("global_name", global_name),
        ("username", username),
        ("password", discord_password),
    ]:
        field = await page.wait_for_selector(f'input[name="{name}"]', timeout=120_000)
        if not field:
            log.error(f"{name} input not found")
            return
        await field.fill(value)
        await asyncio.sleep(0.05)

    month = random.choice(months)
    day = str(random.randint(1, 28))
    year = str(random.randint(1995, 2005))

    for label, value in [("Month", month), ("Day", day), ("Year", year)]:
        dropdown = await page.wait_for_selector(
            f'div[role="button"][aria-label="{label}"]', timeout=30_000
        )
        if not dropdown:
            log.error(f"{label} dropdown not found")
            return
        await dropdown.click()
        await asyncio.sleep(0.1)
        if not await click_dropdown_option(page, value):
            log.warning(f"Failed to select {label}={value}, retrying...")
            await asyncio.sleep(0.1)

    checkbox = await page.query_selector('input[type="checkbox"]')
    if checkbox:
        await checkbox.click()
        await asyncio.sleep(0.05)

    submit_btn = await page.query_selector('button[type="submit"]')
    if submit_btn:
        await submit_btn.click()
        log.success("Submitted Registration Form")
    else:
        log.error("Submit button not found")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return

    log.warning("Please Solve Captcha Manually!")
    send_notification("Worker Gen", "Please solve the CAPTCHA!")

    for attempt in range(300):
        try:
            current_url = await page.evaluate("window.location.href")
            if "discord.com/channels/@me" in current_url:
                log.success("Captcha successfully solved!")
                await asyncio.sleep(random.uniform(2.0, 4.0))
                break
        except Exception as e:
            log.error(f"Error while captcha verification: {e}")
        await asyncio.sleep(1)
    else:
        log.error("CAPTCHA not solved or redirect failed")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return

    await asyncio.sleep(random.uniform(1.0, 2.0))
    verify_url = fetch_verification_url(email_data, timeout=120)
    log.success("Email Verification link fetched!")

    if verify_url:
        await page.evaluate(f'''
            (() => {{
                window.open("{verify_url}", "_blank");
                return "ok";
            }})()
        ''')
    else:
        log.error("Could not find verification link in email")
        await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
        return

    await asyncio.sleep(2)  # allow _blank tab to open
    verify_pages = context.pages
    verify_tab = verify_pages[-1]

    for attempt in range(60):
        try:
            page_text = await verify_tab.evaluate("""
                (() => {
                    return document.body?.innerText || "NO_TEXT_FOUND";
                })()
            """)
            if "email verified" in page_text.lower():
                log.success("Email verified successfully!")
                log.success("Account verified successfully!")

                await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)
                context = None
                playwright_instance = None
                discord_proc = None
                temp_discord_dir = None

                await asyncio.sleep(random.uniform(1.5, 3.0))

                token = get_token_via_login(email, discord_password)

                if token:
                    status = check_token_status(token)
                    ev_line = f"{email}:{discord_password}:{token}"

                    if status == "invalid":
                        log_ev_to_supabase(ev_line, license_key, "invalid")
                        log.warning("Token is invalid — logged to invalid table")
                    elif status == "locked":
                        log_ev_to_supabase(ev_line, license_key, "locked")
                        log.warning("Account is locked — logged to locked table")
                    else:
                        humanize_account(token)
                        log_ev_to_supabase(ev_line, license_key, "evs")
                        log.success("Account Created Successfully")

                cooldown = config.get("after_create_timer", 30)
                log.info(f"Waiting {cooldown} seconds before next account...")
                countdown_timer(cooldown)
                return
        except Exception as e:
            if "Target closed" in str(e) or "Session closed" in str(e):
                break
            log.error(f"Verification check error: {e}")
        await asyncio.sleep(1)

    log.error("Email verification not detected in time")
    await safe_stop(context, playwright_instance, discord_proc, temp_dir=temp_discord_dir)

    if not is_last_instance:
        mode = config.get("mode")
        rotate_ip(mode)


def display_ascii_banner():
    r, g = "\033[0m", "\033[90m"

    c1, c2, c3, c4, c5, c6, c7, c8 = [
        "\033[38;2;0;245;160m",
        "\033[38;2;0;241;170m",
        "\033[38;2;0;237;180m",
        "\033[38;2;0;233;190m",
        "\033[38;2;0;229;200m",
        "\033[38;2;0;225;210m",
        "\033[38;2;0;221;220m",
        "\033[38;2;0;217;245m",
    ]

    ansi_re = re.compile(r"\x1b\[[0-9;]*m")

    def visible_len(text: str) -> int:
        return len(ansi_re.sub("", text))

    term_width = shutil.get_terminal_size((80, 20)).columns
    inner_width = min(52, term_width - 4)

    def box_line(text=""):
        clean_len = visible_len(text)
        if clean_len > inner_width:
            text = ansi_re.sub("", text)[:inner_width]
            clean_len = len(text)

        pad_left = (inner_width - clean_len) // 2
        pad_right = inner_width - clean_len - pad_left

        return f"{g}│{r} {' ' * pad_left}{text}{' ' * pad_right} {g}│{r}"

    top = f"{g}╭{'─' * (inner_width + 2)}╮{r}"
    bottom = f"{g}╰{'─' * (inner_width + 2)}╯{r}"

    ascii_logo = [
        f"{c1}████▄{r}  {c2}▄▄▄▄{r}   {c3}▄▄▄{r}  {c4}▄▄{r} {c5}▄▄{r}  {c6}▄▄▄{r}  {c7}▄▄{r}  {c8}▄▄{r}",
        f"{c1}██  ██{r} {c2}██▄█▄{r} {c3}██▀██{r} {c4}▀█▄█▀{r} {c5}██▀██{r} {c6}███▄██{r}",
        f"{c1}████▀{r}  {c2}██ ██{r} {c3}██▀██{r} {c4}██ ██{r} {c5}▀███▀{r} {c6}██ ▀██{r}",
    ]

    prefix = f"{g}[~]{r}"
    subtitle_1 = f"{prefix} {c2}Worker-Based Discord Generator{r}"
    subtitle_2 = f"{prefix} {c2}Supabase Integrated{r}"
    footer = f"{prefix} {g}Made by @DraxonV1 · v3.00{r}"

    banner = "\n".join(
        [top, box_line()]
        + [box_line(l) for l in ascii_logo]
        + [
            box_line(),
            box_line(subtitle_1),
            box_line(subtitle_2),
            box_line(footer),
            bottom,
        ]
    )

    lines = banner.split("\n")
    for line in lines:
        print(line.center(term_width))


def check_zeus_balance(api_key: str) -> Optional[float]:
    url = "https://api.zeus-x.ru/balance"
    params = {"apikey": api_key}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not isinstance(data, dict):
            log.error("Zeus balance response malformed")
            return None

        if data.get("Code") != 0:
            log.error(f"Zeus API error: {data}")
            return None

        balance = data.get("Balance")
        if balance is None:
            log.error("Zeus balance missing in response")
            return None

        log.success(f"Zeus Balance: {balance}")
        return float(balance)

    except requests.exceptions.Timeout:
        log.error("Zeus balance request timed out")
    except requests.exceptions.HTTPError as e:
        log.error(f"Zeus balance HTTP error: {e}")
    except ValueError:
        log.error("Zeus balance JSON parse failed")
    except Exception as e:
        log.error(f"Zeus balance unexpected error: {e}")

    return None


def run_register_and_get_promo(license_key, zeus_api_key, is_last_instance=False):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            register_and_get_promo(license_key, zeus_api_key, is_last_instance)
        )
    except Exception as e:
        log.error(f"Registration error: {e}")
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )
        except Exception:
            pass
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        try:
            loop.run_until_complete(loop.shutdown_default_executor())
        except Exception:
            pass
        loop.close()


def main():
    license_key = get_license_key()
    if not validate_key(license_key):
        log.failure("Invalid or expired license key. Exiting...")
        sys.exit(1)

    zeus_api_key = fetch_zeus_api_key()
    if not zeus_api_key:
        log.failure("Cannot proceed without Zeus API key. Contact administrator")
        sys.exit(1)

    if zeus_api_key:
        balance = check_zeus_balance(zeus_api_key)
        if balance is None or balance <= 0:
            log.warning("Zeus balance low or unavailable")

    multiprocessing.freeze_support()

    try:
        instance_count = 1
    except ValueError:
        log.warning("Invalid input. Defaulting to 1 instance")
        instance_count = 1

    try:
        max_runs_input = input(
            eg.color("Number of accounts to generate (0 = infinite): ", "#00D9FF")
        )
        max_runs = int(max_runs_input)
    except ValueError:
        log.warning("Invalid input. Defaulting to 1 account")
        max_runs = 1

    run_count = 0
    active_processes = []

    while True:
        active_processes = [p for p in active_processes if p.is_alive()]
        if len(active_processes) < instance_count and (
            max_runs == 0 or run_count < max_runs
        ):
            run_count += 1
            log.info(f"Starting account #{run_count}")
            try:
                is_last = max_runs != 0 and run_count == max_runs
                p = multiprocessing.Process(
                    target=run_register_and_get_promo,
                    args=(
                        license_key,
                        zeus_api_key,
                        is_last,
                    ),
                )
                p.start()
                active_processes.append(p)
            except Exception as e:
                log.failure(f"Failed to launch process: {e}")

        if max_runs and run_count >= max_runs and not active_processes:
            break

        time.sleep(1)

    for p in active_processes:
        p.join(timeout=300)

    log.success("All account generations completed!")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("\n")
    display_ascii_banner()
    print("\n")
    main()