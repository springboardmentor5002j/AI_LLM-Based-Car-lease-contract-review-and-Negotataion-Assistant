def detect_keywords(clause):
    risks = []

    if "interest" in clause:
        risks.append("Interest Risk")

    if "penal" in clause:
        risks.append("Penalty Risk")

    if "possession" in clause:
        risks.append("Vehicle Seizure Risk")

    return risks