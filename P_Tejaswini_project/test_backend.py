"""
Quick test script for the backend API
Verify that the Flask backend is working correctly
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed!\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_analyze_mock():
    """Test analyze endpoint with mock PDF text"""
    print("Testing analyze endpoint with mock data...")
    print("Note: You can upload an actual PDF file to test.\n")
    
    # Create a mock PDF-like file for testing
    sample_text = """
    Car Lease Agreement
    
    APR: 3.5%
    Lease Term: 36 months
    Monthly Payment: $450
    Down Payment: $3000
    Annual Mileage: 12000 miles
    VIN: 1HGCM82633A004352
    """
    
    print("Mock contract data:")
    print(sample_text)
    print("\nTo test with real PDF:")
    print("1. Prepare a lease contract PDF")
    print("2. Upload using the Flutter app")
    print("3. Or use: curl -F 'file=@contract.pdf' http://127.0.0.1:5000/analyze\n")

if __name__ == "__main__":
    print("=" * 50)
    print("Car Lease Analyzer - Backend Test")
    print("=" * 50 + "\n")
    
    test_health()
    test_analyze_mock()
    
    print("=" * 50)
    print("To run the full app:")
    print("1. Backend: python app.py")
    print("2. Frontend: cd frontend_app && flutter run -d chrome")
    print("=" * 50)
