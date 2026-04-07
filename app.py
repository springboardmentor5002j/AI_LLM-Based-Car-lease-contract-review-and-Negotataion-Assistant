import streamlit as st

from modules.pdf_extractor import extract_text
from modules.text_cleaner import clean_text
from modules.clause_splitter import split_clauses
from modules.ai_engine import analyze_clause

st.set_page_config(page_title="Car Loan AI Assistant", layout="wide")

st.title("🚗 Car Loan Contract AI Assistant")
st.write("Upload your loan agreement and get risk analysis + negotiation tips.")

uploaded_file = st.file_uploader("Upload Contract PDF", type=["pdf"])

if uploaded_file:
    st.success("File uploaded successfully!")

    text = extract_text(uploaded_file)
    clean = clean_text(text)
    clauses = split_clauses(clean)

    st.write(f"📄 Total Clauses Found: {len(clauses)}")

    if st.button("Analyze Contract"):
        st.subheader("📊 AI Analysis")

        for i, clause in enumerate(clauses[:10]):  # limit for speed
            with st.expander(f"Clause {i+1}"):

                st.write("📜 Clause Text:")
                st.write(clause[:300] + "...")

                result = analyze_clause(clause)

                st.write("🤖 Analysis:")
                st.write(result)

                st.markdown("---")