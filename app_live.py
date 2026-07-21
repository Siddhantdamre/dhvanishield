"""DhvaniShield — demo UI.  Run: streamlit run app_live.py

Tab 1: check any call text (traffic-light verdict).
Tab 2: LIVE CALL SIMULATION — the astonishment moment. The scam call
plays out utterance by utterance; the six coercion stages light up as
the machine reads the manipulation in real time; the screen flips RED
mid-call — before money is ever mentioned — and the family alert fires.
"""
import time

import streamlit as st

from shield.engine import assess
from shield.registry import CANONICAL_STAGES
from shield.stream import stream, earliness
from alert import send_family_alert
from tests.data import SCAM, AMBIGUOUS

st.set_page_config(page_title="DhvaniShield", page_icon="🛡️", layout="centered")
st.title("🛡️ DhvaniShield")
st.caption("It doesn't just hear words. It reads the grammar of coercion — live.")

STAGE_LABELS = {
    "authority_impersonation": "1 Authority",
    "false_accusation": "2 Accusation",
    "isolation": "3 Isolation",
    "urgency_threat": "4 Threat",
    "money_movement": "5 Money",
    "remote_access_credentials": "6 Access",
}


def stage_bar(stages_hit):
    cols = st.columns(6)
    for col, s in zip(cols, CANONICAL_STAGES):
        with col:
            if s in stages_hit:
                st.markdown(f"**:red[{STAGE_LABELS[s]}] 🔥**")
            else:
                st.markdown(f":gray[{STAGE_LABELS[s]}]")


tab1, tab2 = st.tabs(["✅ Check a call", "🔴 Live call simulation"])

with tab1:
    sample = st.selectbox("Try a sample, or paste your own below",
                          ["— paste my own —",
                           "Sample: CBI parcel scam (English)",
                           "Sample: Aadhaar laundering scam (Hindi)",
                           "Sample: bank OTP request (needs care)"])
    prefill = ""
    if sample.startswith("Sample: CBI"):
        prefill = SCAM[0]
    elif sample.startswith("Sample: Aadhaar"):
        prefill = SCAM[1]
    elif sample.startswith("Sample: bank OTP"):
        prefill = AMBIGUOUS[2]
    text = st.text_area("What did the caller say? (any language)",
                        value=prefill, height=140)
    if st.button("Check this call", type="primary") and text.strip():
        v = assess(text)
        if v.level == "HIGH_RISK":
            st.error(f"🔴 **DANGER — LIKELY SCAM**\n\n{v.action}")
        elif v.level == "UNCERTAIN":
            st.warning(f"🟡 **BE CAREFUL — VERIFY FIRST**\n\n{v.action}")
        else:
            st.success(f"🟢 **LOOKS LIKE A NORMAL CALL**\n\n{v.action}")
        from shield.meter import meter as _meter
        m = _meter(text)
        st.markdown("**What is being done to your mind right now:**")
        for label, val in m["pressures"].items():
            st.progress(val / 100, text=f"{label} — {val}")
        if v.explanation:
            with st.expander("Why"):
                for line in v.explanation:
                    st.markdown(f"- {line}")
        from shield.access import accessible_bundle
        lang = st.radio("Language", ["en", "hi", "mr"], horizontal=True,
                        key="acc_lang")
        b = accessible_bundle(v.level, lang)
        with st.expander("🔊 Spoken verdict (for blind users / read aloud)"):
            st.markdown(f"> {b['speech']}")
        with st.expander("👁️ Picture card (deaf & low-literacy users)"):
            st.markdown(b["picto"])
        st.caption("💡 " + b["codeword_tip"])

