import os
from groq import Groq

# Get API key from environment variable
api_key = os.getenv("GROQ_API_KEY")

# Debug (remove later)
print("DEBUG API KEY:", api_key)

# Create client only if key exists
client = Groq(api_key=api_key) if api_key else None


# 🔹 Rule-based fallback
def rule_based(clause):
    clause = clause.lower()

    if "interest" in clause:
        return "⚠ Risk: Interest rate may increase\n💡 Suggestion: Ask for fixed interest rate"

    elif "penal" in clause:
        return "⚠ Risk: High penalty charges\n💡 Suggestion: Negotiate lower penalty"

    elif "possession" in clause:
        return "⚠ Risk: Bank can seize your vehicle\n💡 Suggestion: Ask for prior notice"

    elif "prepayment" in clause:
        return "⚠ Risk: Prepayment charges applied\n💡 Suggestion: Ask for zero prepayment penalty"

    else:
        return "✅ No major risk detected"


# 🔹 Main function
def analyze_clause(clause):
    prompt = f"""
    You are an AI assistant for analyzing car loan contracts.

    Analyze the clause and provide:

    1. Risk (short)
    2. Explanation (simple English)
    3. Negotiation suggestion

    Clause:
    {clause}
    """

    # If API key missing
    if client is None:
        return f"{rule_based(clause)}\n\n(⚠ API key not found)"

    try:
        response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    model="llama-3.1-8b-instant"
)

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠ ERROR: {str(e)}\n\n{rule_based(clause)}"