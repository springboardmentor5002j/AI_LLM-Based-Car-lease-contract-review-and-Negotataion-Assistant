# 🚗 CarLease AI — Car Lease Contract Review & Negotiation Assistant

An AI-powered app that helps you review car lease/loan contracts, spot red flags, look up vehicle history, and generate negotiation emails — all running locally on your machine.

---

## What It Does

- **Upload a lease/loan PDF** → extracts all key terms (APR, monthly payment, mileage, fees, etc.)
- **Fairness Score** → AI rates your contract and highlights red flags
- **Chat with your contract** → ask any question in plain English
- **VIN Lookup** → free NHTSA vehicle details + recall history
- **Negotiation Helper** → auto-generates a negotiation email or talking script
- **Compare Contracts** → side-by-side comparison of two offers
- **Contract History** → all past uploads saved in MySQL, survives page refresh
- **Telegram Bot** → do everything above from your phone via Telegram

---

## Project Files

```
back.py      ← Flask backend (AI + APIs + MySQL)
front.py     ← Streamlit web interface
bot.py       ← Telegram bot
```

---

## Requirements

### 1. Python 3.8+
Download from [python.org](https://python.org)

### 2. Python packages
```bash
pip install flask flask-cors mysql-connector-python PyPDF2 requests httpx
pip install streamlit
pip install "python-telegram-bot==13.15"
```

### 3. MySQL 8.0+
- **Windows / Mac** → download from [mysql.com](https://mysql.com)
- **Ubuntu/Debian** → `sudo apt install mysql-server`
- **Mac (Homebrew)** → `brew install mysql`

Create the database after installing:
```sql
CREATE DATABASE carlease_ai;
```

### 4. Ollama (local AI — no API key needed)
- Download from [ollama.com](https://ollama.com)
- Then pull the model:
```bash
ollama pull llama3.2
```

---

## Setup

### Step 1 — Configure MySQL (optional)
By default the app connects to `localhost` with user `root` and no password.
To change this, set environment variables before running:

```bash
# Windows
set DB_HOST=localhost
set DB_USER=root
set DB_PASSWORD=yourpassword
set DB_NAME=carlease_ai

# Mac / Linux
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=yourpassword
export DB_NAME=carlease_ai
```

### Step 2 — Set Telegram Bot Token (for bot.py only)
```bash
# Windows
set TELEGRAM_TOKEN=your_token_here

# Mac / Linux
export TELEGRAM_TOKEN=your_token_here
```
> Get a token by messaging [@BotFather](https://t.me/BotFather) on Telegram.  
> Also update `TELEGRAM_BOT_USERNAME` in `front.py` to your bot's @username.

---

## Running the App

Start each part in a **separate terminal**, in this order:

```bash
# Terminal 1 — Start Ollama
ollama serve

# Terminal 2 — Start the backend
python back.py

# Terminal 3 — Start the web interface
streamlit run front.py

# Terminal 4 — Start the Telegram bot (optional)
python bot.py
```

Then open your browser at: **http://localhost:8501**

---

## How to Use

1. Open the app at `http://localhost:8501`
2. Go to **Upload & Extract** → upload your contract PDF
3. Click **Extract Key Terms** → wait 30–60 seconds
4. Go to **Analysis** → click **Run Full Analysis**
5. Use **Chat Assistant** to ask questions about your contract
6. Use **Negotiation Helper** to generate an email to your dealer
7. Use **VIN Lookup** to check vehicle history and recalls
8. Your history is saved — refresh the page and it still shows up

---

## Telegram Bot Commands

| Command | What it does |
|---|---|
| Send a PDF | Upload your contract |
| `/summary` | Extract key contract terms |
| `/score` | Get fairness score + red flags |
| `/negotiate` | Generate negotiation email |
| `/script` | Generate negotiation talking points |
| `/vin 1HGCM82633A123456` | Look up a vehicle by VIN |
| `/price 2023 Toyota Camry` | Market price info |
| `/history` | View your past contracts |
| `/clear` | Clear current contract |
| Just type a question | Ask anything about your contract |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `❌ Cannot connect to backend` | Make sure `python back.py` is running |
| `❌ Ollama is not running` | Run `ollama serve` in a terminal |
| `Model 'llama3.2' not found` | Run `ollama pull llama3.2` |
| `⚠️ MySQL: offline` | Start MySQL service, check DB_PASSWORD |
| Request timed out | Normal for large contracts — wait up to 5 minutes |
| History not showing after refresh | Check the URL has `?sid=` in it |

---

## Notes

- Everything runs **100% locally** — no data is sent to any cloud service
- The AI model (llama3.2) runs on your own computer via Ollama
- VIN lookups use the free public NHTSA API
- MySQL stores your contract history so it persists across sessions
