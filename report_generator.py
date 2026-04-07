def generate_report(results):
    report = ""

    for i, r in enumerate(results, 1):
        report += f"\nClause {i}:\n"
        report += f"{r}\n"
        report += "-"*40

    return report