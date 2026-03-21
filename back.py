"""
Car Lease Contract Review & Negotiation AI Backend
Uses Ollama (llama3.2) — runs 100% locally, no API key needed.
Free NHTSA API for VIN lookups.
MySQL database for persistent storage — full schema from project PDF.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import httpx
import json
import re
import PyPDF2
import io
import os
import hashlib
from datetime import datetime

# ─────────────────────────────────────────
# MySQL Integration
# ─────────────────────────────────────────
import mysql.connector
from mysql.connector import Error

# Configure via environment variables or defaults
DB_CONFIG = {
    "host":       os.getenv("DB_HOST",     "localhost"),
    "port":       int(os.getenv("DB_PORT", 3306)),
    "user":       os.getenv("DB_USER",     "root"),
    "password":   os.getenv("DB_PASSWORD", "root"),
    "database":   os.getenv("DB_NAME",     "carlease_ai"),
    "autocommit": True,
}


def get_db():
    """Return a fresh MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Create all tables from the project schema (PDF page 10)."""
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            session_id   VARCHAR(64) UNIQUE NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS dealers (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            name         VARCHAR(255),
            address_line1 VARCHAR(255),
            address_line2 VARCHAR(255),
            city         VARCHAR(100),
            state        VARCHAR(50),
            postal_code  VARCHAR(20),
            country      VARCHAR(100),
            phone        VARCHAR(50),
            website      VARCHAR(255),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS lenders (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            name         VARCHAR(255),
            nmls_id      VARCHAR(100),
            send         VARCHAR(255),
            website      VARCHAR(255),
            phone        VARCHAR(50),
            address      VARCHAR(255),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS vehicles (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            vin          VARCHAR(17) UNIQUE,
            year         INT,
            make         VARCHAR(100),
            model        VARCHAR(100),
            trim         VARCHAR(100),
            body_class   VARCHAR(100),
            engine       VARCHAR(100),
            drivetrain   VARCHAR(100),
            fuel_type    VARCHAR(50),
            odometer_miles DECIMAL(10,2),
            color_ext    VARCHAR(50),
            color_int    VARCHAR(50),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS vehicle_recalls (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_id    INT,
            recall_number VARCHAR(100),
            issue_date    DATE,
            component     VARCHAR(255),
            summary       TEXT,
            remedy        TEXT,
            source        VARCHAR(100),
            raw           JSON,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS vehicle_reports (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_id    INT,
            provider_id   INT,
            title         VARCHAR(255),
            report_type   VARCHAR(100),
            availability  VARCHAR(100),
            url           VARCHAR(512),
            raw           JSON,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS contracts (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            user_id        INT,
            vehicle_id     INT,
            dealer_id      INT,
            lender_id      INT,
            contract_type  ENUM('lease','loan') DEFAULT 'lease',
            doc_status     ENUM('pending','processing','done','error') DEFAULT 'pending',
            dealer_offer_name VARCHAR(255),
            contract_date  DATE,
            locale         VARCHAR(20),
            currency       VARCHAR(10),
            fairness_score DECIMAL(5,2),
            red_flag_level ENUM('none','low','medium','high') DEFAULT 'none',
            notes          TEXT,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS contract_files (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            contract_id    INT NOT NULL,
            storage_url    VARCHAR(512),
            file_name      VARCHAR(255),
            mime_type      VARCHAR(100),
            page_count     INT,
            uploaded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )""",

        """CREATE TABLE IF NOT EXISTS contract_pages (
            id                INT AUTO_INCREMENT PRIMARY KEY,
            contract_file_id  INT NOT NULL,
            page_number       INT,
            ocr_text          TEXT,
            ocr_confidence    DECIMAL(5,2),
            thumbnail_url     VARCHAR(512),
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS contract_sla (
            id                         INT AUTO_INCREMENT PRIMARY KEY,
            contract_id                INT NOT NULL,
            apr_percent                DECIMAL(10,4),
            money_factor               DECIMAL(10,6),
            term_months                INT,
            monthly_payment            DECIMAL(10,2),
            down_payment               DECIMAL(10,2),
            fees_total                 DECIMAL(10,2),
            residual_value             DECIMAL(10,2),
            residual_percent_msrp      DECIMAL(5,2),
            msrp                       DECIMAL(10,2),
            cap_cost                   DECIMAL(10,2),
            cap_cost_reduction         DECIMAL(10,2),
            mileage_allowance_yr       INT,
            mileage_overage_fee        DECIMAL(8,4),
            early_termination_fee      DECIMAL(10,2),
            disposition_fee            DECIMAL(10,2),
            purchase_option_price      DECIMAL(10,2),
            insurance_requirements     TEXT,
            maintenance_requirements   TEXT,
            maintenance_resp           TEXT,
            warranty_summary           TEXT,
            late_fee_policy            TEXT,
            other_terms                JSON,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        )""",

        """CREATE TABLE IF NOT EXISTS extracted_clauses (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            contract_id      INT NOT NULL,
            clause_type      VARCHAR(100),
            page_number      INT,
            text_snippet     TEXT,
            normalized_value JSON,
            red_flag_level   ENUM('none','low','medium','high') DEFAULT 'none',
            comment          TEXT,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS negotiation_messages (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            thread_id       INT,
            sender_role     ENUM('user','assistant','dealer') DEFAULT 'user',
            body            TEXT,
            suggested_text  TEXT,
            attachments     JSON,
            sent_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS negotiation_threads (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            user_id      INT,
            contract_id  INT,
            dealer_id    INT,
            lender_id    INT,
            channel      ENUM('email','phone','chat','in_person') DEFAULT 'email',
            subject      VARCHAR(255),
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at    TIMESTAMP NULL
        )""",

        """CREATE TABLE IF NOT EXISTS price_recommendations (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            vehicle_id    INT,
            geo_postal    VARCHAR(20),
            msrp          DECIMAL(12,2),
            fair_price_low  DECIMAL(12,2),
            fair_price_high DECIMAL(12,2),
            basis         VARCHAR(100),
            methodology   TEXT,
            generated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS offer_comparisons (
            id                   INT AUTO_INCREMENT PRIMARY KEY,
            user_id              INT,
            primary_contract_id  INT,
            compared_contract_id INT,
            comparison_json      JSON,
            created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS providers (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(255),
            kind        VARCHAR(100),
            is_free     BOOLEAN DEFAULT FALSE,
            base_url    VARCHAR(255),
            notes       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS provider_credentials (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            provider_id INT,
            label       VARCHAR(100),
            config      JSON,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS integration_logs (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            provider_id     INT,
            request_path    VARCHAR(512),
            request_params  JSON,
            response_status INT,
            response_ms     INT,
            occurred_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message   TEXT
        )""",

        """CREATE TABLE IF NOT EXISTS extractions (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            contract_id     INT,
            model_name      VARCHAR(100),
            prompt_version  VARCHAR(50),
            status          ENUM('pending','running','done','error') DEFAULT 'pending',
            started_at      TIMESTAMP NULL,
            completed_at    TIMESTAMP NULL,
            raw_output      JSON,
            error_message   TEXT
        )""",

        """CREATE TABLE IF NOT EXISTS price_sources (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            price_rec_id INT,
            provider_id  INT,
            sample_size  INT,
            median_price DECIMAL(12,2),
            min_price    DECIMAL(12,2),
            max_price    DECIMAL(12,2),
            url          VARCHAR(512),
            raw          JSON
        )""",

        """CREATE TABLE IF NOT EXISTS tagging (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            tag          VARCHAR(100),
            entity_table VARCHAR(100),
            entity_id    INT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS audit_events (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            session_id   VARCHAR(64),
            entity_table VARCHAR(100),
            entity_id    INT,
            action       VARCHAR(100),
            details      JSON,
            occurred_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id)
        )""",

        # Lightweight helper table to map session -> contract quickly
        """CREATE TABLE IF NOT EXISTS session_contracts (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            session_id   VARCHAR(64) NOT NULL,
            contract_id  INT NOT NULL,
            file_name    VARCHAR(255),
            file_hash    VARCHAR(64),
            raw_text     LONGTEXT,
            page_count   INT DEFAULT 0,
            sla_json     JSON,
            uploaded_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_session (session_id)
        )""",

        """CREATE TABLE IF NOT EXISTS chat_history (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            contract_id  INT,
            session_id   VARCHAR(64),
            role         ENUM('user','assistant') NOT NULL,
            message      TEXT NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_contract (contract_id),
            INDEX idx_session  (session_id)
        )""",

        """CREATE TABLE IF NOT EXISTS vin_lookups (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            vin          VARCHAR(17) UNIQUE NOT NULL,
            result_json  JSON,
            looked_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS negotiation_outputs (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            contract_id     INT,
            output_type     ENUM('email','script') DEFAULT 'email',
            concerns        TEXT,
            generated_text  LONGTEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS analyses (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            contract_id  INT,
            analysis_text LONGTEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]

    try:
        conn = get_db()
        cur  = conn.cursor()
        for stmt in statements:
            try:
                cur.execute(stmt)
            except Error as e:
                print(f"  ⚠️  Table already exists or minor error: {e}")
        cur.close()
        conn.close()
        print("  ✅  MySQL tables initialised (full schema)")
    except Error as e:
        print(f"  ⚠️  MySQL init error: {e}")


def db_log(session_id, table, entity_id, action, details=None):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO audit_events (session_id, entity_table, entity_id, action, details) VALUES (%s,%s,%s,%s,%s)",
            (session_id, table, entity_id, action, json.dumps(details or {}))
        )
        cur.close()
        conn.close()
    except Exception:
        pass


app = Flask(__name__)
CORS(app)

OLLAMA_URL  = "http://localhost:11434/api/generate"
OLLAMA_TAGS = "http://localhost:11434/api/tags"
MODEL       = "llama3.2"


def check_ollama():
    try:
        r = requests.get(OLLAMA_TAGS, timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if not any(MODEL.split(":")[0] in m for m in models):
            raise Exception(
                f"Model '{MODEL}' not found in Ollama.\n"
                f"Run:  ollama pull {MODEL}\n"
                f"Available: {models}"
            )
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama is not running. Start with: ollama serve")


def call_ollama(system_prompt, user_prompt):
    try:
        check_ollama()
        full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>"
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": full_prompt, "stream": False,
            "options": {"temperature": 0.1, "num_predict": 1024, "top_p": 0.9}
        }, timeout=300)
        r.raise_for_status()
        return r.json()["response"].strip()
    except Exception as e:
        err = str(e)
        if "Ollama" in err or "Model" in err:
            raise
        raise Exception(f"Ollama error: {err}")


def ensure_session(session_id):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("INSERT IGNORE INTO users (session_id) VALUES (%s)", (session_id,))
        cur.close()
        conn.close()
    except Exception:
        pass


# ───────────────────────────────────────
# 1. Extract Text from PDF + persist
# ───────────────────────────────────────
@app.route("/extract_text", methods=["POST"])
def extract_text():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    session_id = request.form.get("session_id", "anonymous")
    ensure_session(session_id)
    raw_bytes = file.read()
    file_hash = hashlib.sha256(raw_bytes).hexdigest()

    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        text  = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        pages = len(pdf_reader.pages)

        contract_id = None
        try:
            conn = get_db()
            cur  = conn.cursor()
            # Insert into session_contracts helper table
            cur.execute(
                """INSERT INTO session_contracts (session_id, contract_id, file_name, file_hash, raw_text, page_count)
                   VALUES (%s, 0, %s, %s, %s, %s)""",
                (session_id, file.filename, file_hash, text, pages)
            )
            contract_id = cur.lastrowid
            # Update self-referencing contract_id
            cur.execute("UPDATE session_contracts SET contract_id=%s WHERE id=%s", (contract_id, contract_id))
            cur.close()
            conn.close()
            db_log(session_id, "session_contracts", contract_id, "upload", {"file": file.filename, "pages": pages})
        except Error as e:
            print(f"DB upload warning: {e}")

        return jsonify({"text": text, "pages": pages, "contract_id": contract_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 2. Extract SLA + persist
# ───────────────────────────────────────
@app.route("/extract_sla", methods=["POST"])
def extract_sla():
    data          = request.json
    contract_text = data.get("text", "")
    contract_id   = data.get("contract_id")
    session_id    = data.get("session_id", "anonymous")

    if not contract_text:
        return jsonify({"error": "No contract text provided"}), 400

    system = """You are an expert automotive finance attorney.
