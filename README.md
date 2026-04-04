# 🚗 AutoFinance AI Assistant - Car Lease/Loan Contract Review Tool

A comprehensive AI-driven platform for analyzing, reviewing, and negotiating car lease and loan contracts with smart recommendations and vehicle insights.

## 📋 Project Overview

This application helps consumers:
- **Extract** key contract terms (APR, mileage, monthly payment, etc.) from PDF documents
- **Analyze** contract fairness with an AI-powered scoring system
- **Compare** offers with market benchmarks
- **Negotiate** better terms with data-driven insights
- **Lookup** vehicle details using VIN numbers

---

## ✨ Key Features

### 1. **Contract Upload & SLA Extraction**
- Upload lease/loan contract PDFs
- Automatic extraction of critical fields:
  - APR / Interest Rate
  - Lease/Loan Term
  - Monthly Payment
  - Down Payment
  - Residual/Buyout Value
  - Mileage Allowance & Overage Charges
  - Warranty & Maintenance Terms

### 2. **Contract Fairness Score**
- AI-calculated score (0-100) based on market standards
- Grade: A+ to F
- Highlights favorable terms and negotiation points
- Bonuses & Penalties breakdown

### 3. **AI Negotiation Assistant**
- Smart suggestions for each contract section
- Market comparison insights
- Specific negotiation talking points
- Cost-saving recommendations

### 4. **VIN Lookup**
- Enter 17-character VIN number
- Fetch vehicle details from NHTSA database:
  - Make, Model, Year
  - Body Style
  - Engine & Transmission Info
- Quick verification of vehicle specifications

### 5. **Negotiation Tips**
- Industry best practices
- Common negotiation strategies
- Fee waiver opportunities
- Contract optimization tactics

---

## 🛠️ Tech Stack

**Backend:**
- Python Flask 2.3+
- PyPDF2 (PDF text extraction)
- Requests (API integration)
- Flask-CORS (cross-origin support)

**Frontend:**
- HTML5 / CSS3 / JavaScript (ES6+)
- Responsive design
- Tab-based navigation
- Real-time status updates

**APIs:**
- NHTSA Vehicle API (free VIN decoding)
- RESTful endpoints

---

## 📦 Installation & Setup

### 1. **Navigate to Project**
```powershell
cd c:\Users\Kaviyashri\Documents\car_lease
```

### 2. **Activate Virtual Environment**
```powershell
.\.venv\Scripts\activate
```

### 3. **Install Dependencies**
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. **Verify Installation**
```powershell
python -c "import flask, PyPDF2; print('✅ All dependencies installed')"
```

### 5. **Run Application**
```powershell
python app.py
```

### 6. **Access Application**
Open browser: **http://127.0.0.1:5000**

---

## 📱 How to Use

### **Tab 1: Upload Contract**
1. Click "📄 Upload Contract" tab
2. Select a PDF file (lease/loan agreement)
3. Click "🔄 Analyze Contract"
4. View extracted terms, fairness score, and suggestions

### **Tab 2: VIN Lookup**
1. Click "🔍 VIN Lookup" tab
2. Enter 17-character VIN number
3. Click "🔎 Lookup"
4. View vehicle details (Make, Model, Year, etc.)

### **Tab 3: Negotiation Tips**
1. Click "💬 Negotiation Tips" tab
2. Click "💡 Get Tips"
3. Review best practices and strategies

---

## 📂 Project Structure

```
car_lease/
├── app.py                          # Flask backend (main application)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── templates/
│   └── index.html                  # Main HTML template (Flask-enabled)
└── static/
    ├── style.css                   # Professional UI styling
    └── script.js                   # Frontend logic (tabs, API calls)
```

---

## 🔌 API Endpoints

### **POST /upload**
Upload contract PDF and extract SLA terms
```bash
curl -X POST -F "file=@contract.pdf" http://127.0.0.1:5000/upload
```

### **POST /api/vin-lookup**
Lookup vehicle from VIN
```bash
curl -X POST -H "Content-Type: application/json" \\
  -d '{"vin":"1HGCV1F32LA123456"}' \\
  http://127.0.0.1:5000/api/vin-lookup
```

