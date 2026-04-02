from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import re
import requests

app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "AI Contract Analyzer Backend Running"}


@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    reader = PyPDF2.PdfReader(file.file)

    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted

    sla_fields = {
        "apr_percent": None,
        "term_months": None,
        "monthly_payment": None,
        "down_payment": None
    }

    # APR
    apr_match = re.search(
        r"(APR|Interest Rate|Annual Percentage Rate)[^\d]{0,10}([\d]{1,2}\.?[\d]{0,2})",
        text,
        re.IGNORECASE
    )

    if apr_match:
        sla_fields["apr_percent"] = apr_match.group(2)

    # Term
    term_match = re.search(
        r"(\d+)\s*(months|month)",
        text,
        re.IGNORECASE
    )

    if term_match:
        sla_fields["term_months"] = term_match.group(1)

    # Monthly payment
    payment_match = re.search(
        r"(Monthly Payment|Payment Amount|Installment)[^\d]*([\d,\.]+)",
        text,
        re.IGNORECASE
    )

    if payment_match:
        sla_fields["monthly_payment"] = payment_match.group(2)

    # Down payment
    down_match = re.search(
        r"(Down Payment|Initial Payment|Advance Payment)[^\d]*([\d,\.]+)",
        text,
        re.IGNORECASE
    )

    if down_match:
        sla_fields["down_payment"] = down_match.group(2)

    # -------- VIN Detection --------

    vin_match = re.search(
        r"\b[A-HJ-NPR-Z0-9]{17}\b",
        text
    )

    vehicle_info = {
        "make": None,
        "model": None,
        "year": None
    }

    if vin_match:

        vin = vin_match.group(0)

        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"

        response = requests.get(url)

        data = response.json()

        for item in data["Results"]:
            if item["Variable"] == "Make":
                vehicle_info["make"] = item["Value"]

            if item["Variable"] == "Model":
                vehicle_info["model"] = item["Value"]

            if item["Variable"] == "Model Year":
                vehicle_info["year"] = item["Value"]

    # -------- Negotiation --------

    negotiation_points = []

    if sla_fields["apr_percent"]:
        apr = float(sla_fields["apr_percent"])

        if apr > 7:
            negotiation_points.append(
                f"APR {apr}% is higher than typical market rates."
            )
        else:
            negotiation_points.append(
                f"APR {apr}% is within a reasonable market range."
            )

    # -------- Summary --------

    summary = []

    if sla_fields["apr_percent"]:
        summary.append(f"The contract APR is {sla_fields['apr_percent']}%.")

    if sla_fields["term_months"]:
        summary.append(f"The loan term is {sla_fields['term_months']} months.")

    summary_text = " ".join(summary)

    return {
        "contract_details": sla_fields,
        "vehicle_info": vehicle_info,
        "negotiation_suggestions": negotiation_points,
        "summary": summary_text
    }