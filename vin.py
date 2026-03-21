import requests

def lookup_vin(vin: str):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    response = requests.get(url)
    data = response.json()
    vehicle_info = {"make": None, "model": None, "year": None}
    for item in data["Results"]:
        if item["Variable"] == "Make":
            vehicle_info["make"] = item["Value"]
        elif item["Variable"] == "Model":
            vehicle_info["model"] = item["Value"]
        elif item["Variable"] == "Model Year":
            vehicle_info["year"] = item["Value"]
    return vehicle_info