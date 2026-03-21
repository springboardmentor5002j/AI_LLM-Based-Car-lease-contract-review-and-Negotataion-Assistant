"""
Car Lease AI — Telegram Bot
Calls the Flask backend (back.py) directly via HTTP.
Make sure back.py is running on http://localhost:5000 before starting this bot.

Install: pip install "python-telegram-bot==13.15"
Run:     python bot.py
"""

import os
import json
import requests
from telegram import Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# ─────────────────────────────────────────
# Config — set TELEGRAM_TOKEN env variable
# or paste your token directly below
# ─────────────────────────────────────────
TOKEN   = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
BACKEND = os.getenv("BACKEND_URL",    "http://localhost:5000")

# ─────────────────────────────────────────
# In-memory store per chat_id:
# { chat_id: { contract_text, contract_id, sla, fairness_score, chat_history } }
# ─────────────────────────────────────────
user_store: dict = {}


# ─────────────────────────────────────────
# Backend helpers
# ─────────────────────────────────────────
def backend_post(endpoint: str, session_id: str, **kwargs) -> dict:
    """POST to Flask backend. Returns parsed JSON or raises."""
    if "json" in kwargs:
        kwargs["json"]["session_id"] = session_id
    r = requests.post(f"{BACKEND}/{endpoint}", timeout=300, **kwargs)
    r.raise_for_status()
    return r.json()


def backend_get(endpoint: str, session_id: str, **params) -> dict:
    """GET from Flask backend."""
    params["session_id"] = session_id
    r = requests.get(f"{BACKEND}/{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def safe_reply(update: Update, text: str):
    """Send a message, splitting if over Telegram's 4096-char limit."""
    for i in range(0, len(text), 4000):
        update.message.reply_text(text[i:i + 4000])


def get_store(chat_id: int) -> dict:
    """Return (or create) the store for this chat."""
    if chat_id not in user_store:
        user_store[chat_id] = {
            "contract_text":  "",
            "contract_id":    None,
            "sla":            {},
            "fairness_score": None,
            "chat_history":   [],
        }
    return user_store[chat_id]


def session_id(chat_id: int) -> str:
    return f"tg_{chat_id}"


# ─────────────────────────────────────────
# /start  &  /help
# ─────────────────────────────────────────
HELP_TEXT = (
    "👋 *Welcome to CarLease AI Bot!*\n\n"
    "📎 Send me your lease/loan contract *PDF* to get started\\.\n\n"
    "*Commands after upload:*\n"
    "  /summary  — Extract all key contract terms\n"
    "  /score    — Fairness score \\+ red flags\n"
    "  /negotiate — Generate negotiation email\n"
    "  /script   — Generate negotiation talking script\n"
    "  /vin \\<VIN\\> — Vehicle details \\& recalls\n"
    "  /price \\<Year\\> \\<Make\\> \\<Model\\> — Market price\n"
    "  /history  — Your past contracts \\(from DB\\)\n"
    "  /clear    — Clear current contract\n"
    "  /help     — Show this message\n\n"
    "💬 Or just *ask any question* about your contract\\!"
)


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Welcome to the Car Lease Review Assistant!\n\n"
        "📎 Send me your lease contract PDF to get started.\n\n"
        "Commands after upload:\n"
        "  /summary  — Extract all key contract terms\n"
        "  /score    — Contract Fairness Score + red flags\n"
        "  /negotiate — Generate negotiation email\n"
        "  /script   — Generate negotiation talking script\n"
        "  /vin <VIN> — Look up vehicle details & recalls\n"
        "  /price <Year> <Make> <Model> — Market price info\n"
        "  /history  — View your past contracts\n"
        "  /clear    — Clear current contract from memory\n"
        "  /help     — Show this help message\n\n"
        "Or just ask any question about your contract! 💬"
    )


def help_cmd(update: Update, context: CallbackContext):
    start(update, context)


# ─────────────────────────────────────────
# Document handler — PDF upload
# ─────────────────────────────────────────
def handle_document(update: Update, context: CallbackContext):
    msg     = update.message
    chat_id = msg.chat_id
    doc     = msg.document

    if not doc.file_name.lower().endswith(".pdf"):
        msg.reply_text("⚠️ Please send a PDF file.")
        return

    msg.reply_text("⏳ Uploading and reading your contract... this may take 30–60 seconds.")

    try:
        tg_file  = doc.get_file()
        raw_bytes = tg_file.download_as_bytearray()

        res = backend_post(
            "extract_text",
            session_id(chat_id),
            files={"file": (doc.file_name, bytes(raw_bytes), "application/pdf")},
            data={"session_id": session_id(chat_id)},
        )

        store = get_store(chat_id)
        store["contract_text"] = res.get("text", "")
        store["contract_id"]   = res.get("contract_id")
        store["sla"]           = {}
        store["fairness_score"] = None
        store["chat_history"]   = []

        pages = res.get("pages", 0)
        chars = len(store["contract_text"])
        msg.reply_text(
            f"✅ Contract uploaded!\n\n"
            f"📄 Pages: {pages}\n"
            f"📝 Characters extracted: {chars:,}\n\n"
            "What would you like to do?\n"
            "• /summary — Extract key terms\n"
            "• /score   — Get fairness score & red flags\n"
            "• Or just ask me any question about the contract"
        )

    except requests.exceptions.ConnectionError:
        msg.reply_text("❌ Cannot connect to backend. Make sure back.py is running.")
    except Exception as e:
        msg.reply_text(f"❌ Error processing contract: {e}")


