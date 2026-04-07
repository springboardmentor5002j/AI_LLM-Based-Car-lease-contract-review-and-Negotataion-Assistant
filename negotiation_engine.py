def generate_suggestions(risks):
    suggestions = []

    for r in risks:
        if "Interest" in r:
            suggestions.append("Ask for fixed interest rate")

        if "Penalty" in r:
            suggestions.append("Negotiate lower penalty")

        if "Vehicle" in r:
            suggestions.append("Ask for prior notice before seizure")

    return suggestions