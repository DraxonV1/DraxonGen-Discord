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
from datetime import datetime
import shutil
import tempfile
import urllib3
from typing import Optional, Dict
import re
import subprocess
import warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
init(autoreset=True)

with open('config.json', 'r') as f:
    config = json.load(f)

RESET = "\033[0m"
ANSI_PATTERN = re.compile(r'\033\[[0-9;]*m')

def write_print(text, interval=0.01, hide_cursor=True, end=RESET):
    if hide_cursor:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    i = 0
    while i < len(text):
        if text[i] == '\033':  
            match = ANSI_PATTERN.match(text, i)
            if match:
                sys.stdout.write(match.group())  
                sys.stdout.flush()
                i = match.end()
                continue
        sys.stdout.write(text[i])
        sys.stdout.flush()
        time.sleep(interval)
        i += 1
    sys.stdout.write(end)
    sys.stdout.flush()
    if hide_cursor:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


# --- LOGGER CODE ---
import threading
class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class Console:
    def __init__(self, log_to_file: bool = False, log_file: str = "discord_creator.log", 
                 log_level: LogLevel = LogLevel.INFO, max_file_size: int = 10 * 1024 * 1024) -> None:
        init(autoreset=True)
        self.print_lock = threading.Lock()
        self.log_to_file = log_to_file
        self.log_file = log_file
        self.log_level = log_level
        self.max_file_size = max_file_size
        if self.log_to_file:
            self._setup_file_logging()
        self.colors = {
            "green": Fore.GREEN,
            "red": Fore.RED,
            "yellow": Fore.YELLOW,
            "blue": Fore.BLUE,
            "magenta": Fore.MAGENTA,
            "cyan": Fore.CYAN,
            "white": Fore.WHITE,
            "black": Fore.BLACK,
            "reset": Style.RESET_ALL,
            "lightblack": Fore.LIGHTBLACK_EX,
            "lightred": Fore.LIGHTRED_EX,
            "lightgreen": Fore.LIGHTGREEN_EX,
            "lightyellow": Fore.LIGHTYELLOW_EX,
            "lightblue": Fore.LIGHTBLUE_EX,
            "lightmagenta": Fore.LIGHTMAGENTA_EX,
            "lightcyan": Fore.LIGHTCYAN_EX,
            "lightwhite": Fore.LIGHTWHITE_EX
        }
        self.level_width = 8
        self.level_colors = {
            LogLevel.DEBUG: self.colors["lightblack"],
            LogLevel.INFO: self.colors["lightblue"],
            LogLevel.WARNING: self.colors["lightyellow"],
            LogLevel.ERROR: self.colors["lightred"],
            LogLevel.CRITICAL: self.colors["red"]
        }
    def _setup_file_logging(self):
        try:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > self.max_file_size:
                os.rename(self.log_file, self.log_file + ".old")
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
            self.log_to_file = False
    def _write_to_file(self, level: str, message: str, obj: str = ""):
        if not self.log_to_file:
            return
        try:
            timestamp = self.timestamp()
            log_entry = f"[{timestamp}] [{level}] {message}"
            if obj:
                log_entry += f" | {obj}"
            log_entry += "\n"
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass
    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")
    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")
    def _format_box(self, lines, color=Fore.LIGHTBLACK_EX):
        width = max(len(self._strip_ansi(line)) for line in lines)
        top = f"{color}┌{'─' * (width + 2)}┐{Style.RESET_ALL}"
        bottom = f"{color}└{'─' * (width + 2)}┘{Style.RESET_ALL}"
        boxed = [top]
        for line in lines:
            boxed.append(f"{color}│{Style.RESET_ALL} {line.ljust(width)} {color}│{Style.RESET_ALL}")
        boxed.append(bottom)
        return "\n".join(boxed)
    def _strip_ansi(self, s):
        return re.sub(r'\x1b\[[0-9;]*m', '', s)
    def _print(self, msg, box=False):
        if box:
            lines = msg.splitlines()
            print(self._format_box(lines))
        else:
            print(msg)
    def _format_multiline(self, msg, indent="    "):
        lines = msg.splitlines()
        if len(lines) <= 1:
            return msg
        return lines[0] + "\n" + "\n".join(indent + l for l in lines[1:])
    def _should_log(self, level: LogLevel) -> bool:
        return level.value >= self.log_level.value
    def _log(self, level: LogLevel, message: str, obj: str = "", box: bool = False):
        if not self._should_log(level):
            return
        with self.print_lock:
            level_str = f"{level.name.upper():<{self.level_width}}"
            color = self.level_colors.get(level, self.colors["white"])
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{color}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file(level.name, message, obj)
    def header(self, text: str, box: bool = True):
        with self.print_lock:
            msg = f"{self.colors['lightmagenta']}{Style.BRIGHT}{text.center(60)}{self.colors['reset']}"
            self._print(msg, box=box)
            if self.log_to_file:
                self._write_to_file("HEADER", text)
    def debug(self, message: str, obj: str = "", box: bool = False):
        self._log(LogLevel.DEBUG, message, obj, box)
    def info(self, message: str, obj: str = "", box: bool = False):
        self._log(LogLevel.INFO, message, obj, box)
    def warning(self, message: str, obj: str = "", box: bool = False):
        self._log(LogLevel.WARNING, message, obj, box)
    def error(self, message: str, obj: str = "", box: bool = False):
        self._log(LogLevel.ERROR, message, obj, box)
    def critical(self, message: str, obj: str = "", box: bool = False):
        self._log(LogLevel.CRITICAL, message, obj, box)
    def success(self, message: str, obj: str = "", box: bool = False):
        with self.print_lock:
            level_str = f"{'SUCCESS':<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightgreen']}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file("SUCCESS", message, obj)
    def failure(self, message: str, obj: str = "", box: bool = False):
        with self.print_lock:
            level_str = f"{'FAILURE':<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightred']}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file("FAILURE", message, obj)
    def regened(self, message: str, obj: str = "", box: bool = False):
        with self.print_lock:
            level_str = f"{'REGENED':<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightblue']}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file("REGENED", message, obj)
    def revoked(self, message: str, obj: str = "", box: bool = False):
        with self.print_lock:
            level_str = f"{'REVOKED':<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightgreen']}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file("REVOKED", message, obj)
    def custom(self, message: str, obj: str, color: str, box: bool = False):
        color_key = color.lower()
        color_val = self.colors.get(color_key, Fore.WHITE)
        with self.print_lock:
            level_str = f"{color.upper():<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{color_val}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}"
            )
            if obj:
                msg += f" | {obj}"
            self._print(msg, box=box)
            self._write_to_file(color.upper(), message, obj)
    def input(self, message: str, box: bool = False):
        with self.print_lock:
            level_str = f"{'INPUT':<{self.level_width}}"
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightcyan']}{level_str}{self.colors['reset']} │ "
                f"{self.colors['white']}{self._format_multiline(message)}{self.colors['reset']}"
            )
            if box:
                print(self._format_box([msg]))
            else:
                print(msg)
            return input("")
    def progress(self, current: int, total: int, message: str = "Progress", bar_length: int = 30):
        with self.print_lock:
            progress = current / total
            filled_length = int(bar_length * progress)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            percentage = progress * 100
            msg = (
                f"{self.colors['lightblack']}{self.timestamp()} │ "
                f"{Style.BRIGHT}{self.colors['lightcyan']}{'PROGRESS':<{self.level_width}}{self.colors['reset']} │ "
                f"{self.colors['white']}{message}: [{bar}] {percentage:.1f}% ({current}/{total})"
            )
            print(f"\r{msg}", end='', flush=True)
            if current == total:
                print()
    def set_log_level(self, level: LogLevel):
        self.log_level = level
    def get_log_file_path(self) -> str:
        return os.path.abspath(self.log_file)
    def clear_log_file(self):
        if self.log_to_file and os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("")

