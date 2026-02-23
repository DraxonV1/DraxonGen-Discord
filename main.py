import time
import requests
import psutil
import os
from colorama import init, Fore, Style
import json
import datetime
import random
from enum import Enum
import asyncio
import string
import nodriver as uc
import multiprocessing
import sys
from pystyle import Center
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
import websockets

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*unclosed transport.*")
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited.*")
warnings.filterwarnings("ignore", message=".*I/O operation on closed pipe.*")
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
    }

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r"\033\[[0-9;]*m")

import threading


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
        return None


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


def log_wasted_email(email_data: dict, license_key: str, category: str):
    try:
        payload = {
            "email_data": json.dumps(email_data),
            "email": email_data.get("email", ""),
            "password": email_data.get("password", ""),
            "key": license_key,
            "category": category,
        }
        requests.post(
            f"{SUPABASE_URL}/rest/v1/mails",
            headers=SUPABASE_HEADERS,
            data=json.dumps(payload),
            timeout=10,
        )
        log.debug(f"Wasted email logged to mails table: {category}")
    except Exception as e:
        log.error(f"Failed to log wasted email: {e}")


def log_registered_email(email_data: dict, license_key: str):
    try:
        payload = {
            "email_data": json.dumps(email_data),
            "email": email_data.get("email", ""),
            "password": email_data.get("password", ""),
            "key": license_key,
            "category": "registered",
            "mail_type": email_data.get("mail_type", "zeus"),
        }
        requests.post(
            f"{SUPABASE_URL}/rest/v1/registered_emails",
            headers=SUPABASE_HEADERS,
            data=json.dumps(payload),
            timeout=10,
        )
        log.debug(f"Registered email logged")
    except Exception as e:
        log.error(f"Failed to log registered email: {e}")


def get_custom_mail_from_supabase(mail_type: str, license_key: str):
    try:
        url = f"{SUPABASE_URL}/rest/v1/custom_mails?select=*&mail_type=eq.{mail_type}&limit=1"
        resp = requests.get(url, headers=SUPABASE_HEADERS, timeout=10)
        if resp.status_code == 200 and resp.json():
            mail_data = resp.json()[0]
            delete_resp = requests.delete(
                f"{SUPABASE_URL}/rest/v1/custom_mails?id=eq.{mail_data['id']}",
                headers=SUPABASE_HEADERS,
                timeout=10,
            )
            if delete_resp.status_code in [200, 204]:
                log.info(f"Got custom mail: {mail_data.get('email', '')}")
                result = {
                    "email": mail_data.get("email", ""),
                    "password": mail_data.get("password", ""),
                    "mail_type": mail_type,
                    "imap_server": mail_data.get("imap_server"),
                    "imap_port": mail_data.get("imap_port"),
                }
                if mail_type == "graph":
                    result["token"] = mail_data.get("refresh_token", "")
                    result["uuid"] = mail_data.get("client_id", "")
                    if mail_data.get("email_data"):
                        try:
                            email_data_json = json.loads(mail_data["email_data"])
                            result["token"] = email_data_json.get(
                                "RefreshToken", result.get("token")
                            )
                            result["uuid"] = email_data_json.get(
                                "ClientId", result.get("uuid")
                            )
                        except:
                            pass
                return result
        return None
    except Exception as e:
        log.error(f"Failed to get custom mail: {e}")
        return None


def get_imap_settings():
    try:
        url = f"{SUPABASE_URL}/rest/v1/settings?select=*&key=eq.imap_server"
        resp = requests.get(url, headers=SUPABASE_HEADERS, timeout=10)
        imap_server = None
        imap_port = 993
        if resp.status_code == 200 and resp.json():
            imap_server = resp.json()[0].get("value")
        url = f"{SUPABASE_URL}/rest/v1/settings?select=*&key=eq.imap_port"
        resp = requests.get(url, headers=SUPABASE_HEADERS, timeout=10)
        if resp.status_code == 200 and resp.json():
            try:
                imap_port = int(resp.json()[0].get("value", 993))
            except:
                imap_port = 993
        return imap_server, imap_port
    except Exception as e:
        log.error(f"Failed to get IMAP settings: {e}")
        return None, 993


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


