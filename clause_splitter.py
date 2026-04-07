import re

def split_clauses(text):
    clauses = re.split(r'\d+\.', text)
    return [c.strip() for c in clauses if len(c) > 50]