# Create a global logger instance
log = Console(log_to_file=False, log_level=LogLevel.DEBUG)
# --- END LOGGER CODE ---

def generate_random_name():
    return ''.join(random.choices(string.ascii_letters, k=8))

def generate_random_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=14))

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
        mailbaba = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        email = mailbaba + "@gmail.com"
        nam = generate_random_name()
        data = {
            'email': email,
            'password': paassword,
            'date_of_birth': "2000-09-20",
            'username': email,
            'global_name': nam,
            'consent': True,
            'captcha_service': 'hcaptcha',
            'captcha_key': None,
            'invite': None,
            'promotional_email_opt_in': False,
            'gift_code_sku_id': None
        }
        req = requests.post('https://discord.com/api/v9/auth/register', json=data, headers=headers)
        try:
            resp_data = req.json()
        except Exception as je:
            return 1
        if req.status_code == 429 or 'retry_after' in resp_data:
            limit = resp_data.get('retry_after', 1)
            return int(float(limit)) + 1 if limit else 1
        else:
            return 1
    except Exception as e:
        log.failure(f"❌ Account ratelimit crashed: {e}")
        return 1
    
def countdown_timer(duration):
    for i in range(duration):
        msg = f"[{i+1:02d}/{duration}] Waiting before generating next token..."
        print(f"\r{msg}", end='', flush=True)
        time.sleep(1)
    print()  # Move to next line after countdown