paassword = "$TermTUSiCE2169#"


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
            "password": paassword,
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


async def click_dropdown_option(tab, expected_text):
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
    result = await tab.evaluate(js)
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
    def __init__(self, proxy_data=None):
        self.session = tls_client.Session(
            client_identifier="chrome_120", random_tls_extension_order=True
        )
        self.proxy_data = proxy_data
        if proxy_data:
            tls_proxy_url = proxy_data[0]
            proxy_user = proxy_data[1]
            proxy_pass = proxy_data[2]
            self.session.proxies = {"http": tls_proxy_url, "https": tls_proxy_url}
            if proxy_user and proxy_pass:
                self.session.proxy_username = proxy_user
                self.session.proxy_password = proxy_pass

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
            if self.proxy_data:
                host = self.proxy_data[3]
                port = self.proxy_data[4]
                proxy_user = self.proxy_data[1]
                proxy_pass = self.proxy_data[2]
                if proxy_user and proxy_pass:
                    ws.connect(
                        "wss://gateway.discord.gg/?v=9&encoding=json",
                        http_proxy_host=host,
                        http_proxy_port=int(port),
                        proxy_type="http",
                        http_proxy_auth=(proxy_user, proxy_pass),
                    )
                else:
                    ws.connect(
                        "wss://gateway.discord.gg/?v=9&encoding=json",
                        http_proxy_host=host,
                        http_proxy_port=int(port),
                        proxy_type="http",
                    )
            else:
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

            threading.Thread(target=_heartbeat_loop, daemon=True).start()

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
                log.info(f"Profile update returned: {response.status_code}")
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
    mail_type = email_data.get("mail_type", "zeus")
    if mail_type == "custom_imap":
        return fetch_verification_url_imap(email_data, timeout)
    refresh_token = email_data.get("token", "")
    client_id = email_data.get("uuid", "") or MS_CLIENT_ID
    access_token = get_access_token(refresh_token, client_id)
    if not access_token:
        log.error(f"Graph API: failed to get access token (refresh_token present: {bool(refresh_token)}, client_id: {client_id[:8] if client_id else 'none'})")
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


def fetch_verification_url_imap(email_data: Dict, timeout: int = 120) -> Optional[str]:
    import imaplib
    import email as email_lib
    import ssl

    email_addr = email_data.get("email", "")
    password = email_data.get("password", "")
    imap_server = email_data.get("imap_server")
    imap_port = email_data.get("imap_port", 993)

    if not imap_server:
        imap_server, imap_port = get_imap_settings()

    if not imap_server:
        log.error("IMAP server not configured")
        return None

    start_time = time.time()

    while (time.time() - start_time) < timeout:
        try:
            context = ssl.create_default_context()
            mail = imaplib.IMAP4_SSL(imap_server, int(imap_port), ssl_context=context)
            mail.login(email_addr, password)
            mail.select("inbox")

            status, messages = mail.search(None, "FROM", "discord")
            if status != "OK":
                status, messages = mail.search(None, "ALL")

            message_ids = messages[0].split()

            for msg_id in reversed(message_ids[-10:]):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email_lib.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "").lower()

                if "verify" not in subject and "confirm" not in subject:
                    continue

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                continue
                            break
                        elif content_type == "text/plain" and not body:
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                continue
                else:
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        continue

                verify_pattern = r'https://discord\.com/verify\?token=[^"\'\>\s]+'
                match = re.search(verify_pattern, body)
                if match:
                    mail.logout()
                    return match.group(0)

                click_patterns = [
                    r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                    r'https://links\.discord\.com[^"\'\>\s]+',
                ]
                for pat in click_patterns:
                    for m in re.finditer(pat, body):
                        url = m.group(0)
                        try:
                            resp = requests.get(
                                url, allow_redirects=True, timeout=15, verify=False
                            )
                            final_url = resp.url
                            if "discord.com/verify" in final_url:
                                mail.logout()
                                return final_url
                            verify_in_body = re.search(
                                r'https://discord\.com/verify\?token=[^"\'\>\s]+',
                                resp.text,
                            )
                            if verify_in_body:
                                mail.logout()
                                return verify_in_body.group(0)
                        except:
                            pass

            mail.logout()
        except Exception as e:
            log.debug(f"IMAP error: {e}")

        time.sleep(3)

    return None