Extract key terms from car lease/loan contracts.
Respond with ONLY a valid JSON object. No markdown, no backticks, no extra text."""

    user = f"""Extract these fields. Return ONLY raw JSON (use null if not found):
{{
  "apr": null, "lease_term_months": null, "monthly_payment": null,
  "down_payment": null, "residual_value": null, "mileage_allowance_per_year": null,
  "mileage_overage_fee": null, "early_termination_fee": null,
  "purchase_option_price": null, "disposition_fee": null, "acquisition_fee": null,
  "money_factor": null, "vehicle_make": null, "vehicle_model": null,
  "vehicle_year": null, "vin": null, "dealer_name": null, "lender_name": null,
  "maintenance_responsibilities": null, "insurance_requirements": null,
  "late_fee": null, "warranty_summary": null, "red_flags": [], "fairness_score": null
}}
CONTRACT TEXT: {contract_text[:2000]}
IMPORTANT: Output ONLY the JSON. Nothing else."""

    try:
        result = call_ollama(system, user)
        result = re.sub(r"```json|```", "", result).strip()
        start  = result.find("{")
        end    = result.rfind("}") + 1
        if start != -1 and end > start:
            result = result[start:end]
        parsed = json.loads(result)

        # Persist SLA JSON into session_contracts
        if contract_id:
            try:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute(
                    "UPDATE session_contracts SET sla_json=%s WHERE id=%s",
                    (json.dumps(parsed), contract_id)
                )
                # Also insert into contract_sla (canonical table)
                def safe_decimal(v):
                    if v is None: return None
                    try: return float(str(v).replace("$","").replace(",","").replace("%","").strip())
                    except: return None
                def safe_int(v):
                    if v is None: return None
                    try: return int(str(v).replace(",","").strip())
                    except: return None

                cur.execute(
                    """INSERT INTO contract_sla
                       (contract_id, apr_percent, money_factor, term_months, monthly_payment,
                        down_payment, residual_value, mileage_allowance_yr, mileage_overage_fee,
                        early_termination_fee, disposition_fee, purchase_option_price,
                        insurance_requirements, maintenance_requirements, warranty_summary,
                        other_terms)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        contract_id,
                        safe_decimal(parsed.get("apr")),
                        safe_decimal(parsed.get("money_factor")),
                        safe_int(parsed.get("lease_term_months")),
                        safe_decimal(parsed.get("monthly_payment")),
                        safe_decimal(parsed.get("down_payment")),
                        safe_decimal(parsed.get("residual_value")),
                        safe_int(parsed.get("mileage_allowance_per_year")),
                        safe_decimal(parsed.get("mileage_overage_fee")),
                        safe_decimal(parsed.get("early_termination_fee")),
                        safe_decimal(parsed.get("disposition_fee")),
                        safe_decimal(parsed.get("purchase_option_price")),
                        parsed.get("insurance_requirements"),
                        parsed.get("maintenance_responsibilities"),
                        parsed.get("warranty_summary"),
                        json.dumps({k: parsed.get(k) for k in ("dealer_name","lender_name","late_fee","vehicle_make","vehicle_model","vehicle_year","vin","acquisition_fee","red_flags","fairness_score")}),
                    )
                )
                cur.close()
                conn.close()
                db_log(session_id, "contract_sla", contract_id, "extract", {"score": parsed.get("fairness_score")})
            except Error as e:
                print(f"DB SLA warning: {e}")

        return jsonify({"sla": parsed})
    except json.JSONDecodeError:
        return jsonify({"sla": {}, "raw": result, "error": "Could not parse JSON"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 3. Fairness Analysis + persist
# ───────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze_contract():
    data          = request.json
    contract_text = data.get("text", "")
    sla           = data.get("sla", {})
    contract_id   = data.get("contract_id")
    session_id    = data.get("session_id", "anonymous")

    system = """You are a consumer protection expert specializing in automotive finance.
Give clear, honest, actionable analysis. Prioritize the consumer's interests."""

    user = f"""Analyze this car contract:

## 1. Overall Assessment (2-3 sentences)
## 2. Top 3 Concerns (with amounts)
## 3. Top 3 Strengths
## 4. Negotiation Opportunities
## 5. Red Flags
## 6. Recommendation: SIGN AS-IS / NEGOTIATE FIRST / WALK AWAY

Extracted terms: {json.dumps(sla, indent=2)}
Contract text: {contract_text[:2000]}"""

    try:
        result = call_ollama(system, user)
        if contract_id:
            try:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute("INSERT INTO analyses (contract_id, analysis_text) VALUES (%s,%s)", (contract_id, result))
                cur.close()
                conn.close()
            except Error as e:
                print(f"DB analysis warning: {e}")
        return jsonify({"analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 4. Chat + persist history
# ───────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data          = request.json
    question      = data.get("question", "")
    contract_text = data.get("context", "")
    chat_history  = data.get("history", [])
    contract_id   = data.get("contract_id")
    session_id    = data.get("session_id", "anonymous")

    system = """You are a helpful car lease advisor. Be specific and concise (3-5 sentences)."""

    history_text = ""
    for msg in chat_history[-4:]:
        role    = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if "Question:" in content:
            content = content.split("Question:")[-1].strip()
        history_text += f"{role}: {content}\n"

    user = f"""Contract: {contract_text[:2000]}
{f'Previous: {chr(10)}{history_text}' if history_text else ''}
Question: {question}
Answer:"""

    try:
        result = call_ollama(system, user)
        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("INSERT INTO chat_history (contract_id, session_id, role, message) VALUES (%s,%s,%s,%s)", (contract_id, session_id, "user", question))
            cur.execute("INSERT INTO chat_history (contract_id, session_id, role, message) VALUES (%s,%s,%s,%s)", (contract_id, session_id, "assistant", result))
            cur.close()
            conn.close()
        except Error as e:
            print(f"DB chat warning: {e}")
        return jsonify({"response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 5. VIN Lookup + DB cache
# ───────────────────────────────────────
@app.route("/vin_lookup", methods=["POST"])
def vin_lookup():
    data = request.json
    vin  = data.get("vin", "").strip().upper()
    if not vin or len(vin) != 17:
        return jsonify({"error": "Invalid VIN — must be 17 characters"}), 400

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT result_json FROM vin_lookups WHERE vin=%s", (vin,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return jsonify({"vehicle": row["result_json"], "cached": True})
    except Exception:
        pass

    try:
        r = httpx.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json", timeout=30)
        results = {item["Variable"]: item["Value"] for item in r.json().get("Results", []) if item.get("Value") and item["Value"] not in ["null", "Not Applicable", ""]}
        vehicle_info = {
            "vin": vin, "make": results.get("Make","N/A"), "model": results.get("Model","N/A"),
            "year": results.get("Model Year","N/A"), "trim": results.get("Trim","N/A"),
            "body_class": results.get("Body Class","N/A"), "engine": results.get("Displacement (L)","N/A"),
            "cylinders": results.get("Engine Number of Cylinders","N/A"),
            "fuel_type": results.get("Fuel Type - Primary","N/A"), "drive_type": results.get("Drive Type","N/A"),
            "transmission": results.get("Transmission Style","N/A"), "plant_country": results.get("Plant Country","N/A"),
            "series": results.get("Series","N/A"), "doors": results.get("Doors","N/A"),
        }
        recall_r = httpx.get(f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={vehicle_info['make']}&model={vehicle_info['model']}&modelYear={vehicle_info['year']}", timeout=30)
        recalls = recall_r.json().get("results", [])
        vehicle_info["recall_count"] = len(recalls)
        vehicle_info["recalls"] = [{"component": rec.get("Component",""), "summary": rec.get("Summary","")[:200], "consequence": rec.get("Consequence","")[:200]} for rec in recalls[:5]]

        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute("INSERT INTO vin_lookups (vin, result_json) VALUES (%s,%s) ON DUPLICATE KEY UPDATE result_json=%s, looked_up_at=NOW()", (vin, json.dumps(vehicle_info), json.dumps(vehicle_info)))
            cur.close()
            conn.close()
        except Exception:
            pass

        return jsonify({"vehicle": vehicle_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 6. Negotiation + persist
# ───────────────────────────────────────
@app.route("/negotiate", methods=["POST"])
def negotiate():
    data             = request.json
    sla              = data.get("sla", {})
    concerns         = data.get("concerns", "")
    negotiation_type = data.get("type", "email")
    contract_id      = data.get("contract_id")

    system = "You are an expert automotive negotiation coach."

    if negotiation_type == "email":
        user = f"""Write a professional negotiation email to the dealer.
Contract terms: {json.dumps(sla, indent=2)}
Concerns: {concerns or "identify the worst terms automatically"}
Requirements: Subject line, professional but firm tone, reference specific amounts, request 2-3 changes, clear call to action."""
    else:
        user = f"""Write a negotiation script for talking to the dealer.
Contract terms: {json.dumps(sla, indent=2)}
Concerns: {concerns or "auto-detect"}
Sections: 1. Opening  2-4. Issue + counter-offer  5. Handling pushback  6. Walk-away line"""

    try:
        result = call_ollama(system, user)
        if contract_id:
            try:
                conn = get_db()
                cur  = conn.cursor()
                cur.execute("INSERT INTO negotiation_outputs (contract_id, output_type, concerns, generated_text) VALUES (%s,%s,%s,%s)", (contract_id, negotiation_type, concerns, result))
                cur.close()
                conn.close()
            except Error as e:
                print(f"DB negotiation warning: {e}")
        return jsonify({"negotiation": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 7. Compare Contracts + persist
# ───────────────────────────────────────
@app.route("/compare", methods=["POST"])
def compare_contracts():
    data       = request.json
    sla1       = data.get("sla1", {})
    sla2       = data.get("sla2", {})
    label1     = data.get("label1", "Contract A")
    label2     = data.get("label2", "Contract B")
    session_id = data.get("session_id", "anonymous")
    cid1       = data.get("contract_id_1")
    cid2       = data.get("contract_id_2")

    system = "You are an automotive finance expert. Compare contracts clearly."
    user = f"""Compare these two contracts.
{label1}: {json.dumps(sla1, indent=2)}
{label2}: {json.dumps(sla2, indent=2)}
Provide: 1. Table (Term | {label1} | {label2} | Winner)  2. Total cost comparison  3. Better deal  4. Recommendation"""

    try:
        result = call_ollama(system, user)
        try:
            conn = get_db()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO offer_comparisons (user_id, primary_contract_id, compared_contract_id, comparison_json) VALUES (0,%s,%s,%s)",
                (cid1, cid2, json.dumps({"sla1": sla1, "sla2": sla2, "result": result}))
            )
            cur.close()
            conn.close()
        except Error as e:
            print(f"DB compare warning: {e}")
        return jsonify({"comparison": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ───────────────────────────────────────
# 8. NEW — Contract History
# ───────────────────────────────────────
@app.route("/history", methods=["GET"])
def get_history():
    session_id = request.args.get("session_id", "anonymous")
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT id, file_name, page_count, uploaded_at,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.vehicle_make'))  AS vehicle_make,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.vehicle_model')) AS vehicle_model,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.vehicle_year'))  AS vehicle_year,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.monthly_payment')) AS monthly_payment,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.apr'))           AS apr,
                      JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.fairness_score')) AS fairness_score
               FROM session_contracts
               WHERE session_id=%s
               ORDER BY uploaded_at DESC LIMIT 20""",
            (session_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for row in rows:
            if row.get("uploaded_at"):
                row["uploaded_at"] = row["uploaded_at"].strftime("%Y-%m-%d %H:%M")
        return jsonify({"history": rows})
    except Exception as e:
        return jsonify({"history": [], "error": str(e)})


# ───────────────────────────────────────
# 9. NEW — Analytics
# ───────────────────────────────────────
@app.route("/analytics", methods=["GET"])
def get_analytics():
    session_id = request.args.get("session_id", "anonymous")
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        stats = {}

        cur.execute("SELECT COUNT(*) AS cnt FROM session_contracts WHERE session_id=%s", (session_id,))
        stats["total_contracts"] = (cur.fetchone() or {}).get("cnt", 0)

        cur.execute("SELECT COUNT(*) AS cnt FROM chat_history WHERE session_id=%s", (session_id,))
        stats["total_chats"] = (cur.fetchone() or {}).get("cnt", 0)

        cur.execute("SELECT COUNT(*) AS cnt FROM negotiation_outputs no2 JOIN session_contracts sc ON no2.contract_id=sc.id WHERE sc.session_id=%s", (session_id,))
        stats["total_negotiations"] = (cur.fetchone() or {}).get("cnt", 0)

        cur.execute("SELECT COUNT(*) AS cnt FROM vin_lookups")
        stats["total_vin_lookups"] = (cur.fetchone() or {}).get("cnt", 0)

        cur.execute(
            """SELECT JSON_UNQUOTE(JSON_EXTRACT(sla_json,'$.fairness_score')) AS fairness_score,
                      file_name, uploaded_at
               FROM session_contracts
               WHERE session_id=%s AND sla_json IS NOT NULL
               ORDER BY uploaded_at DESC LIMIT 5""",
            (session_id,)
        )
        stats["recent_scores"] = cur.fetchall()
        for row in stats["recent_scores"]:
            if row.get("uploaded_at"):
                row["uploaded_at"] = row["uploaded_at"].strftime("%Y-%m-%d")

        cur.close()
        conn.close()
        return jsonify({"analytics": stats})
    except Exception as e:
        return jsonify({"analytics": {}, "error": str(e)})


# ───────────────────────────────────────
# Health Check
# ───────────────────────────────────────
@app.route("/")
def home():
    try:
        check_ollama()
        ollama_status = "connected"
    except Exception as e:
        ollama_status = str(e)

    try:
        conn = get_db()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = str(e)

    return jsonify({"status": "running", "model": MODEL, "ollama": ollama_status, "mysql": db_status})


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🚗  CarLease AI — Backend (MySQL + Ollama)")
    print("=" * 60)

    try:
        init_db()
    except Exception as e:
        print(f"  ⚠️  DB init skipped: {e}")

    try:
        check_ollama()
        print(f"  ✅  Ollama connected — model: {MODEL}")
    except Exception as e:
        print(f"  ❌  {e}")

    print(f"\n  🚀  Starting on http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)