"""
OPTIONAL desktop popup notifier. You do NOT need this — every ping already
lands in the in-app Inbox tab. Run this only if you'd like a native popup on
your own PC instead of checking the tab. No account, no bot, no admin rights.

    pip install -r requirements-watch.txt
    python watch.py "Your Name"

Uses the exact name as it appears in the app's user menu. Reads
VENDOR_SERVER_URL and SITE_PASSWORD from the same .env the app uses.
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
SERVER = os.getenv("VENDOR_SERVER_URL", "http://localhost:8000").rstrip("/")
PASSWORD = os.getenv("SITE_PASSWORD", "")
POLL = int(os.getenv("WATCH_POLL_SECONDS", "20"))

if len(sys.argv) < 2:
    print('Usage: python watch.py "Your Name"')
    sys.exit(1)
USER = sys.argv[1]

try:
    from plyer import notification as toast
except ImportError:
    print("Missing dependency. Run: pip install -r requirements-watch.txt")
    sys.exit(1)


def login():
    s = requests.Session()
    r = s.post(f"{SERVER}/api/login", data={"password": PASSWORD}, timeout=10)
    if r.status_code != 200:
        print(f"Login failed ({r.status_code}). Check SITE_PASSWORD in .env.")
        sys.exit(1)
    return s


def main():
    print(f"Watching for '{USER}' on {SERVER} (every {POLL}s). Ctrl+C to stop.\n")
    session = login()
    seen, first = set(), True
    while True:
        try:
            r = session.get(f"{SERVER}/api/notifications", params={"user": USER}, timeout=10)
            if r.status_code == 401:
                session = login(); continue
            for n in r.json():
                if n["id"] in seen:
                    continue
                seen.add(n["id"])
                if first or n.get("to_user") != USER:
                    continue
                title = "Vendor Drive: " + (n.get("action", "ping").replace("_", " ").title())
                body = n.get("message") or f"From {n.get('from_user', '')}"
                try:
                    toast.notify(title=title, message=body[:250], timeout=12)
                except Exception as e:
                    print(f"({e}) {title}: {body}")
            first = False
        except requests.exceptions.RequestException as e:
            print(f"Connection issue, retrying: {e}")
        time.sleep(POLL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