def gen_username():
    first_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn",
        "Blake", "Cameron", "Drew", "Hayden", "Jamie", "Kendall", "Logan", "Parker",
        "Sage", "Skylar", "Reese", "Phoenix", "River", "Rowan", "Dakota", "Emery",
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
        "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    ]
    tech_words = [
        "Tech", "Code", "Byte", "Pixel", "Data", "Neo", "Cyber", "Digital", "Virtual",
        "Alpha", "Beta", "Prime", "Core", "Edge", "Link", "Node", "Grid", "Wave",
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


async def safe_stop(driver):
    try:
        for _ in range(3):
            try:
                result = driver.stop()
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=5)
                break
            except asyncio.TimeoutError:
                continue
            except Exception:
                await asyncio.sleep(0.3)
    except Exception:
        pass
    await asyncio.sleep(0.5)


def get_token_via_login(email: str, password: str, proxy_data=None) -> Optional[str]:
    try:
        session = tls_client.Session(client_identifier="chrome_120")
        if proxy_data:
            tls_proxy_url = proxy_data[0]
            proxy_user = proxy_data[1]
            proxy_pass = proxy_data[2]
            proxy_host = proxy_data[3]
            proxy_port = proxy_data[4]
            session.proxies = {"http": tls_proxy_url, "https": tls_proxy_url}
            if proxy_user and proxy_pass:
                session.proxy_username = proxy_user
                session.proxy_password = proxy_pass
            log.info(f"Login request using proxy: {proxy_host}:{proxy_port}")
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
        try:
            resp_json = response.json()
            log.error(f"Login failed: {response.status_code} - {resp_json}")
        except:
            log.error(f"Login failed: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        log.error(f"Token fetch error: {e}")
        return None


def check_token_status(token: str, proxy_data=None) -> str:
    try:
        session = tls_client.Session(client_identifier="chrome_120")
        if proxy_data:
            tls_proxy_url = proxy_data[0]
            proxy_user = proxy_data[1]
            proxy_pass = proxy_data[2]
            session.proxies = {"http": tls_proxy_url, "https": tls_proxy_url}
            if proxy_user and proxy_pass:
                session.proxy_username = proxy_user
                session.proxy_password = proxy_pass
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


def humanize_account(token: str, proxy_data=None) -> bool:
    try:
        humanizer = DiscordHumanizer(proxy_data)

        avatar_b64 = None
        avatar_url = get_random_avatar_url()
        try:
            avatar_resp = None
            if proxy_data:
                tls_proxy_url = proxy_data[0]
                proxies = {"http": tls_proxy_url, "https": tls_proxy_url}
                avatar_resp = requests.get(avatar_url, timeout=10, proxies=proxies)
            else:
                avatar_resp = requests.get(avatar_url, timeout=10)
            if avatar_resp and avatar_resp.status_code == 200:
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


class ProxyManager:
    PROXY_USAGE_FILE = "proxy_usage.json"

    def __init__(self):
        self._current_proxy = None
        self._current_proxy_line = None
        self._max_usage = 2

    def _load_usage_data(self):
        try:
            with open(self.PROXY_USAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_usage_data(self, data):
        with open(self.PROXY_USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def parse_proxy(self, proxy_line):
        proxy_line = proxy_line.strip()
        if "@" in proxy_line:
            # Format: user:pass@host:port — use rfind so passwords with @ are handled
            at_idx = proxy_line.rfind("@")
            auth_part = proxy_line[:at_idx]
            host_part = proxy_line[at_idx + 1:]
            colon_idx = auth_part.find(":")
            if colon_idx == -1:
                log.warning(f"Invalid auth in proxy: {proxy_line} — skipping")
                return None
            username = auth_part[:colon_idx]
            password = auth_part[colon_idx + 1:]
            host_colon = host_part.rfind(":")
            if host_colon == -1:
                log.warning(f"Invalid host:port in proxy: {proxy_line} — skipping")
                return None
            host = host_part[:host_colon]
            port = host_part[host_colon + 1:]
            tls_proxy_url = f"http://{username}:{password}@{host}:{port}"
            browser_proxy_url = f"http://{host}:{port}"
            return tls_proxy_url, username, password, host, port, browser_proxy_url
        else:
            parts = proxy_line.split(":")
            if len(parts) == 2:
                host, port = parts
                return (
                    f"http://{host}:{port}",
                    None,
                    None,
                    host,
                    port,
                    f"http://{host}:{port}",
                )
            elif len(parts) == 4:
                host, port, username, password = parts
                return (
                    f"http://{username}:{password}@{host}:{port}",
                    username,
                    password,
                    host,
                    port,
                    f"http://{host}:{port}",
                )
            else:
                log.warning(f"Invalid proxy format: {proxy_line} — skipping")
                return None

    def get_proxy(self, file_path="proxies.txt"):
        with _proxy_lock:
            usage_data = self._load_usage_data()

            for proxy_line, count in list(usage_data.items()):
                if count < self._max_usage:
                    usage_data[proxy_line] = count + 1
                    self._save_usage_data(usage_data)
                    parsed = self.parse_proxy(proxy_line)
                    self._current_proxy = parsed
                    self._current_proxy_line = proxy_line
                    return parsed
                else:
                    del usage_data[proxy_line]

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    proxies = [p.strip() for p in f if p.strip()]
            except FileNotFoundError:
                log.warning("proxies.txt not found — running without proxy")
                return None

            if not proxies:
                log.warning("No proxies left — running without proxy")
                return None

            proxy_line = random.choice(proxies)
            proxies.remove(proxy_line)

            with open(file_path, "w", encoding="utf-8") as f:
                if proxies:
                    f.write("\n".join(proxies) + "\n")

            usage_data[proxy_line] = 1
            self._save_usage_data(usage_data)

            parsed = self.parse_proxy(proxy_line)
            self._current_proxy = parsed
            self._current_proxy_line = proxy_line

            return parsed

    def get_requests_proxy(self, proxy_data):
        proxy_url = proxy_data[0]
        return {"http": proxy_url, "https": proxy_url}


_proxy_manager = ProxyManager()


def get_session_proxy(file_path="proxies.txt"):
    return _proxy_manager.get_proxy(file_path)


async def register_and_get_promo(license_key, zeus_api_key, is_last_instance=False):
    temp_profile_dir = tempfile.mkdtemp(prefix="brave-profile-")
    driver = None
    proxy_data = None
    email_data = None
    try:
        import os
        import json

        proxy_data = get_session_proxy()
        if proxy_data:
            tls_proxy_url = proxy_data[0]
            proxy_user = proxy_data[1]
            proxy_pass = proxy_data[2]
            proxy_host = proxy_data[3]
            proxy_port = proxy_data[4]
            browser_proxy_url = proxy_data[5]
            log.info(f"Using proxy: {proxy_host}:{proxy_port} for this account")
        else:
            tls_proxy_url = proxy_user = proxy_pass = proxy_host = proxy_port = browser_proxy_url = None
            log.info("No proxy available — running without proxy")

        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        extension_path = os.path.join(base_path, "proxy_extension")
        proxy_config_path = os.path.join(extension_path, "proxy_config.json")
        with open(proxy_config_path, "w", encoding="utf-8") as f:
            json.dump({"username": proxy_user or "", "password": proxy_pass or ""}, f)

        default_path = os.path.join(temp_profile_dir, "Default")
        os.makedirs(default_path, exist_ok=True)

        prefs_path = os.path.join(default_path, "Preferences")

        prefs = {
            "credentials_enable_service": False,
            "profile": {"password_manager_enabled": False},
        }

        with open(prefs_path, "w", encoding="utf-8") as f:
            json.dump(prefs, f)

        browser_args = [
            "--start-maximized",
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
            "--webrtc-ip-handling-policy=disable_non_proxied_udp",
            "--disable-webrtc",
            "--disable-features=PasswordManager,PasswordManagerOnboarding,AutofillServerCommunication",
            "--disable-save-password-bubble",
            "--disable-password-generation",
            "--disable-password-manager-reauthentication",
            "--disable-credentials-service",
            "--disable-sync",
            "--disable-brave-extension",
            "--disable-features=BraveRewards,BraveWallet,BraveVPN,BraveNews,BraveTalk",
            "--brave-disable-native-brave-wallet",
            "--brave-disable-sync",
            "--disable-translate",
            "--disable-popup-blocking",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-component-extensions-with-background-pages",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-background-networking",
            "--metrics-recording-only",
            "--disable-domain-reliability",
            "--no-first-run",
            "--no-default-browser-check",
            f"--load-extension={extension_path}",
            "--disable-extensions-except=" + extension_path,
        ]

        if browser_proxy_url:
            browser_args.append(f"--proxy-server={browser_proxy_url}")

        driver = await uc.start(
            user_data_dir=temp_profile_dir,
            browser_executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            headless=False,
            browser_args=browser_args,
        )

        await asyncio.sleep(2)

        tab = await driver.get("https://discord.com/register")
    except RuntimeError as e:
        if "StopIteration" in str(e) or "coroutine raised StopIteration" in str(e):
            log.error(
                "Failed to get browser tab, browser may not have started properly"
            )
            if email_data:
                log_wasted_email(email_data, license_key, "browser_failed")
            if driver:
                try:
                    await safe_stop(driver)
                except Exception as stop_e:
                    log.error(f"Error during driver.stop(): {stop_e}")
            return
        else:
            raise

    log.info("Loaded Register Page")

    mail_type = fetch_mail_type()
    if not mail_type:
        log.error("Cannot proceed without mail type. Contact administrator")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        return

    if mail_type == "custom_graph":
        email_data = get_custom_mail_from_supabase("graph", license_key)
        if email_data:
            email_data["mail_type"] = "custom_graph"
    elif mail_type == "custom_imap":
        email_data = get_custom_mail_from_supabase("imap", license_key)
        if email_data:
            email_data["mail_type"] = "custom_imap"
    else:
        email_provider = EmailProvider(zeus_api_key, mail_type)
        email_data = email_provider.purchase()
        if email_data and email_data != "INSUFFICIENT_STOCK":
            email_data["mail_type"] = "zeus"

    if email_data == "INSUFFICIENT_STOCK":
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        sys.exit(1)

    if not email_data:
        log.error("Failed to get email")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        if not is_last_instance:
            rotate_ip(config.get("mode"))
        return

    email = email_data.get("email")
    password = email_data.get("password")

    if not email or not password:
        log.error(f"Invalid email payload received")
        if email_data:
            log_wasted_email(email_data, license_key, "invalid_payload")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        return

    log.info(f"Using email: {email}")

    username = get_random_username()
    global_name = get_random_nickname()

    log.info(f"Using username: {username}, global_name: {global_name}")

    discord_password = password

    for name, value in [
        ("email", email),
        ("global_name", global_name),
        ("username", username),
        ("password", discord_password),
    ]:
        field = await tab.wait_for(f'input[name="{name}"]', timeout=120_000)
        if not field:
            log.error(f"{name} input not found")
            return
        await field.send_keys(value)
        await asyncio.sleep(0.05)

    month = random.choice(months)
    day = str(random.randint(1, 28))
    year = str(random.randint(1995, 2005))

    for label, value in [("Month", month), ("Day", day), ("Year", year)]:
        dropdown = await tab.wait_for(
            f'div[role="button"][aria-label="{label}"]', timeout=30_000
        )
        if not dropdown:
            log.error(f"{label} dropdown not found")
            return
        await dropdown.click()
        await asyncio.sleep(0.1)
        if not await click_dropdown_option(tab, value):
            log.warning(f"Failed to select {label}={value}, retrying...")
            await asyncio.sleep(0.1)

    checkbox = await tab.query_selector('input[type="checkbox"]')
    if checkbox:
        await checkbox.click()
        await asyncio.sleep(0.05)

    submit_btn = await tab.query_selector('button[type="submit"]')
    if submit_btn:
        await submit_btn.click()
        log.success("Submitted Registration Form")
    else:
        log.error("Submit button not found")
        log_wasted_email(email_data, license_key, "submit_button_not_found")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        return

    log.warning("Please Solve Captcha Manually!")
    send_notification("Worker Gen", "Please solve the CAPTCHA!")

    for attempt in range(300):
        try:
            current_url = await tab.evaluate("window.location.href")
            if "discord.com/channels/@me" in current_url:
                log.success("Captcha successfully solved!")
                await asyncio.sleep(random.uniform(2.0, 4.0))
                break
        except Exception as e:
            log.error(f"Error while captcha verification: {e}")
        await asyncio.sleep(1)
    else:
        log.error("CAPTCHA not solved or redirect failed")
        log_wasted_email(email_data, license_key, "captcha_not_solved")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        return

    await asyncio.sleep(random.uniform(1.0, 2.0))
    log.info(f"Waiting for verification email (mail_type={email_data.get('mail_type', 'unknown')}, email={email})...")
    verify_url = fetch_verification_url(email_data, timeout=120)

    if verify_url:
        log.success("Email Verification link fetched!")
        await tab.evaluate(f'''
            (() => {{
                window.open("{verify_url}", "_blank");
                return "ok";
            }})()
        ''')
    else:
        log.error(f"Could not find verification link in email after 120s (mail_type={email_data.get('mail_type', 'unknown')})")
        log_wasted_email(email_data, license_key, "verification_link_not_found")
        if driver:
            try:
                await safe_stop(driver)
            except Exception as stop_e:
                log.error(f"Error during driver.stop(): {stop_e}")
        return

    tabs = driver.tabs
    verify_tab = tabs[-1]

    for attempt in range(60):
        try:
            result = await verify_tab.evaluate("""
                (function() {
                    try {
                        return document.body?.innerText || "NO_TEXT_FOUND";
                    } catch(e) {
                        return "NO_TEXT_FOUND";
                    }
                })()
            """)
            page_text = ""
            if result is None:
                page_text = ""
            elif hasattr(result, "exceptionDetails"):
                page_text = ""
            elif isinstance(result, str):
                page_text = result
            elif isinstance(result, dict):
                if "exceptionDetails" in result:
                    page_text = ""
                elif "result" in result:
                    inner = result["result"]
                    if isinstance(inner, dict):
                        if "exceptionDetails" in inner:
                            page_text = ""
                        elif "value" in inner:
                            page_text = inner["value"] or ""
                    elif isinstance(inner, str):
                        page_text = inner
                elif "value" in result:
                    page_text = result["value"] or ""
            else:
                page_text = str(result)
            if "email verified" in page_text.lower():
                log.success("Email verified successfully!")
                log.success("Account verified successfully!")

                token = None
                for idx, t in enumerate(driver.tabs):
                    try:
                        url = await t.evaluate("window.location.href")
                        url_str = ""
                        if isinstance(url, str):
                            url_str = url
                        elif isinstance(url, dict):
                            if "result" in url:
                                inner = url["result"]
                                if isinstance(inner, dict) and "value" in inner:
                                    url_str = inner["value"]
                                elif isinstance(inner, str):
                                    url_str = inner
                            elif "value" in url:
                                url_str = url["value"]
                        if "discord.com/channels" not in url_str.lower():
                            continue
                        local_storage = await t.get_local_storage()
                        if local_storage and "token" in local_storage:
                            token = (
                                local_storage["token"].replace('"', "").replace("'", "")
                            )
                            log.success(
                                f"Token extracted from browser: {token[:25]}***"
                            )
                            break
                    except Exception as te:
                        log.debug(f"Token extraction error on tab {idx}: {te}")

                if driver:
                    try:
                        await safe_stop(driver)
                    except Exception as stop_e:
                        log.error(f"Error during driver.stop(): {stop_e}")
                driver = None

                await asyncio.sleep(random.uniform(1.5, 3.0))

                if not token:
                    log.error("Failed to extract token from browser")
                    log_wasted_email(email_data, license_key, "registered_but_no_token")
                    no_token_line = f"{email}:{discord_password}"
                    log_ev_to_supabase(no_token_line, license_key, "no_token")
                    cooldown = config.get("after_create_timer", 30)
                    log.info(f"Waiting {cooldown} seconds before next account...")
                    countdown_timer(cooldown)
                    return

                log.info(
                    f"Validating token with proxy: {proxy_host}:{proxy_port}" if proxy_host else "Validating token (no proxy)"
                )
                session = tls_client.Session(client_identifier="chrome_120")
                if proxy_data:
                    session.proxies = {"http": tls_proxy_url, "https": tls_proxy_url}
                    if proxy_user and proxy_pass:
                        session.proxy_username = proxy_user
                        session.proxy_password = proxy_pass

                headers = {
                    "Authorization": token,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
                validate_resp = session.get(
                    "https://discord.com/api/v9/users/@me", headers=headers
                )

                if validate_resp.status_code == 200:
                    user_data = validate_resp.json()
                    log.success(
                        f"Token validated for user: {user_data.get('username', 'unknown')}"
                    )
                    status = "valid"
                elif validate_resp.status_code == 401:
                    status = "invalid"
                    log.warning("Token is invalid")
                elif validate_resp.status_code in [403, 423]:
                    status = "locked"
                    log.warning("Account is locked")
                else:
                    status = "unknown"
                    log.warning(f"Unknown status: {validate_resp.status_code}")

                if status == "valid":
                    ev_line = f"{email}:{discord_password}:{token}"
                    log_registered_email(email_data, license_key)
                    log.info(
                        f"Humanizing account with proxy: {proxy_host}:{proxy_port}" if proxy_host else "Humanizing account (no proxy)"
                    )
                    humanizer = DiscordHumanizer(proxy_data)
                    avatar_b64 = None
                    avatar_url = get_random_avatar_url()
                    try:
                        if proxy_data:
                            avatar_resp = requests.get(
                                avatar_url,
                                timeout=10,
                                proxies={"http": tls_proxy_url, "https": tls_proxy_url},
                            )
                        else:
                            avatar_resp = requests.get(avatar_url, timeout=10)
                        if avatar_resp.status_code == 200:
                            avatar_b64 = base64.b64encode(avatar_resp.content).decode()
                    except:
                        pass
                    pronouns = get_random_pronouns()
                    bio = get_random_bio()
                    humanizer.humanize(token, avatar_b64, pronouns, bio)
                    log_ev_to_supabase(ev_line, license_key, "evs")
                    log.success("Account Created Successfully")
                elif status == "invalid":
                    ev_line = f"{email}:{discord_password}:{token}"
                    log_ev_to_supabase(ev_line, license_key, "invalid")
                    log_wasted_email(email_data, license_key, "token_invalid")
                    log.warning("Token is invalid — logged to invalid table")
                elif status == "locked":
                    ev_line = f"{email}:{discord_password}:{token}"
                    log_ev_to_supabase(ev_line, license_key, "locked")
                    log_wasted_email(email_data, license_key, "account_locked")
                    log.warning("Account is locked — logged to locked table")

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
    log_wasted_email(email_data, license_key, "email_verification_timeout")
    if driver:
        try:
            await safe_stop(driver)
        except Exception as stop_e:
            log.error(f"Error during driver.stop(): {stop_e}")

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


def get_wasted_emails(category: str = None, limit: int = 50):
    try:
        url = (
            f"{SUPABASE_URL}/rest/v1/mails?select=*&order=created_at.desc&limit={limit}"
        )
        if category:
            url += f"&category=eq.{category}"
        resp = requests.get(url, headers=SUPABASE_HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        log.error(f"Failed to fetch wasted emails: {e}")
        return []


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