def close_brave(profile_dir):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info.get('name')
            cmdline = proc.info.get('cmdline')

            if not name or not cmdline:
                continue   # skip broken processes

            if 'brave' in name.lower():
                cmd = ' '.join(cmdline).lower()
                if profile_dir.lower() in cmd:
                    proc.kill()

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, TypeError):
            continue
    shutil.rmtree(profile_dir, ignore_errors=True)

months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
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
        notification.application_name = "Aizenking17"
        notification.title = title
        notification.message = message
        icon_path = config.get("notification_icon")
        if icon_path and os.path.isfile(icon_path):
            notification.icon = icon_path  
        notification.send()
    except Exception as e:
        log.error(f"❌ Notification error: {e}")

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
            if resp.status_code == 200:
                data = resp.json()
                if data.get("Code") == 0 and "Data" in data and "Accounts" in data["Data"]:
                    accounts = data["Data"]["Accounts"]
                    if accounts:
                        account = accounts[0]
                        return {
                            "email": account.get("Email", ""),
                            "password": account.get("Password", ""),
                            "token": account.get("RefreshToken", ""),
                            "uuid": account.get("ClientId", "") if account.get("ClientId") else ""
                        }
        except Exception as e:
            pass
        return None
    def purchase(self) -> Optional[Dict]:
        start_time = time.time()
        timeout = 20
        while (time.time() - start_time) < timeout:
            account = self._fetch_email()
            if account:
                return account
            time.sleep(1)
        return None
    
MS_CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"

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
                "scope": "https://graph.microsoft.com/.default"
            },
            timeout=30,
            verify=False
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
                    "$select": "subject,body,from,bodyPreview,receivedDateTime"
                },
                timeout=15
            )
            emails = response.json().get("value", [])
            if attempt % 3 == 0:
                elapsed = int(time.time() - start_time)
            for email in emails:
                subject = email.get("subject", "").lower()
                from_addr = email.get("from", {}).get("emailAddress", {}).get("address", "").lower()
                is_verify_email = (
                    ("verify" in subject or "confirm" in subject or "email" in subject) and
                    ("discord" in from_addr or "noreply@discord.com" in from_addr)
                )
                if not is_verify_email:
                    continue
                body_html = email.get("body", {}).get("content", "")
                verify_pattern = r'https://discord\.com/verify\?token=[^"\'\>\s]+'
                direct_match = re.search(verify_pattern, body_html)
                if direct_match:
                    return direct_match.group(0)
                click_patterns = [
                    r'https://click\.discord\.com/ls/click\?[^"\'\>\s]+',
                    r'https://links\.discord\.com[^"\'\>\s]+'
                ]
                for pat in click_patterns:
                    for m in re.finditer(pat, body_html):
                        url = m.group(0)
                        try:
                            resp = requests.get(url, allow_redirects=True, timeout=15, verify=False)
                            final_url = resp.url
                            if "discord.com/verify" in final_url:
                                return final_url
                            verify_in_body = re.search(r'https://discord\.com/verify\?token=[^"\'\>\s]+', resp.text)
                            if verify_in_body:
                                return verify_in_body.group(0)
                        except:
                            pass     
        except Exception as e:
            log.error(f"❌ Graph API error: {e}.")
        time.sleep(1)
    return None