with tab2:
    st.markdown("Watch DhvaniShield listen to a digital-arrest call as it happens. "
                "The six stages of the scam script light up as the machine "
                "recognises them — and it turns red **before money is mentioned**.")
    pick = st.selectbox("Choose a call", [
        "CBI parcel scam (English)",
        "FedEx → Mumbai Police digital arrest (English)",
        "Aadhaar laundering scam (Hindi)",
        "Crime branch scam (Marathi)"])
    call = {"CBI": SCAM[0], "FedEx": SCAM[4],
            "Aadhaar": SCAM[1], "Crime": SCAM[8]}[pick.split()[0]]
    speed = st.slider("Playback speed (seconds per line)", 0.5, 3.0, 1.5)
    alert_contact = st.text_input("Family contact (gets alerted on red)",
                                  value="Asha (daughter)")

    if st.button("▶️ Play the call", type="primary"):
        status = st.empty()
        stages_area = st.empty()
        transcript = st.empty()
        alert_area = st.empty()
        lines, fired = [], False
        e = earliness(call)
        for step in stream(call):
            lines.append(f"🗣️ {step.utterance}.")
            transcript.markdown("\n\n".join(lines))
            with stages_area.container():
                stage_bar(step.stages_so_far)
            lvl = step.verdict.level
            if lvl == "HIGH_RISK" and not fired:
                fired = True
                status.error(
                    f"🔴 **SCAM DETECTED — utterance {step.index+1} of "
                    f"{e['utterances']}, before any money was requested.** "
                    f"HANG UP. Call 1930.")
                msg = send_family_alert(alert_contact, "HIGH_RISK",
                                        "A digital-arrest scam call is in progress.")
                alert_area.info(f"📨 Family alert sent: “{msg}”")
            elif lvl == "UNCERTAIN" and not fired:
                status.warning("🟡 Warning signs building — verify before acting.")
            elif not fired:
                status.success("🟢 Nothing suspicious yet.")
            time.sleep(speed)
        if fired:
            st.markdown(
                f"**DhvaniShield flagged this call at "
                f"{e['fired_fraction']:.0%} of its length — "
                f"{'before' if e['before_money'] else 'at'} the money stage. "
                f"On our 12-scam benchmark it fires at or before the money "
                f"stage in 12/12 calls, with zero false reassurance.**")


# ---------------- Scam Gym: inoculation mode ----------------
# Prebunking research (inoculation theory) shows that experiencing a
# weakened attack builds lasting resistance. Detection protects you
# today; inoculation protects you forever.
import random as _rnd

from shield.trajectory import _utterances

with st.expander("🥊 Scam Gym — train yourself against the scammers"):
    st.markdown("A call will play line by line. Press **It's a scam** the "
                "moment you're sure — or end the call as normal. Can you "
                "beat DhvaniShield?")
    if "gym_call" not in st.session_state or st.button("🎲 New call"):
        pool = SCAM + [
            "Hello, this is the courier company. Your delivery is scheduled "
            "for tomorrow between 10 and 12. Please keep your phone reachable.",
            "Good morning, I am calling from your bank about your fixed "
            "deposit maturity next month. You can visit the branch anytime.",
        ]
        st.session_state.gym_call = _rnd.choice(pool)
        st.session_state.gym_idx = 1
        st.session_state.gym_done = False
    call = st.session_state.gym_call
    utts = _utterances(call)
    shown = utts[: st.session_state.gym_idx]
    for u in shown:
        st.markdown(f"🗣️ {u}.")
    c1, c2, c3 = st.columns(3)
    if not st.session_state.gym_done:
        if c1.button("▶ Next line") and st.session_state.gym_idx < len(utts):
            st.session_state.gym_idx += 1
            st.rerun()
        guess_scam = c2.button("🚨 It's a scam!")
        guess_ok = c3.button("✅ Seems normal")
        if guess_scam or guess_ok:
            st.session_state.gym_done = True
            truth_scam = call in SCAM
            e = earliness(call) if truth_scam else None
            if guess_scam and truth_scam:
                you_at = st.session_state.gym_idx
                ds_at = e["fired_at"] + 1
                st.success(f"Correct — it IS a scam. You caught it at line "
                           f"{you_at}; DhvaniShield fired at line {ds_at}. "
                           f"{'You beat the machine! 🏆' if you_at <= ds_at else 'The machine was faster — study the stages below.'}")
            elif guess_ok and not truth_scam:
                st.success("Correct — a normal call. Well judged.")
            elif guess_scam and not truth_scam:
                st.warning("This one was actually a normal call. Healthy "
                           "suspicion — but remember real deliveries and banks "
                           "do call. Verify, don't panic.")
            else:
                st.error("This WAS a scam — and this is exactly how people "
                         "get trapped. Replay it and watch the stages below.")
            if truth_scam:
                v = assess(call)
                st.markdown("**The manipulation stages in this call:**")
                for line in v.explanation:
                    st.markdown(f"- {line}")