# ─────────────────────────────────────────
# /summary — SLA extraction
# ─────────────────────────────────────────
def cmd_summary(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    store   = get_store(chat_id)

    if not store["contract_text"]:
        update.message.reply_text("📎 Please upload your contract PDF first.")
        return

    update.message.reply_text("🔍 Extracting contract terms... please wait.")

    try:
        res = backend_post("extract_sla", session_id(chat_id), json={
            "text":        store["contract_text"],
            "contract_id": store["contract_id"],
        })
        sla = res.get("sla", {})
        store["sla"] = sla

        def fmt(v):
            return str(v) if v and str(v) not in ["null", "None", ""] else "—"

        lines = [
            "📋 *CONTRACT TERMS SUMMARY*",
            "─" * 30,
            f"🚗 Vehicle:       {fmt(sla.get('vehicle_year'))} {fmt(sla.get('vehicle_make'))} {fmt(sla.get('vehicle_model'))}",
            f"🏦 Lender:        {fmt(sla.get('lender_name'))}",
            f"🏪 Dealer:        {fmt(sla.get('dealer_name'))}",
            "",
            f"💰 Monthly Payment: {fmt(sla.get('monthly_payment'))}",
            f"📉 APR / Rate:      {fmt(sla.get('apr'))}",
            f"📅 Lease Term:      {fmt(sla.get('lease_term_months'))} months",
            f"⬇️  Down Payment:   {fmt(sla.get('down_payment'))}",
            f"🔢 Money Factor:    {fmt(sla.get('money_factor'))}",
            "",
            f"🏁 Residual Value:  {fmt(sla.get('residual_value'))}",
            f"🛣️  Mileage/Year:   {fmt(sla.get('mileage_allowance_per_year'))} miles",
            f"⚡ Overage Fee:     {fmt(sla.get('mileage_overage_fee'))}/mile",
            f"🚪 Early Exit Fee:  {fmt(sla.get('early_termination_fee'))}",
            f"🔖 Buyout Price:    {fmt(sla.get('purchase_option_price'))}",
            f"📦 Disposition Fee: {fmt(sla.get('disposition_fee'))}",
            f"🔐 Acquisition Fee: {fmt(sla.get('acquisition_fee'))}",
            "",
            f"⚖️  Fairness Score:  {fmt(sla.get('fairness_score'))}",
        ]

        red_flags = sla.get("red_flags") or []
        if red_flags:
            lines.append("\n⚠️ RED FLAGS:")
            for flag in red_flags:
                lines.append(f"  • {flag}")

        safe_reply(update, "\n".join(lines))
        update.message.reply_text("Run /score for a full fairness analysis.")

    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


# ─────────────────────────────────────────
# /score — Full fairness analysis
# ─────────────────────────────────────────
def cmd_score(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    store   = get_store(chat_id)

    if not store["contract_text"]:
        update.message.reply_text("📎 Please upload your contract PDF first.")
        return

    # Auto-extract SLA if not done yet
    if not store["sla"]:
        update.message.reply_text("⏳ Extracting contract terms first...")
        try:
            res = backend_post("extract_sla", session_id(chat_id), json={
                "text":        store["contract_text"],
                "contract_id": store["contract_id"],
            })
            store["sla"] = res.get("sla", {})
        except Exception as e:
            update.message.reply_text(f"❌ Error extracting terms: {e}")
            return

    update.message.reply_text("🧠 Running full contract analysis... please wait.")

    try:
        res = backend_post("analyze", session_id(chat_id), json={
            "text":        store["contract_text"],
            "sla":         store["sla"],
            "contract_id": store["contract_id"],
        })
        analysis = res.get("analysis", "No analysis returned.")
        safe_reply(update, f"📊 CONTRACT ANALYSIS\n{'─'*30}\n\n{analysis}")

        score = store["sla"].get("fairness_score")
        try:
            score_val = float(str(score).split("/")[0]) if score and str(score) not in ["null","None",""] else 5
            if score_val < 7:
                update.message.reply_text(
                    "💡 This contract has issues worth negotiating.\n"
                    "Run /negotiate to generate a negotiation email."
                )
        except Exception:
            pass

    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


# ─────────────────────────────────────────
# /vin <VIN>
# ─────────────────────────────────────────
def cmd_vin(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        update.message.reply_text("Usage: /vin 1HGCM82633A123456")
        return

    vin = args[0].strip().upper()
    if len(vin) != 17:
        update.message.reply_text("⚠️ VIN must be exactly 17 characters.")
        return

    update.message.reply_text(f"🔍 Looking up VIN: {vin}...")

    try:
        res = backend_post("vin_lookup", session_id(update.message.chat_id), json={"vin": vin})
        v   = res.get("vehicle", {})

        def fmt(val):
            return str(val) if val and val != "N/A" else "—"

        cached = " ⚡ (cached)" if res.get("cached") else ""
        lines  = [
            f"🚗 VIN REPORT{cached}",
            "─" * 30,
            f"VIN:          {fmt(v.get('vin'))}",
            f"Make:         {fmt(v.get('make'))}",
            f"Model:        {fmt(v.get('model'))}",
            f"Year:         {fmt(v.get('year'))}",
            f"Trim:         {fmt(v.get('trim'))}",
            f"Body:         {fmt(v.get('body_class'))}",
            f"Engine:       {fmt(v.get('engine'))} L",
            f"Cylinders:    {fmt(v.get('cylinders'))}",
            f"Fuel:         {fmt(v.get('fuel_type'))}",
            f"Drive:        {fmt(v.get('drive_type'))}",
            f"Transmission: {fmt(v.get('transmission'))}",
            f"Assembly:     {fmt(v.get('plant_country'))}",
            "",
        ]

        recall_count = v.get("recall_count", 0)
        if recall_count == 0:
            lines.append("✅ No recalls found for this vehicle.")
        else:
            lines.append(f"⚠️ {recall_count} RECALL(S) FOUND:")
            for rec in v.get("recalls", []):
                lines.append(f"\n🔧 {rec.get('component','')}")
                lines.append(f"   {rec.get('summary','')[:150]}")

        safe_reply(update, "\n".join(lines))

    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


# ─────────────────────────────────────────
# /negotiate — Negotiation email
# /script    — Negotiation talking script
# ─────────────────────────────────────────
def _run_negotiate(update: Update, context: CallbackContext, neg_type: str):
    chat_id = update.message.chat_id
    store   = get_store(chat_id)

    if not store["contract_text"]:
        update.message.reply_text("📎 Please upload your contract PDF first.")
        return

    if not store["sla"]:
        update.message.reply_text("⏳ Extracting contract terms first...")
        try:
            res = backend_post("extract_sla", session_id(chat_id), json={
                "text":        store["contract_text"],
                "contract_id": store["contract_id"],
            })
            store["sla"] = res.get("sla", {})
        except Exception as e:
            update.message.reply_text(f"❌ Error: {e}")
            return

    concerns   = " ".join(context.args) if context.args else ""
    label      = "📧 NEGOTIATION EMAIL" if neg_type == "email" else "🎙️ NEGOTIATION SCRIPT"
    update.message.reply_text(f"✍️ Generating {neg_type}... please wait.")

    try:
        res = backend_post("negotiate", session_id(chat_id), json={
            "sla":         store["sla"],
            "concerns":    concerns or "auto-detect from contract terms",
            "type":        neg_type,
            "contract_id": store["contract_id"],
        })
        output = res.get("negotiation", "No output returned.")
        safe_reply(update, f"{label}\n{'─'*30}\n\n{output}")

    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


def cmd_negotiate(update: Update, context: CallbackContext):
    _run_negotiate(update, context, "email")


def cmd_script(update: Update, context: CallbackContext):
    _run_negotiate(update, context, "script")


# ─────────────────────────────────────────
# /price <Year> <Make> <Model>
# ─────────────────────────────────────────
def cmd_price(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 3:
        update.message.reply_text("Usage: /price 2023 Toyota Camry")
        return

    year  = args[0]
    make  = args[1]
    model = " ".join(args[2:])

    update.message.reply_text(f"🔍 Looking up {year} {make} {model} via NHTSA...")

    try:
        # Use NHTSA directly (no separate price endpoint needed)
        r = requests.get(
            f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformakeyear/make/{make}/modelyear/{year}?format=json",
            timeout=15
        )
        results = r.json().get("Results", [])
        models  = [x.get("Model_Name","") for x in results if x.get("Model_Name")]

        lines = [
            f"🚗 {year} {make} {model}",
            "─" * 30,
        ]

        if models:
            lines.append(f"📋 NHTSA confirmed models: {', '.join(models[:8])}")
        else:
            lines.append("⚠️ No NHTSA data found for this make/year.")

        lines += [
            "",
            "💡 Price guidance:",
            "   • Check Edmunds.com or TrueCar.com for live market pricing",
            "   • NHTSA does not provide pricing data (free public API)",
            "   • Compare the dealer's offer to the market average before signing",
        ]

        update.message.reply_text("\n".join(lines))

    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


# ─────────────────────────────────────────
# /history — Past contracts from MySQL
# ─────────────────────────────────────────
def cmd_history(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text("📂 Fetching your contract history from database...")

    try:
        res     = backend_get("history", session_id(chat_id))
        history = res.get("history", [])

        if not history:
            update.message.reply_text("No contracts found. Upload a PDF to get started!")
            return

        lines = ["📂 YOUR CONTRACT HISTORY", "─" * 30, ""]
        for i, item in enumerate(history, 1):
            vehicle = " ".join(filter(None, [
                item.get("vehicle_year"),
                item.get("vehicle_make"),
                item.get("vehicle_model"),
            ])) or "Unknown Vehicle"

            score = item.get("fairness_score") or "—"
            try:
                sv = float(str(score).split("/")[0])
                icon = "🟢" if sv >= 7 else "🟡" if sv >= 5 else "🔴"
            except Exception:
                icon = "⚪"

            lines += [
                f"{i}. {icon} {vehicle}",
                f"   📄 {item.get('file_name','contract.pdf')}",
                f"   📅 {item.get('uploaded_at','—')}",
                f"   💰 {item.get('monthly_payment','—')}/mo  |  APR: {item.get('apr','—')}",
                f"   ⚖️  Score: {score}",
                "",
            ]

        safe_reply(update, "\n".join(lines))

    except Exception as e:
        update.message.reply_text(f"❌ Error fetching history: {e}")


# ─────────────────────────────────────────
# /clear — Reset current session
# ─────────────────────────────────────────
def cmd_clear(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user_store[chat_id] = {
        "contract_text":  "",
        "contract_id":    None,
        "sla":            {},
        "fairness_score": None,
        "chat_history":   [],
    }
    update.message.reply_text("🗑️ Session cleared! Send a new PDF to start fresh.")


# ─────────────────────────────────────────
# Free text — Q&A about contract
# ─────────────────────────────────────────
def handle_question(update: Update, context: CallbackContext):
    chat_id  = update.message.chat_id
    store    = get_store(chat_id)
    question = update.message.text

    if not store["contract_text"]:
        update.message.reply_text(
            "📎 Please upload your lease contract PDF first.\n"
            "Then I can answer questions about it!"
        )
        return

    update.message.reply_text("💭 Thinking...")

    try:
        res = backend_post("chat", session_id(chat_id), json={
            "question":    question,
            "context":     store["contract_text"],
            "history":     store["chat_history"][-6:],
            "contract_id": store["contract_id"],
        })
        answer = res.get("response", "Sorry, I could not generate an answer.")

        # Save to history
        store["chat_history"].append({"role": "user",      "content": question})
        store["chat_history"].append({"role": "assistant", "content": answer})

        safe_reply(update, answer)

    except requests.exceptions.ConnectionError:
        update.message.reply_text("❌ Cannot connect to backend. Make sure back.py is running.")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Please set your Telegram bot token!")
        print("   Either set the TELEGRAM_TOKEN environment variable")
        print("   or replace YOUR_TELEGRAM_BOT_TOKEN_HERE in bot.py")
        return

    # Check backend is reachable
    try:
        r = requests.get(BACKEND, timeout=5)
        data = r.json()
        print(f"✅ Backend connected — model: {data.get('model')}, MySQL: {data.get('mysql')}")
    except Exception:
        print(f"⚠️  Warning: Cannot reach backend at {BACKEND}")
        print("   Make sure back.py is running before using the bot.")

    updater = Updater(TOKEN, use_context=True)
    dp      = updater.dispatcher

    dp.add_handler(CommandHandler("start",     start))
    dp.add_handler(CommandHandler("help",      help_cmd))
    dp.add_handler(CommandHandler("summary",   cmd_summary))
    dp.add_handler(CommandHandler("score",     cmd_score))
    dp.add_handler(CommandHandler("negotiate", cmd_negotiate, pass_args=True))
    dp.add_handler(CommandHandler("script",    cmd_script,    pass_args=True))
    dp.add_handler(CommandHandler("vin",       cmd_vin,       pass_args=True))
    dp.add_handler(CommandHandler("price",     cmd_price,     pass_args=True))
    dp.add_handler(CommandHandler("history",   cmd_history))
    dp.add_handler(CommandHandler("clear",     cmd_clear))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_document))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_question))

    print("\n" + "=" * 50)
    print("  🤖  CarLease AI — Telegram Bot")
    print("=" * 50)
    print("  Bot started. Press Ctrl+C to stop.\n")

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()