def gen_username():
    first_names = ["Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn", "Blake", "Cameron", "Drew", "Hayden", "Jamie", "Kendall", "Logan", "Parker", "Sage", "Skylar", "Reese", "Phoenix", "River", "Rowan", "Dakota", "Emery"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"]
    tech_words = ["Tech", "Code", "Byte", "Pixel", "Data", "Neo", "Cyber", "Digital", "Virtual", "Alpha", "Beta", "Prime", "Core", "Edge", "Link", "Node", "Grid", "Wave"]
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
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        return '\tdevice' in result.stdout
    except:
        return False
    
def rotate_ip(mode):
    global adb_failed
    if mode == 'adb':
        if adb_failed:
            if check_adb_available():
                adb_failed = False
            else:
                cooldown = account_ratelimit()
                log.warning(f"⚠️ Rate limited — waiting {cooldown} seconds...")
                return
        try:
            subprocess.run(['adb', 'shell', 'cmd', 'connectivity', 'airplane-mode', 'enable'],
                         check=True, capture_output=True)
            time.sleep(1)
            subprocess.run(['adb', 'shell', 'cmd', 'connectivity', 'airplane-mode', 'disable'],
                         check=True, capture_output=True)
            time.sleep(4)
            log.success('🎉 IP Rotated via ADB.')
            time.sleep(3)
        except Exception as e:
            adb_failed = True
            cooldown = account_ratelimit()
            log.warning(f"⚠️ Rate limited — waiting {cooldown} seconds...")
            countdown_timer(cooldown)
    elif mode == 'vpn':
        cooldown = config.get('timer')
        log.info(f'🌐 VPN Mode Waiting {cooldown}s for user IP change.')
        countdown_timer(cooldown)
    else:
        cooldown = account_ratelimit()
        log.warning(f"⚠️ Rate limited — waiting {cooldown} seconds...")
        countdown_timer(cooldown)

async def register_and_get_promo(is_last_instance=False):
    temp_profile_dir = tempfile.mkdtemp(prefix="brave-profile-")
    driver = None
    try:
        driver = await uc.start(options={"user_data_dir": temp_profile_dir}, browser_executable_path=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
        await asyncio.sleep(2)  # Wait for browser to fully initialize
        tab = await driver.get("https://discord.com/register")
    except RuntimeError as e:
        if "StopIteration" in str(e) or "coroutine raised StopIteration" in str(e):
            log.error("❌ Failed to get browser tab, browser may not have started properly.")
            if driver:
                try:
                    await driver.stop()
                except Exception as stop_e:
                    log.error(f"❌ Error during driver.stop(): {stop_e}")
            return
        else:
            raise
    log.info("🕒 Loaded Register Page")
    


    api_key = config.get("zues_key")
    mail_type = config.get("mail_type")
    email_provider = EmailProvider(api_key, mail_type)
    email_data = email_provider.purchase()

    if not email_data:
        log.error("❌ Failed to purchase email (email_data is None). Check Zeus API / balance / mail_type.")
        if driver:
            try:
                await driver.stop()
            except Exception as stop_e:
                log.error(f"❌ Error during driver.stop(): {stop_e}")
        if not is_last_instance:
            rotate_ip(config.get("mode"))
        return  # 🔥 THIS IS CRITICAL

    email = email_data.get("email")
    password = email_data.get("password")
    refresh_token = email_data.get("token")
    client_id = email_data.get("uuid")

    if email and password:
        try:
            with open("ids.txt", "a") as f:
                f.write(f"{email}:{password}:{refresh_token}:{client_id}\n")
            log.info(f"💾 Saved account details to ids.txt")
        except Exception as e:
            log.error(f"❌ Failed to save account details: {e}")

    if not email or not password:
        log.error(f"❌ Invalid email payload received: {email_data}")
        if driver:
            try:
                await driver.stop()
            except Exception as stop_e:
                log.error(f"❌ Error during driver.stop(): {stop_e}")
        return

    log.info(f"✉️ Using {email}")
    username, global_name = gen_username()
    discord_password = generate_random_password()
    for name, value in [('email', email), ('global_name', global_name), ('username', username), ('password', discord_password)]:
        field = await tab.wait_for(f'input[name="{name}"]', timeout=120_000)
        if not field:
            log.error(f"❌ {name} input not found.")
            return
        await field.send_keys(value)
        await asyncio.sleep(0.05)
    month = random.choice(months)
    day = str(random.randint(1,28))
    year = str(random.randint(1995,2005))
    for label, value in [('Month', month), ('Day', day), ('Year', year)]:
        dropdown = await tab.wait_for(f'div[role="button"][aria-label="{label}"]', timeout=30_000)
        if not dropdown:
            log.error(f"❌ {label} dropdown not found.")
            return
        await dropdown.click()
        await asyncio.sleep(0.1)
        if not await click_dropdown_option(tab, value):
            log.warning(f"⚠️ Failed to select {label}={value}, retrying...")
            await asyncio.sleep(0.1)
    checkbox = await tab.query_selector('input[type="checkbox"]')
    if checkbox: await checkbox.click(); await asyncio.sleep(0.05)
    submit_btn = await tab.query_selector('button[type="submit"]')
    if submit_btn:
        await submit_btn.click()
        log.info("✅ Submitted Registration Form")
    else:
        log.error("❌ Submit button not found.")
        if driver:
            try:
                await driver.stop()
            except Exception as stop_e:
                log.error(f"❌ Error during driver.stop(): {stop_e}")
        return
    log.warning(f"⚠️ Please Solve Captcha Manually!")
    send_notification("Ultimate", "⚠️ Please solve the CAPTCHA!")
    for attempt in range(300): 
        try:
            current_url = await tab.evaluate("window.location.href")
            if "discord.com/channels/@me" in current_url:
                log.success("🎉 Captcha sucessfully solved by the user!")
                break
        except Exception as e:
            log.error(f"❌ Error while captcha verification - {e}")
        await asyncio.sleep(1)
    else:
        log.error("❌ CAPTCHA not solved or redirect failed.")
        if driver:
            try:
                await driver.stop()
            except Exception as stop_e:
                log.error(f"❌ Error during driver.stop(): {stop_e}")
        return
    verify_url = fetch_verification_url(email_data, timeout=120)
    log.info("✅ Email Verification link fetched!")
    if verify_url:
        await tab.evaluate(f'''
    (() => {{
        window.open("{verify_url}", "_blank");
        return "ok";
    }})()
''')
    else:
        log.error("❌ Could not find verification link in email.")
        if driver:
            try:
                await driver.stop()
            except Exception as stop_e:
                log.error(f"❌ Error during driver.stop(): {stop_e}")
        return
    tabs = driver.tabs
    verify_tab = tabs[-1]

    for attempt in range(60):
        try:
            page_text = await verify_tab.evaluate("""
                (() => {
                    return document.body?.innerText || "NO_TEXT_FOUND";
                })()
            """)
            if "email verified" in page_text.lower():
                log.success(f"🎉 Email verified successfully!")
                log.success("🎉 Account verified successfully")
                # Fetch and save token from localStorage after email verification
                await fetch_and_save_localstorage_token(verify_tab, email, password)
                # 🕒 TIMER AFTER ACCOUNT CREATION
                cooldown = config.get("after_create_timer", 30)
                log.info(f"⏳ Waiting {cooldown} seconds before next account...")
                countdown_timer(cooldown)
                if driver:
                    try:
                        await driver.stop()
                    except Exception as stop_e:
                        log.error(f"❌ Error during driver.stop(): {stop_e}")
                return  # 🔥 EXIT FUNCTION CLEANLY
        except Exception as e:
            log.error(f"❌ Error getting token: {e}")
            if "Target closed" in str(e) or "Session closed" in str(e):
                break
            log.error(f"❌ Eval failed: {e}")
        await asyncio.sleep(1)

    log.error("❌ Email verification not detected in time.")
    if driver:
        try:
            await driver.stop()
        except Exception as stop_e:
            log.error(f"❌ Error during driver.stop(): {stop_e}")
    if not is_last_instance:
        mode = config.get("mode")
        rotate_ip(mode)

banner = '''

   ___                        ______                   
 .'   `.                    .' ___  |                  
/  .-.  \ __   _   _ .--.  / .'   \_|  .---.  _ .--.   
| |   | |[  | | | [ `/'`\] | |   ____ / /__\\[ `.-. |  
\  `-'  / | \_/ |, | |     \ `.___]  || \__., | | | |  
 `.___.'  '.__.'_/[___]     `._____.'  '.__.'[___||__] 
                                                       
                                                  
'''
def print_gradient_text(text, start_color=(137, 207, 240), end_color=(25, 25, 112)):
    lines = text.split('\n')
    total_lines = len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            print(line)
            continue
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / total_lines)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / total_lines)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / total_lines)
        color_code = f"\033[38;2;{r};{g};{b}m"
        print(f"{color_code}{line}{Style.RESET_ALL}")            
