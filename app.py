from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PyPDF2 import PdfReader
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

NHTSA_API_URL = "https://vpic.nhtsa.dot.gov/api"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "Server is running ✅", "timestamp": datetime.now().isoformat()})

def extract_text(file):
    """Extract text from PDF."""
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        txt = page.extract_text()
        if txt:
            text += txt
    return text

def analyze_text(text):
    """Advanced SLA extraction with AI patterns."""
    apr = re.search(r'(?:APR|annual.*?rate)[:\s]*([\d.]+)\s*%', text, re.I)
    term = re.search(r'(?:lease term|duration)[:\s]*(\d+)\s*(?:months|month)', text, re.I)
    monthly = re.search(r'(?:monthly(?:\s+)?payment|total monthly payment)[:\s]*\$?([\d,]+(?:\.\d{2})?)', text, re.I)
    down = re.search(r'(?:down\s+payment|cap\s+reduction)[:\s]*\$?([\d,]+(?:\.\d{2})?)', text, re.I)
    residual = re.search(r'(?:residual\s+value|buyout|purchase.*?price)[:\s]*\$?([\d,]+(?:\.\d{2})?)', text, re.I)
    mileage = re.search(r'(?:annual mileage allowance|miles\s+per\s+year)[:\s]*(\d+(?:,\d{3})*)', text, re.I)
    overage = re.search(r'(?:excess mileage charge)[:\s]*\$?([\d.]+)\s*(?:per|/)?\s*mile', text, re.I)
    warranty = re.search(r'(?:factory warranty|warranty period)[:\s]*([^\n]+)', text, re.I)

    return {
        "APR (%)": apr.group(1) if apr else "Not detected",
        "Lease Term (Months)": term.group(1) if term else "Not detected",
        "Monthly Payment ($)": monthly.group(1) if monthly else "Not detected",
        "Down Payment ($)": down.group(1) if down else "Not detected",
        "Residual/Buyout ($)": residual.group(1) if residual else "Not detected",
        "Annual Mileage": mileage.group(1) if mileage else "Not detected",
        "Excess Mileage ($/mile)": overage.group(1) if overage else "Not detected",
        "Warranty": warranty.group(1) if warranty else "Not detected"
    }

def generate_suggestions(data):
    """AI negotiation assistant."""
    suggestions = []
    
    try:
        apr = float(re.sub(r'[^\d.]', '', data["APR (%)"]))
        if apr > 8:
            suggestions.append("⚠️ HIGH APR: >8% is above market. Negotiate for 6-7%.")
        elif apr < 4:
            suggestions.append("✅ Excellent APR: <4% is a strong deal.")
        else:
            suggestions.append("✅ Fair APR: 4-8% range is typical.")
    except:
        pass
    
    try:
        term = int(re.sub(r'[^\d]', '', data["Lease Term (Months)"]))
        if term > 60:
            suggestions.append("⚠️ Long term: Consider shorter commitment (36-48 months) to reduce total cost.")
        elif term < 24:
            suggestions.append("⚠️ Short term: Negotiate for longer to reduce monthly payment.")
    except:
        pass
    
    try:
        mileage = int(re.sub(r'[^\d]', '', data["Annual Mileage"]))
        if mileage < 10000:
            suggestions.append("⚠️ Low mileage (<10k/year). Negotiate increase or plan for overage charges.")
        elif mileage >= 15000:
            suggestions.append("✅ Excellent mileage allowance (>15k/year).")
    except:
        pass
    
    return suggestions if suggestions else ["ℹ️ Unable to fully analyze contract. Please review document."]

def calculate_fairness_score(sla_data):
    """Contract fairness scoring."""
    score = 50
    bonuses = []
    penalties = []
    
    try:
        apr = float(re.sub(r'[^\\d.]', '', sla_data["APR (%)"]))
        if apr <= 4:
            score += 20
            bonuses.append("Low APR")
        elif apr > 10:
            score -= 20
            penalties.append("High APR")
    except:
        pass
    
    try:
        mileage = int(re.sub(r'[^\d]', '', sla_data["Annual Mileage"]))
        if mileage >= 15000:
            score += 15
            bonuses.append("High mileage allowance")
        elif mileage < 8000:
            score -= 15
            penalties.append("Low mileage allowance")
    except:
        pass
    
    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C",
        "bonuses": bonuses,
        "penalties": penalties
    }

def lookup_vin(vin):
    """NHTSA VIN lookup."""
    try:
        url = f"{NHTSA_API_URL}/vehicles/DecodeVin/{vin}"
        response = requests.get(url, params={"format": "json"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('Results'):
                results = {item['Variable']: item['Value'] for item in data['Results']}
                return {
                    "Make": results.get('Make', 'N/A'),
                    "Model": results.get('Model', 'N/A'),
                    "Year": results.get('Model Year', 'N/A'),
                    "Body Style": results.get('Body Class', 'N/A')
                }
    except Exception as e:
        print(f"VIN error: {e}")
    
    return {"error": "VIN lookup failed"}

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "PDF only"}), 400
    
    try:
        text = extract_text(file)
        sla = analyze_text(text)
        suggestions = generate_suggestions(sla)
        fairness = calculate_fairness_score(sla)
        
        return jsonify({
            "sla": sla,
            "suggestions": suggestions,
            "fairness_score": fairness,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/vin-lookup', methods=['POST'])
def vin_lookup_route():
    data = request.get_json()
    vin = data.get('vin', '').strip().upper()
    
    if not vin or len(vin) != 17:
        return jsonify({"error": "Invalid VIN"}), 400
    
    return jsonify(lookup_vin(vin))

@app.route('/api/negotiation-tips', methods=['POST'])
def negotiation_tips():
    tips = [
        "Request APR reduction by mentioning competitor rates.",
        "Ask about manufacturer incentives or rebates.",
        "Negotiate mileage allowance before signing.",
        "Inquire about warranty extension options.",
        "Request waiver of documentation fees.",
        "Negotiate maintenance plan.",
        "Ask about early termination options."
    ]
    return jsonify({"tips": tips})

if __name__ == '__main__':
    app.run(debug=True, port=5000)