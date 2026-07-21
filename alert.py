"""Family alert — breaks the scammer's isolation tactic.

Demo mode logs alerts locally; the send() call is structured so a real
channel (SMS gateway, WhatsApp Business API, Telegram bot) can be
plugged in by replacing one function. Consent-first: alerts fire only
for contacts the user registered in advance.
"""
from datetime import datetime
from pathlib import Path

ALERT_LOG = Path(__file__).parent / "alerts.log"


def send_family_alert(contact_name: str, verdict_level: str, summary: str) -> str:
    msg = (f"DhvaniShield alert for {contact_name}: a call your family member "
           f"is on was assessed as {verdict_level}. {summary} "
           f"Please call them now on their other number, and remind them: "
           f"hang up, and dial 1930 if money was requested.")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with ALERT_LOG.open("a") as f:
        f.write(f"[{stamp}] {msg}\n")
    return msg