cret = f'''[+] Creator - Aizenking17'''

def check_zeus_balance(api_key: str) -> Optional[float]:
    """
    Fictional / utility balance checker for Zeus-X.
    Safe for unattended execution.
    """

    url = "https://api.zeus-x.ru/balance"
    params = {"apikey": api_key}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()

        data = resp.json()

        # Expected format (fictional but realistic):
        # { "Code": 0, "Balance": 12.34 }

        if not isinstance(data, dict):
            log.error("❌ Zeus balance response malformed")
            return None

        if data.get("Code") != 0:
            log.error(f"❌ Zeus API error: {data}")
            return None

        balance = data.get("Balance")
        if balance is None:
            log.error("❌ Zeus balance missing in response")
            return None

        log.success(f"💰 Zeus Balance: {balance}")
        return float(balance)

    except requests.exceptions.Timeout:
        log.error("❌ Zeus balance request timed out")
    except requests.exceptions.HTTPError as e:
        log.error(f"❌ Zeus balance HTTP error: {e}")
    except ValueError:
        log.error("❌ Zeus balance JSON parse failed")
    except Exception as e:
        log.error(f"❌ Zeus balance unexpected error: {e}")

    return None


def run_register_and_get_promo(is_last_instance=False):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(register_and_get_promo(is_last_instance))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