### **GET /api/health**
Health check
```bash
curl http://127.0.0.1:5000/api/health
```

---

## 📊 SLA Fields Extracted

| Field | Example | Use Case |
|-------|---------|----------|
| APR (%) | 6.5 | Compare interest rates |
| Lease Term | 36 months | Check commitment length |
| Monthly Payment | $425 | Budget planning |
| Down Payment | $3,000 | Initial cost |
| Residual Value | $15,000 | Buyout option |
| Mileage Allowance | 12,000/year | Usage limits |
| Excess Mileage | $0.25/mile | Overage cost |
| Warranty | Factory warranty | Coverage details |

---

## 🔧 Troubleshooting

### **ModuleNotFoundError: flask**
```powershell
python -m pip install -r requirements.txt
```

### **PDF not extracting text**
- Ensure PDF is text-based (not image scan)
- Try different PDF format

### **VIN lookup returns error**
- Check VIN format (17 chars, alphanumeric)
- Internet connection required for NHTSA API

### **App won't start**
```powershell
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Run on different port
# Edit app.py: app.run(debug=True, port=5001)
```

---

## 📈 Latest Updates (v1.0)

✅ Complete backend with Flask  
✅ Advanced SLA extraction with AI patterns  
✅ Contract fairness scoring (0-100)  
✅ VIN lookup integration with NHTSA API  
✅ AI negotiation suggestions  
✅ Professional UI with tabs and responsive design  
✅ Real-time status updates  
✅ Comprehensive API endpoints  

---

## 📝 Database Schema (Future Implementation)

```sql
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    apr FLOAT,
    term_months INTEGER,
    fairness_score INTEGER,
    uploaded_at TIMESTAMP
);

CREATE TABLE vin_lookups (
    id INTEGER PRIMARY KEY,
    vin TEXT UNIQUE,
    make TEXT,
    model TEXT,
    year INTEGER
);
```

---

## 🔐 Security Notes

- PDFs processed in-memory (not stored)
- CORS enabled for development
- Input validation on all endpoints
- No sensitive data stored locally

---

## 📚 Resources

- NHTSA API: https://vpic.nhtsa.dot.gov/api/
- Flask: https://flask.palletsprojects.com/
- PyPDF2: https://github.com/py-pdf/PyPDF2

---

**🚗 AutoFinance AI Assistant v1.0**  
_Empowering smarter car financing decisions_

## Project Structure

```
car_lease/
├── app.py                 # Main Flask application
├── reqirements.txt        # Python dependencies
├── .env                   # Environment variables
├── README.md              # This file
├── templates/
│   └── index.html         # Web interface
└── static/                # Static files (CSS, JS, images)
```

## How to Use

1. Open your browser and go to `http://localhost:5000`
2. Upload a PDF lease agreement
3. Click "Analyze Agreement"
4. View the extracted lease terms and recommendations

## Lease Term Analysis

The application extracts:
- **APR (%)**: Annual Percentage Rate
- **Term (Months)**: Lease duration in months
- **Monthly Payment**: Regular monthly payment amount
- **Down Payment**: Initial payment required
- **Mileage Allowance**: Allowed annual mileage

## Recommendations Provided

- High APR warning (> 7%)
- APR assessment (3-7% is reasonable)
- Short term notice (< 12 months)
- Low mileage allowance warning (< 12,000 miles)

## Troubleshooting

### Port 5000 already in use
```bash
python app.py --port 5001
```

### Module not found errors
Ensure virtual environment is activated and dependencies are installed:
```bash
pip install -r reqirements.txt
```

### PDF not reading correctly
- Ensure the PDF is text-based (not scanned image)
- Try re-exporting the PDF from the original source

## Technologies Used

- **Flask**: Web framework
- **Flask-CORS**: Cross-Origin Resource Sharing
- **PyPDF2**: PDF text extraction
- **HTML5/CSS3/JavaScript**: Frontend

## License

MIT License

## Support

For issues or suggestions, please create an issue in the repository.
