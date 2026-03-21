"""
Car Lease Contract Review & Negotiation AI Assistant
Streamlit Frontend — connects to Flask backend with MySQL
New: Telegram floating button, contract history, analytics dashboard
"""
from back import MODEL
import streamlit as st
import requests
import json
import uuid
import time

BACKEND = "http://127.0.0.1:5000"

# ─────────────────────────────────────────
# Your Telegram bot username — change this!
# ─────────────────────────────────────────
TELEGRAM_BOT_USERNAME = "CarLeaseAI_bot"   # ← replace with your actual bot @username

st.set_page_config(
    page_title="CarLease AI",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

.main {{ background-color: #0f1117; }}

.metric-card {{
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3350;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 6px 0;
}}
.metric-label {{ color: #8b93b0; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
.metric-value {{ color: #e8ecf8; font-size: 20px; font-weight: 700; margin-top: 4px; }}
.metric-value.good {{ color: #34d399; }}
.metric-value.warn {{ color: #fbbf24; }}
.metric-value.bad  {{ color: #f87171; }}

.flag-box {{
    background: #2d1b1b;
    border-left: 3px solid #f87171;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    color: #fca5a5;
    font-size: 13px;
}}
.good-box {{
    background: #1b2d1e;
    border-left: 3px solid #34d399;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    color: #6ee7b7;
    font-size: 13px;
}}
.chat-user {{
    background: #1e3a5f;
    border-radius: 12px 12px 4px 12px;
    padding: 10px 14px;
    margin: 8px 0 8px auto;
    max-width: 75%;
    color: #bfdbfe;
    font-size: 14px;
    float: right;
    clear: both;
}}
.chat-bot {{
    background: #1e2130;
    border-radius: 12px 12px 12px 4px;
    padding: 10px 14px;
    margin: 8px auto 8px 0;
    max-width: 80%;
    color: #e2e8f0;
    font-size: 14px;
    float: left;
    clear: both;
    border: 1px solid #2e3350;
}}
.section-header {{
    color: #7c8db5;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 20px 0 10px 0;
    border-bottom: 1px solid #1e2335;
    padding-bottom: 6px;
}}
.score-badge {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 13px;
}}
.stButton > button {{
    background: linear-gradient(135deg, #3b5bdb, #4c6ef5);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 20px;
    transition: all 0.2s;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, #4c6ef5, #5c7cfa);
    transform: translateY(-1px);
}}

/* ── History card ── */
.history-card {{
    background: linear-gradient(135deg,#1a1f33,#1e2540);
    border: 1px solid #2e3a5a;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 8px 0;
    cursor: pointer;
    transition: border-color .2s;
}}
.history-card:hover {{ border-color: #4c6ef5; }}
.history-title {{ color: #c5cde8; font-weight: 600; font-size: 14px; }}
.history-meta  {{ color: #6b7aa0; font-size: 11px; margin-top:4px; }}

/* ── Analytics stats ── */
.stat-box {{
    background: linear-gradient(135deg,#1e2540,#222a45);
    border: 1px solid #2e3a5a;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
}}
.stat-num  {{ font-size: 36px; font-weight: 800; color: #4c6ef5; line-height: 1; }}
.stat-lbl  {{ font-size: 12px; color: #8b93b0; margin-top: 6px; text-transform: uppercase; letter-spacing: 1px; }}

/* ══════════════════════════════════════
   TELEGRAM FLOATING BUTTON
   ══════════════════════════════════════ */
.tg-fab {{
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 9999;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #2aabee, #229ed9);
    box-shadow: 0 4px 20px rgba(42,171,238,.55);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    text-decoration: none;
    transition: transform .25s ease, box-shadow .25s ease;
    animation: tg-pulse 2.6s infinite;
}}
.tg-fab:hover {{
    transform: scale(1.12) translateY(-3px);
    box-shadow: 0 8px 28px rgba(42,171,238,.75);
    animation: none;
}}
.tg-fab svg {{ width: 30px; height: 30px; fill: #fff; }}

.tg-tooltip {{
    position: fixed;
    bottom: 36px;
    right: 100px;
    z-index: 9998;
    background: #1e2540;
    color: #c5cde8;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 8px;
    white-space: nowrap;
    border: 1px solid #2e3a5a;
    box-shadow: 0 4px 14px rgba(0,0,0,.4);
    opacity: 0;
    pointer-events: none;
    transition: opacity .2s;
}}
.tg-fab:hover + .tg-tooltip {{ opacity: 1; }}

@keyframes tg-pulse {{
    0%,100% {{ box-shadow: 0 4px 20px rgba(42,171,238,.55); }}
    50%      {{ box-shadow: 0 4px 30px rgba(42,171,238,.90); }}
}}
</style>

<!-- ══ TELEGRAM FLOATING ACTION BUTTON ══ -->
<a class="tg-fab"
   href="https://t.me/{TELEGRAM_BOT_USERNAME}"
   target="_blank"
   title="Open in Telegram Bot">
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373
             12-12S18.627 0 12 0zm5.894 8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447
             1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871
             4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194
             1.006.131.833.941z"/>
  </svg>
</a>
<div class="tg-tooltip">Chat on Telegram Bot 💬</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Session ID (persists per browser tab)
# ─────────────────────────────────────────
def init_state():
    defaults = {
        "session_id":        str(uuid.uuid4()),
        "contract_text":     "",
        "contract_text_2":   "",
        "contract_id":       None,
        "contract_id_2":     None,
        "sla":               {},
        "sla_2":             {},
        "analysis":          "",
        "chat_history":      [],
        "vin_result":        {},
        "pages":             0,
        "file_name":         "",
        "file_name_2":       "",
        "negotiation_output":"",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
SESSION = st.session_state.session_id


# ─────────────────────────────────────────
# Helper: API calls
# ─────────────────────────────────────────
def api_post(endpoint, **kwargs):
    try:
        # Inject session_id into JSON payloads automatically
        if "json" in kwargs and isinstance(kwargs["json"], dict):
            kwargs["json"]["session_id"] = SESSION
        r = requests.post(f"{BACKEND}/{endpoint}", timeout=300, **kwargs)
        if not r.ok:
            try:
                msg = r.json().get("error") or r.text
            except Exception:
                msg = r.text or f"HTTP {r.status_code}"
            return None, f"❌ Backend error ({r.status_code}): {msg}"
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to backend. Make sure `back.py` is running:\n\npython back.py"
    except requests.exceptions.Timeout:
        return None, "❌ Request timed out. Try a shorter contract or check your API key."
    except Exception as e:
        return None, str(e)


def api_get(endpoint, **params):
    try:
        params["session_id"] = SESSION
        r = requests.get(f"{BACKEND}/{endpoint}", params=params, timeout=30)
        return r.json(), None
    except Exception as e:
        return None, str(e)


def score_color(score_str):
    try:
        score = float(str(score_str).split("/")[0].strip())
        if score >= 7: return "good"
        if score >= 5: return "warn"
        return "bad"
    except:
        return "warn"


# ─────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚗 CarLease AI")
    st.markdown("<div style='color:#6b7595;font-size:12px;margin-bottom:20px'>Contract Review & Negotiation</div>", unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        [
            "📄 Upload & Extract",
            "🔍 Analysis",
            "💬 Chat Assistant",
            "🔑 VIN Lookup",
            "✍️ Negotiation Helper",
            "⚖️ Compare Contracts",
            "📂 My History",
            "📊 Analytics",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Backend status
    try:
        r = requests.get(BACKEND, timeout=3)
        data = r.json()
        st.success("✅ Backend connected")
        mysql_ok = data.get("mysql") == "connected"
        if mysql_ok:
            st.success("✅ MySQL connected")
        else:
            st.warning(f"⚠️ MySQL: {data.get('mysql','offline')}")
    except:
        st.error("❌ Backend offline\nRun: `python back.py`")

    if st.session_state.file_name:
        st.markdown(f"**📎 Loaded:** `{st.session_state.file_name}`")
        if st.session_state.sla.get("vehicle_make"):
            st.markdown(f"**🚙** {st.session_state.sla.get('vehicle_year','')} {st.session_state.sla.get('vehicle_make','')} {st.session_state.sla.get('vehicle_model','')}")
        if st.session_state.sla.get("fairness_score"):
            score = st.session_state.sla["fairness_score"]
            st.markdown(f"**⚖️ Fairness:** {score}")

    st.markdown("---")
    st.markdown(
        f"<a href='https://t.me/{TELEGRAM_BOT_USERNAME}' target='_blank' "
        f"style='display:flex;align-items:center;gap:8px;text-decoration:none;"
        f"background:#1a2540;padding:10px 14px;border-radius:10px;"
        f"border:1px solid #2e3a5a;color:#2aabee;font-weight:600;font-size:13px;'>"
        f"<svg width='18' height='18' viewBox='0 0 24 24' fill='#2aabee'>"
        f"<path d='M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 "
        f"8.221-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l"
        f".213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-"
        f".643.136-.953l11.57-4.461c.537-.194 1.006.131.833.941z'/></svg>"
        f"Open Telegram Bot</a>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════
# PAGE 1: Upload & Extract
# ══════════════════════════════════════════════════════════════
if page == "📄 Upload & Extract":
    st.title("📄 Upload Contract")
    st.markdown("Upload your car lease or loan contract PDF to get started.")

    col1, col2 = st.columns([3, 2])

    with col1:
        uploaded = st.file_uploader("Choose a PDF contract", type=["pdf"], key="upload1")

        if uploaded and uploaded.name != st.session_state.file_name:
            st.session_state.file_name = uploaded.name
            with st.spinner("📖 Reading PDF..."):
                res, err = api_post(
                    "extract_text",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    data={"session_id": SESSION}
                )
                if err:
                    st.error(err)
                elif res:
                    st.session_state.contract_text = res["text"]
                    st.session_state.pages          = res["pages"]
                    st.session_state.contract_id    = res.get("contract_id")
                    st.success(f"✅ Extracted {res['pages']} pages · {len(res['text'])} characters · saved to DB")

        if st.session_state.contract_text:
            with st.expander("📃 View Contract Text", expanded=False):
                st.text_area("", st.session_state.contract_text, height=300, label_visibility="collapsed")

            st.markdown("---")
            if st.button("🔍 Extract Key Terms & SLA", use_container_width=True):
                with st.spinner(f"🤖 {MODEL} is analysing your contract..."):
                    res, err = api_post("extract_sla", json={
                        "text":        st.session_state.contract_text,
                        "contract_id": st.session_state.contract_id,
                    })
                    if err:
                        st.error(err)
                    elif res:
                        st.session_state.sla = res.get("sla", {})
                        st.success("✅ Extraction complete — saved to MySQL!")

    with col2:
        if st.session_state.sla:
            sla = st.session_state.sla
            st.markdown("### 📊 Extracted Terms")

            def metric(label, value, color_class=""):
                val = value if value and value != "null" else "—"
                return f"""<div class='metric-card'>
                <div class='metric-label'>{label}</div>
                <div class='metric-value {color_class}'>{val}</div>
                </div>"""

            score_cls = score_color(sla.get("fairness_score", "5"))
            st.markdown(metric("Fairness Score",      sla.get("fairness_score"),           score_cls), unsafe_allow_html=True)
            st.markdown(metric("Monthly Payment",     sla.get("monthly_payment")),          unsafe_allow_html=True)
            st.markdown(metric("APR / Interest Rate", sla.get("apr")),                      unsafe_allow_html=True)
            st.markdown(metric("Lease Term",          f"{sla.get('lease_term_months','—')} months"), unsafe_allow_html=True)
            st.markdown(metric("Down Payment",        sla.get("down_payment")),             unsafe_allow_html=True)
            st.markdown(metric("Mileage / Year",      f"{sla.get('mileage_allowance_per_year','—')} miles"), unsafe_allow_html=True)
            st.markdown(metric("Overage Fee",         sla.get("mileage_overage_fee")),      unsafe_allow_html=True)
            st.markdown(metric("Early Termination",   sla.get("early_termination_fee")),    unsafe_allow_html=True)
            st.markdown(metric("Buyout Price",        sla.get("purchase_option_price")),    unsafe_allow_html=True)
            st.markdown(metric("Residual Value",      sla.get("residual_value")),           unsafe_allow_html=True)

            if sla.get("red_flags"):
                st.markdown("<div class='section-header'>⚠️ Red Flags</div>", unsafe_allow_html=True)
                for flag in sla["red_flags"]:
                    st.markdown(f"<div class='flag-box'>{flag}</div>", unsafe_allow_html=True)

            with st.expander("📋 Full JSON Output"):
                st.json(sla)


# ══════════════════════════════════════════════════════════════
# PAGE 2: Analysis
# ══════════════════════════════════════════════════════════════
elif page == "🔍 Analysis":
    st.title("🔍 Contract Analysis")

    if not st.session_state.contract_text:
        st.warning("⬅️ Upload a contract first on the Upload page.")
    else:
        if st.button("📊 Run Full Analysis", use_container_width=True):
            with st.spinner(f"🧠 {MODEL} is reviewing your contract for fairness..."):
                res, err = api_post("analyze", json={
                    "text":        st.session_state.contract_text,
                    "sla":         st.session_state.sla,
                    "contract_id": st.session_state.contract_id,
                })
                if err:
                    st.error(err)
                elif res:
                    st.session_state.analysis = res["analysis"]

        if st.session_state.analysis:
            st.markdown(st.session_state.analysis)


# ══════════════════════════════════════════════════════════════
# PAGE 3: Chat Assistant
# ══════════════════════════════════════════════════════════════
elif page == "💬 Chat Assistant":
    st.title("💬 Chat with Your Contract")

    if not st.session_state.contract_text:
        st.warning("⬅️ Upload a contract first on the Upload page.")
    else:
        st.markdown("Ask anything about your contract — terms, clauses, what to watch out for.")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-user'>🧑 {msg['content'].split('Question:')[-1].strip()}</div><div style='clear:both'></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bot'>🤖 {msg['content']}</div><div style='clear:both'></div>", unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown("**💡 Try asking:**")
            cols = st.columns(2)
            suggestions = [
                "Is my APR rate competitive?",
                "What happens if I go over mileage?",
                "Can I negotiate the disposition fee?",
                "Explain the early termination clause",
                "What are my buyout options?",
                "Are there any hidden fees?"
            ]
            for i, sug in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(sug, key=f"sug_{i}"):
                        st.session_state._pending_question = sug
                        st.rerun()

        question = st.chat_input("Ask about your contract...")

        if hasattr(st.session_state, "_pending_question"):
            question = st.session_state._pending_question
            del st.session_state._pending_question

        if question:
            with st.spinner("🤖 Thinking..."):
                res, err = api_post("chat", json={
                    "question":    question,
                    "context":     st.session_state.contract_text,
                    "history":     st.session_state.chat_history,
                    "contract_id": st.session_state.contract_id,
                })
                if err:
                    st.error(err)
                else:
                    st.session_state.chat_history.append({"role": "user",      "content": f"Contract context:\n[loaded]\n\nQuestion: {question}"})
                    st.session_state.chat_history.append({"role": "assistant", "content": res["response"]})
                    st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()


# ══════════════════════════════════════════════════════════════
# PAGE 4: VIN Lookup
# ══════════════════════════════════════════════════════════════
elif page == "🔑 VIN Lookup":
    st.title("🔑 VIN Lookup")
    st.markdown("Look up any vehicle using its 17-character VIN. Results are cached in MySQL for instant re-lookup.")

    default_vin = st.session_state.sla.get("vin", "") or ""
    if default_vin:
        st.info(f"📎 VIN detected in your contract: `{default_vin}`")

    vin_input = st.text_input("Enter VIN Number (17 characters)", value=default_vin, max_chars=17, placeholder="e.g. 1HGBH41JXMN109186")

    if st.button("🔍 Look Up VIN", use_container_width=False):
        if len(vin_input) != 17:
            st.error("VIN must be exactly 17 characters.")
        else:
            with st.spinner("🔍 Fetching vehicle data from NHTSA..."):
                res, err = api_post("vin_lookup", json={"vin": vin_input})
                if err:
                    st.error(err)
                else:
                    st.session_state.vin_result = res.get("vehicle", {})
                    if res.get("cached"):
                        st.info("⚡ Result loaded from MySQL cache (instant)")

    if st.session_state.vin_result:
        v = st.session_state.vin_result
        st.markdown("---")
        st.subheader(f"🚗 {v.get('year','')} {v.get('make','')} {v.get('model','')} {v.get('trim','')}")

        col1, col2, col3 = st.columns(3)
        fields = [
            ("Body Class",    "body_class"),  ("Engine (L)",  "engine"),   ("Cylinders",  "cylinders"),
            ("Fuel Type",     "fuel_type"),   ("Drive Type",  "drive_type"),("Transmission","transmission"),
            ("Doors",         "doors"),       ("Series",      "series"),   ("Assembly",   "plant_country"),
        ]
        for i, (label, key) in enumerate(fields):
            with [col1, col2, col3][i % 3]:
                st.metric(label, v.get(key, "—") or "—")

        st.markdown("---")
        recall_count = v.get("recall_count", 0)
        if recall_count == 0:
            st.success("✅ No recalls found for this vehicle.")
        else:
            st.warning(f"⚠️ {recall_count} recall(s) found for this make/model/year")
            for rec in v.get("recalls", []):
                with st.expander(f"🔧 {rec.get('component','Recall')}"):
                    st.write("**Summary:**",     rec.get("summary", ""))
                    st.write("**Consequence:**", rec.get("consequence", ""))


# ══════════════════════════════════════════════════════════════
# PAGE 5: Negotiation Helper
# ══════════════════════════════════════════════════════════════
elif page == "✍️ Negotiation Helper":
    st.title("✍️ Negotiation Helper")

    if not st.session_state.sla:
        st.warning("⬅️ Upload and extract your contract first.")
    else:
        st.markdown("Generate a negotiation email or talking-points script based on your contract's issues.")

        sla = st.session_state.sla
        col1, col2 = st.columns([2, 1])

        with col1:
            concerns = st.text_area(
                f"What are your main concerns? (optional — {MODEL} will auto-detect from your contract)",
                placeholder="e.g. APR seems high, disposition fee is $500 which is above market…",
                height=100
            )
            neg_type = st.radio("Format", ["email", "script"], horizontal=True,
                                format_func=lambda x: "📧 Negotiation Email" if x == "email" else "🎙️ Talking Points Script")

            if st.button("✨ Generate Negotiation Content", use_container_width=True):
                with st.spinner("🤖 Crafting your negotiation strategy..."):
                    res, err = api_post("negotiate", json={
                        "sla":         sla,
                        "concerns":    concerns or "auto-detect from contract terms",
                        "type":        neg_type,
                        "contract_id": st.session_state.contract_id,
                    })
                    if err:
                        st.error(err)
                    else:
                        st.session_state.negotiation_output = res["negotiation"]

        with col2:
            st.markdown("**📋 Key Terms in Your Contract**")
            for label, key in [
                ("Monthly Payment",  "monthly_payment"),
                ("APR",              "apr"),
                ("Term",             "lease_term_months"),
                ("Disposition Fee",  "disposition_fee"),
                ("Early Exit Fee",   "early_termination_fee"),
                ("Mileage Limit",    "mileage_allowance_per_year"),
            ]:
                val = sla.get(key, "—")
                if val and val != "null":
                    st.markdown(f"**{label}:** {val}")

        if st.session_state.negotiation_output:
            st.markdown("---")
            st.markdown(st.session_state.negotiation_output)
            st.download_button(
                "⬇️ Download",
                data=st.session_state.negotiation_output,
                file_name=f"negotiation_{neg_type}.txt",
                mime="text/plain"
            )


# ══════════════════════════════════════════════════════════════
# PAGE 6: Compare Contracts
# ══════════════════════════════════════════════════════════════
elif page == "⚖️ Compare Contracts":
    st.title("⚖️ Compare Two Contracts")
    st.markdown("Upload a second contract to compare against your current one.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Contract A")
        if st.session_state.file_name:
            st.success(f"✅ Loaded: {st.session_state.file_name}")
            if st.session_state.sla:
                with st.expander("View Terms"):
                    st.json(st.session_state.sla)
        else:
            st.warning("Upload Contract A on the Upload page first.")

    with col2:
        st.subheader("Contract B")
        uploaded2 = st.file_uploader("Upload second contract (PDF)", type=["pdf"], key="upload2")

        if uploaded2 and uploaded2.name != st.session_state.file_name_2:
            st.session_state.file_name_2 = uploaded2.name
            with st.spinner("Reading Contract B..."):
                res, err = api_post(
                    "extract_text",
                    files={"file": (uploaded2.name, uploaded2.getvalue(), "application/pdf")},
                    data={"session_id": SESSION}
                )
                if not err and res:
                    st.session_state.contract_text_2 = res["text"]
                    st.session_state.contract_id_2   = res.get("contract_id")
                    res2, err2 = api_post("extract_sla", json={
                        "text":        res["text"],
                        "contract_id": res.get("contract_id"),
                    })
                    if not err2 and res2:
                        st.session_state.sla_2 = res2.get("sla", {})
                        st.success(f"✅ Extracted {uploaded2.name}")

        if st.session_state.sla_2:
            with st.expander("View Terms"):
                st.json(st.session_state.sla_2)

    if st.session_state.sla and st.session_state.sla_2:
        if st.button("⚖️ Compare Now", use_container_width=True):
            with st.spinner("🤖 Comparing contracts..."):
                res, err = api_post("compare", json={
                    "sla1":           st.session_state.sla,
                    "sla2":           st.session_state.sla_2,
                    "label1":         st.session_state.file_name or "Contract A",
                    "label2":         st.session_state.file_name_2 or "Contract B",
                    "contract_id_1":  st.session_state.contract_id,
                    "contract_id_2":  st.session_state.contract_id_2,
                })
                if err:
                    st.error(err)
                else:
                    st.markdown("---")
                    st.markdown(res["comparison"])
    elif st.session_state.sla and not st.session_state.sla_2:
        st.info("Upload Contract B above to enable comparison.")


# ══════════════════════════════════════════════════════════════
# PAGE 7: NEW — My Contract History (DB powered)
# ══════════════════════════════════════════════════════════════
elif page == "📂 My History":
    st.title("📂 My Contract History")
    st.markdown("All contracts you've uploaded this session — stored securely in MySQL.")

    res, err = api_get("history")
    if err:
        st.error(f"Could not fetch history: {err}")
    else:
        history = (res or {}).get("history", [])
        if not history:
            st.info("No contracts uploaded yet. Upload one on the **Upload & Extract** page!")
        else:
            for item in history:
                vehicle = " ".join(filter(None, [item.get("vehicle_year"), item.get("vehicle_make"), item.get("vehicle_model")])) or "Unknown Vehicle"
                score   = item.get("fairness_score") or "—"

                def safe_score_icon(s):
                    try:
                        if s in ["—", None, "null", "None", ""]:
                            return "⚪"
                        val = float(str(s).split("/")[0].strip())
                        if val >= 7: return "🟢"
                        if val >= 5: return "🟡"
                        return "🔴"
                    except:
                        return "⚪"

                score_c = safe_score_icon(score)

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(
                        f"<div class='history-card'>"
                        f"<div class='history-title'>🚗 {vehicle} — {item.get('file_name','contract.pdf')}</div>"
                        f"<div class='history-meta'>📅 {item.get('uploaded_at','—')} &nbsp;|&nbsp; "
                        f"📄 {item.get('page_count',0)} pages &nbsp;|&nbsp; "
                        f"💰 {item.get('monthly_payment','—')}/mo &nbsp;|&nbsp; APR: {item.get('apr','—')}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with col2:
                    st.markdown(f"<br><div style='text-align:center;font-size:20px'>{score_c}</div>", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"<br><div style='text-align:center;color:#8b93b0;font-size:13px'>Score: {score}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# PAGE 8: NEW — Analytics Dashboard (DB powered)
# ══════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.title("📊 My Usage Analytics")
    st.markdown("Powered by real data from your MySQL database.")

    res, err = api_get("analytics")
    if err:
        st.error(f"Could not fetch analytics: {err}")
    else:
        data = (res or {}).get("analytics", {})

        # Top stats row
        c1, c2, c3, c4 = st.columns(4)
        stats = [
            (c1, data.get("total_contracts",   0), "Contracts Reviewed"),
            (c2, data.get("total_chats",        0), "Chat Messages"),
            (c3, data.get("total_negotiations", 0), "Negotiations Generated"),
            (c4, data.get("total_vin_lookups",  0), "VIN Lookups (global)"),
        ]
        for col, num, lbl in stats:
            with col:
                st.markdown(
                    f"<div class='stat-box'>"
                    f"<div class='stat-num'>{num}</div>"
                    f"<div class='stat-lbl'>{lbl}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # Recent fairness scores
        recent = data.get("recent_scores", [])
        if recent:
            st.subheader("📈 Recent Fairness Scores")
            for item in recent:
                score_raw = item.get("fairness_score") or "N/A"
                fname     = item.get("file_name", "contract.pdf")
                date      = item.get("uploaded_at", "")

                try:
                    score_val = float(str(score_raw).split("/")[0])
                    bar_pct   = int(score_val * 10)
                    bar_color = "#34d399" if score_val >= 7 else "#fbbf24" if score_val >= 5 else "#f87171"
                except:
                    bar_pct   = 50
                    bar_color = "#4c6ef5"

                st.markdown(
                    f"<div style='margin:10px 0'>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:4px'>"
                    f"<span style='color:#c5cde8;font-size:13px'>{fname}</span>"
                    f"<span style='color:{bar_color};font-weight:700'>{score_raw} &nbsp; <span style='color:#6b7aa0;font-weight:400'>{date}</span></span>"
                    f"</div>"
                    f"<div style='background:#1e2540;border-radius:6px;height:8px'>"
                    f"<div style='background:{bar_color};width:{bar_pct}%;height:8px;border-radius:6px;transition:width .5s'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("Upload and analyse contracts to see your fairness score trends here.")

        st.markdown("---")
        st.markdown("### 💡 Tips Based on Your Usage")
        tips = []
        if data.get("total_contracts", 0) >= 2:
            tips.append("📊 You've reviewed multiple contracts — use **Compare Contracts** to find the best deal!")
        if data.get("total_chats", 0) == 0:
            tips.append("💬 Try the **Chat Assistant** to ask specific questions about your contract clauses.")
        if data.get("total_negotiations", 0) == 0:
            tips.append("✍️ Use **Negotiation Helper** to auto-generate a negotiation email for your dealer.")
        tips.append("📱 Use the **Telegram Bot** (bottom-right button) to review contracts on the go!")

        for tip in tips:
            st.markdown(f"- {tip}")