def main():
    api_key = config.get("zues_key")

    balance = check_zeus_balance(api_key)
    if balance is None or balance <= 0:
        log.error("❌ Insufficient Zeus balance. Stopping run.")
    


    multiprocessing.freeze_support()
    try:
        instance_count = 1
    except ValueError:
        log.warning("⚠️ Invalid input. Defaulting to 1.")
        instance_count = 1
    try:
        log.debug("Number of accounts to generate (0 = infinite): ")
        max_runs = int(input())
    except ValueError:
        log.warning("⚠️ Invalid input. Defaulting to 1 account.")
        max_runs = 1
    run_count = 0
    active_processes = []
    while True:
        active_processes = [p for p in active_processes if p.is_alive()]
        if len(active_processes) < instance_count and (max_runs == 0 or run_count < max_runs):
            run_count += 1
            log.info(f"🚀 Starting account #{run_count}")
            try:
                is_last = (max_runs != 0 and run_count == max_runs)
                p = multiprocessing.Process(target=run_register_and_get_promo, args=(is_last,))
                p.start()
                active_processes.append(p)
            except Exception as e:
                log.failure(f"❌ Failed to launch process: {e}")
        if max_runs and run_count >= max_runs and not active_processes:
            break
        time.sleep(1)
    for p in active_processes:
        p.join(timeout=300)
    log.success("🎉 All account generations completed!")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("\n")
    print_gradient_text(Center.XCenter(banner))
    print_gradient_text(Center.XCenter(cret))
    print("\n")
    main()

# Example: Fetch 'token' from localStorage and save to tokens.txt
async def fetch_and_save_localstorage_token(tab, email=None, password=None):
    js_code = """
    let token = null;
    window.webpackChunkdiscord_app.push([[Symbol()], {}, o => {
      for (let e of Object.values(o.c)) {
        try {
          if (!e.exports || e.exports === window) continue;
          if (e.exports?.getToken) {
            token = e.exports.getToken();
          }
          for (let o in e.exports) {
            if (e.exports?.[o]?.getToken && \"IntlMessagesProxy\" !== e.exports[o][Symbol.toStringTag]) {
              token = e.exports[o].getToken();
            }
          }
        } catch {}
      }
    }]);
    window.webpackChunkdiscord_app.pop();
    token;
    """
    try:
        token = await tab.evaluate(js_code)
        if isinstance(token, Exception):
            log.error(f"Error fetching token: {token}")
            return
        if token is not None and email and password:
            with open("tokens.txt", "a") as f:
                f.write(f"{email}:{password}:{token}\n")
            log.success("Token saved to tokens.txt in mail:pass:token format")
        else:
            log.warning("No token found or missing email/password.")
    except Exception as e:
        log.error(f"Exception occurred while fetching token: {e}")