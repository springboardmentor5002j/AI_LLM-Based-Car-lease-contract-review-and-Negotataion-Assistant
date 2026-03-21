import re

def extract_sla_fields(text):
    sla_fields = {
        "apr_percent": None,
        "term_months": None,
        "monthly_payment": None,
        "down_payment": None,
        "residual_value": None,
        "mileage_allowance": None,
        "mileage_overage_fee": None,
        "early_termination_fee": None,
        "purchase_option_price": None,
        "insurance_requirements": None,
        "maintenance_responsibilities": None,
        "warranty_summary": None,
        "late_fee_policy": None
    }

    # APR
    apr = re.search(r"(APR|Annual Percentage Rate|Interest Rate)[^\d]*([\d\.]+)", text, re.IGNORECASE)
    if apr:
        sla_fields["apr_percent"] = apr.group(2)

    # Monthly Payment
    monthly = re.search(r"(Monthly Payment|Payment Amount)[^\d]*\$?([\d,\.]+)", text, re.IGNORECASE)
    if monthly:
        sla_fields["monthly_payment"] = monthly.group(2)

    # Term months
    term = re.search(r"(\d+)\s*(months|month term)", text, re.IGNORECASE)
    if term:
        sla_fields["term_months"] = term.group(1)

    # Down payment
    down = re.search(r"(Down Payment|Initial Payment)[^\d]*\$?([\d,\.]+)", text, re.IGNORECASE)
    if down:
        sla_fields["down_payment"] = down.group(2)

    # Residual value
    residual = re.search(r"(Residual Value|End Value)[^\d]*\$?([\d,\.]+)", text, re.IGNORECASE)
    if residual:
        sla_fields["residual_value"] = residual.group(2)

    # Mileage allowance
    mileage = re.search(r"(Mileage Allowance|Annual Mileage)[^\d]*(\d+)", text, re.IGNORECASE)
    if mileage:
        sla_fields["mileage_allowance"] = mileage.group(2)

    # Mileage overage fee
    overage = re.search(r"(Overage Fee|Excess Mileage)[^\d]*\$?([\d,\.]+)", text, re.IGNORECASE)
    if overage:
        sla_fields["mileage_overage_fee"] = overage.group(2)

    return sla_fields


explanations = {
    "apr_percent": "APR is the yearly interest charged on the loan.",
    "term_months": "Term is the length of the loan or lease in months.",
    "monthly_payment": "Monthly Payment is what you pay each month.",
    "down_payment": "Down Payment is the upfront amount you pay at the start.",
    "residual_value": "Residual Value is the car's worth at the end of the lease.",
    "mileage_allowance": "Mileage Allowance is the maximum miles per year without penalty.",
    "mileage_overage_fee": "Overage Fee is the charge per extra mile over the limit.",
    "early_termination_fee": "Early Termination Fee is the penalty for ending the contract early.",
    "purchase_option_price": "Purchase Option Price is the buyout price at lease end.",
    "insurance_requirements": "Insurance Requirements specify the coverage you must have.",
    "maintenance_responsibilities": "Maintenance explains who handles servicing.",
    "warranty_summary": "Warranty describes what parts or services are covered.",
    "late_fee_policy": "Late Fee Policy is the penalty for missing a payment."
}