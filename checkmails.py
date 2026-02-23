import requests
import json
import urllib3
import warnings
from datetime import datetime
from typing import Optional
import easygradients as eg
import threading
from colorama import init

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

MS_CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"

print_lock = threading.Lock()


def ts():
    return datetime.now().strftime("%H:%M:%S")


def log_ok(msg):
    with print_lock:
        print(f"{eg.color(f'[{ts()}]', '#9D26FF')} {eg.color('[+]', '#00FF88')} {eg.color(msg, '#FFFFFF')}")


def log_err(msg):
    with print_lock:
        print(f"{eg.color(f'[{ts()}]', '#9D26FF')} {eg.color('[✗]', '#FF3366')} {eg.color(msg, '#FFFFFF')}")


def log_info(msg):
    with print_lock:
        print(f"{eg.color(f'[{ts()}]', '#9D26FF')} {eg.color('[!]', '#00D9FF')} {eg.color(msg, '#FFFFFF')}")


def log_warn(msg):
    with print_lock:
        print(f"{eg.color(f'[{ts()}]', '#9D26FF')} {eg.color('[⚠]', '#FFD700')} {eg.color(msg, '#FFFFFF')}")


def fetch_custom_mails(mail_type: str = "graph") -> list:
    try:
        url = f"{SUPABASE_URL}/rest/v1/custom_mails?select=*&mail_type=eq.{mail_type}&order=created_at.asc"
        resp = requests.get(url, headers=SUPABASE_HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        log_err(f"Failed to fetch mails: {resp.status_code} {resp.text}")
        return []
    except Exception as e:
        log_err(f"Supabase fetch error: {e}")
        return []


def delete_mail_from_db(mail_id: int):
    try:
        url = f"{SUPABASE_URL}/rest/v1/custom_mails?id=eq.{mail_id}"
        resp = requests.delete(url, headers=SUPABASE_HEADERS, timeout=10)
        return resp.status_code in [200, 204]
    except Exception as e:
        log_err(f"Delete error for id={mail_id}: {e}")
        return False


def get_access_token(refresh_token: str, client_id: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (access_token, error_description)"""
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
        token = result.get("access_token")
        error_desc = result.get("error_description") or result.get("error")
        return token, error_desc
    except Exception as e:
        return None, str(e)


def check_mail(mail_data: dict, auto_delete: bool) -> dict:
    mail_id = mail_data.get("id")
    email = mail_data.get("email", "unknown")
    mail_type = mail_data.get("mail_type", "graph")

    # Extract refresh token and client_id from email_data JSON or direct columns
    refresh_token = mail_data.get("refresh_token", "")
    client_id = mail_data.get("client_id", "") or MS_CLIENT_ID

    raw_email_data = mail_data.get("email_data")
    if raw_email_data:
        try:
            parsed = json.loads(raw_email_data)
            refresh_token = parsed.get("RefreshToken", refresh_token)
            client_id = parsed.get("ClientId", client_id) or MS_CLIENT_ID
        except Exception:
            pass

    if not refresh_token:
        log_warn(f"[{email}] No refresh token found — skipping")
        return {"email": email, "status": "no_token", "id": mail_id}

    access_token, error = get_access_token(refresh_token, client_id)

    if access_token:
        log_ok(f"[ALIVE] {email} (client_id: {(client_id or '')[:8]}...)")
        return {"email": email, "status": "alive", "id": mail_id}
    else:
        log_err(f"[DEAD]  {email} — {error}")
        if auto_delete:
            deleted = delete_mail_from_db(mail_id)
            if deleted:
                log_warn(f"  └─ Deleted from database")
            else:
                log_err(f"  └─ Failed to delete from database")
        return {"email": email, "status": "dead", "error": error, "id": mail_id}


def check_all(mail_type: str = "graph", auto_delete: bool = False):
    log_info(f"Fetching custom_mails from Supabase (mail_type={mail_type})...")
    mails = fetch_custom_mails(mail_type)

    if not mails:
        log_warn("No mails found in database.")
        return

    log_info(f"Found {len(mails)} mail(s) — checking validity...\n")

    alive = []
    dead = []
    skipped = []

    for mail in mails:
        result = check_mail(mail, auto_delete)
        status = result["status"]
        if status == "alive":
            alive.append(result)
        elif status == "dead":
            dead.append(result)
        else:
            skipped.append(result)

    print()
    log_info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    log_ok(f"Alive:   {len(alive)}")
    log_err(f"Dead:    {len(dead)}")
    if skipped:
        log_warn(f"Skipped: {len(skipped)}")
    log_info(f"Total:   {len(mails)}")
    log_info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if dead and not auto_delete:
        print()
        answer = input(eg.color("Delete all dead mails from database? (y/n): ", "#FFD700")).strip().lower()
        if answer == "y":
            for d in dead:
                deleted = delete_mail_from_db(d["id"])
                if deleted:
                    log_warn(f"Deleted: {d['email']}")
                else:
                    log_err(f"Failed to delete: {d['email']}")
            log_ok("Done.")


def main():
    print()
    log_info("Custom Mail Validator — Supabase Edition")
    print()

    mail_type = input(eg.color("Mail type to check (graph/imap) [default: graph]: ", "#00D9FF")).strip() or "graph"
    auto_delete_input = input(eg.color("Auto-delete dead mails without prompt? (y/n) [default: n]: ", "#00D9FF")).strip().lower()
    auto_delete = auto_delete_input == "y"

    print()
    check_all(mail_type, auto_delete)
    print()


if __name__ == "__main__":
    main()