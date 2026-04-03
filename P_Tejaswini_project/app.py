from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2, re, requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------- Extract Text ----------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "".join([p.extract_text() or "" for p in reader.pages])

# ---------- Extract SLA ----------
def extract_sla(text):
    def find(p): 
        m = re.search(p, text, re.I)
        return m.group(1) if m else None

    return {
        "apr": find(r"(\d+\.?\d*)\s*%"),
        "term": find(r"(\d+)\s*months"),
        "monthly": find(r"Monthly.*?(\d+)"),
        "down": find(r"Down.*?(\d+)"),
        "mileage": find(r"Mileage.*?(\d+)")
    }

# ---------- Suggestions ----------
def get_suggestions(sla):
    suggestions = []

    if sla.get("apr") and float(sla["apr"]) > 7:
        suggestions.append("APR is high. Try negotiating a lower interest rate.")

    if sla.get("term") and int(sla["term"]) > 60:
        suggestions.append("Long loan term. Consider reducing duration.")

    return suggestions

# ---------- Routes ----------
@app.route("/")
def home():
    return "Backend running 🚀"

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["file"]

    text = extract_text(file)
    sla = extract_sla(text)

    # VIN API
    vin = "1HGCM82633A004352"
    res = requests.get(
        f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    ).json()

    vehicle = {}
    for i in res["Results"]:
        if i["Variable"] in ["Make", "Model", "Model Year"]:
            vehicle[i["Variable"]] = i["Value"]

    suggestions = get_suggestions(sla)

    return jsonify({
        "sla": sla,
        "vehicle": vehicle,
        "suggestions": suggestions
    })

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)