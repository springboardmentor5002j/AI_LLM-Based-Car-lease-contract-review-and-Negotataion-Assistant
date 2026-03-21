from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
import json
import google.generativeai as genai
from vin import lookup_vin

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = "AIzaSyDaqsfELb7MKdpq5omeDlfAPeAdwRaqDf4"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

explanations = {
    "apr_percent": "APR is the yearly interest charged on the loan.",
    "term_months": "Term is the length of the loan or lease in months.",
    "monthly_payment": "Monthly Payment is what you pay each month.",
    "down_payment": "Down Payment is the upfront amount at the start.",
    "residual_value": "Residual Value is the car worth at lease end.",
    "mileage_allowance": "Maximum miles per year without penalty.",
    "mileage_overage_fee": "Charge per extra mile over the limit.",
    "early_termination_fee": "Penalty for ending the contract early.",
    "purchase_option_price": "Buyout price at lease end.",
    "insurance_requirements": "Insurance coverage you must maintain.",
    "maintenance_responsibilities": "Who handles servicing and repairs.",
    "warranty_summary": "What parts or services are covered.",
    "late_fee_policy": "Penalty for missing a payment."
}

@app.post("/upload-contract")
async def upload_contract(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        reader = PyPDF2.PdfReader(io.BytesIO(contents))
        text = ""
        for page in reader.pages:
            text += page.extract_text()

        prompt = f"""Extract these fields from this car lease or loan contract.
Return ONLY a valid JSON object with these exact keys.
If a field is not found, use null.

Keys:
apr_percent, term_months, monthly_payment, down_payment,
residual_value, mileage_allowance, mileage_overage_fee,
early_termination_fee, purchase_option_price,
insurance_requirements, maintenance_responsibilities,
warranty_summary, late_fee_policy

Contract text:
{text[:4000]}

Return only JSON. No explanation. No markdown. No backticks."""

        response = model.generate_content(prompt)
        raw = response.text.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        extracted = json.loads(clean)

        result = {
            k: {
                "value": str(v) if v else None,
                "explanation": explanations.get(k, "")
            }
            for k, v in extracted.items()
        }
        return {"status": "success", "sla_fields": result}

    except Exception as e:
        print(f"ERROR: {e}")
        return {"status": "error", "message": str(e), "sla_fields": {}}


@app.get("/vin/{vin}")
def vin_lookup(vin: str):
    vehicle_info = lookup_vin(vin)
    return {"status": "success", "vehicle_info": vehicle_info}


@app.get("/")
def root():
    return {"message": "Car Lease API is running!"}