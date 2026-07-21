"""DhvaniShield — demo UI.  Run: streamlit run app.py

One screen built for a frightened, possibly elderly user:
big verdict, plain-language action, reasons in simple words.
No 'safe' output exists anywhere in this interface, by design.
"""
import streamlit as st

from core import assess
from alert import send_family_alert
from tests.data import SCAM, AMBIGUOUS

st.set_page_config(page_title="DhvaniShield", page_icon="🛡️", layout="centered")
st.title("🛡️ DhvaniShield")
st.caption("A second opinion on a suspicious call — in your language. "
           "Green, yellow or red — a calm, honest verdict in seconds.")

sample = st.selectbox(
    "Try a sample, or paste your own below",
    ["— paste my own —",
     "Sample: CBI parcel scam (English)",
     "Sample: Aadhaar laundering scam (Hindi)",
     "Sample: bank OTP request (ambiguous)"])

prefill = ""
if sample.startswith("Sample: CBI"):
    prefill = SCAM[0]
elif sample.startswith("Sample: Aadhaar"):
    prefill = SCAM[1]
elif sample.startswith("Sample: bank OTP"):
    prefill = AMBIGUOUS[2]

text = st.text_area("What did the caller say? (any language — type, paste, "
                    "or transcribe)", value=prefill, height=140)

alert_on = st.checkbox("Alert my family member if the risk is high", value=True)
contact = st.text_input("Family contact name (demo)", value="Asha (daughter)") if alert_on else ""

if st.button("Check this call", type="primary") and text.strip():
    v = assess(text)
    if v.level == "HIGH_RISK":
        st.error(f"🔴 **DANGER — LIKELY SCAM**\n\n{v.action}")
        if alert_on and contact:
            msg = send_family_alert(contact, v.level,
                                    "It matches the digital-arrest scam pattern.")
            st.info(f"📨 Family alert sent (demo log): “{msg}”")
    elif v.level == "UNCERTAIN":
        st.warning(f"🟡 **BE CAREFUL — VERIFY FIRST**\n\n{v.action}")
    else:
        st.success(f"🟢 **LOOKS LIKE A NORMAL CALL**\n\n{v.action}")

    if v.explanation:
        st.subheader("Why")
        for line in v.explanation:
            st.markdown(f"- {line}")

    st.caption("DhvaniShield: green means nothing suspicious was found. When in any "
               "doubt, it tells you honestly and points you to the helpline 1930.")
