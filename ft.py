import streamlit as st
import pdfplumber
import pandas as pd
import os
import re

# CSV file to store transactions
CSV_FILE = "transactions.csv"

# Function to extract transactions from a PDF
def extract_transactions_from_pdf(pdf_file, bank_name):
    transactions = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    match = re.search(r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\d+\.\d{2})", line)
                    if match:
                        date, description, amount = match.groups()
                        transactions.append({
                            "Bank": bank_name,
                            "Transaction Date": pd.to_datetime(date, format="%m/%d/%Y"),
                            "Details": description.strip(),
                            "Transaction Amount": float(amount)
                        })
    return transactions

# Load existing transactions from CSV
def load_transactions():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=["Bank", "Transaction Date", "Details", "Transaction Amount"])

# Save transactions to CSV
def save_transactions(df):
    df.to_csv(CSV_FILE, index=False)

# Streamlit App UI
st.title("📊 Personal Finance Tracker")

# 📂 PDF Upload Section
st.header("Upload Bank Statements (PDF)")
uploaded_files = st.file_uploader("Choose PDFs", type=["pdf"], accept_multiple_files=True)
bank_name = st.text_input("Enter Bank Name for Uploaded PDFs")

if uploaded_files and bank_name:
    all_transactions = []
    for file in uploaded_files:
        transactions = extract_transactions_from_pdf(file, bank_name)
        all_transactions.extend(transactions)
    
    if all_transactions:
        df_new = pd.DataFrame(all_transactions)
        df_existing = load_transactions()
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        save_transactions(df_combined)
        st.success(f"✅ {len(all_transactions)} transactions extracted and saved!")
    else:
        st.warning("⚠️ No transactions found in the uploaded PDFs.")

# ✍ Manual Transaction Entry
st.header("Manual Transaction Entry")
with st.form("manual_entry_form"):
    date = st.date_input("Transaction Date")
    details = st.text_input("Transaction Details")
    amount = st.number_input("Amount (+ for income, - for spending)", step=0.01)
    submit_button = st.form_submit_button("Add Transaction")

if submit_button:
    df_existing = load_transactions()
    new_transaction = pd.DataFrame([{
        "Bank": "Manual Entry",
        "Transaction Date": date,
        "Details": details,
        "Transaction Amount": amount
    }])
    df_combined = pd.concat([df_existing, new_transaction], ignore_index=True)
    save_transactions(df_combined)
    st.success("✅ Transaction added successfully!")

# 📊 Summary of Transactions
st.header("Spending & Income Summary")
df_transactions = load_transactions()

if not df_transactions.empty:
    df_transactions["Spending"] = df_transactions["Transaction Amount"].apply(lambda x: x if x < 0 else 0)
    df_transactions["Income"] = df_transactions["Transaction Amount"].apply(lambda x: x if x > 0 else 0)

    total_income = df_transactions["Income"].sum()
    total_spending = abs(df_transactions["Spending"].sum())

    st.metric("💰 Total Income", f"${total_income:,.2f}")
    st.metric("💸 Total Spending", f"${total_spending:,.2f}")

    # Breakdown by category (if available)
    if "Details" in df_transactions.columns:
        category_summary = df_transactions[df_transactions["Spending"] < 0].groupby("Details")["Spending"].sum().abs().sort_values(ascending=False).head(5)
        st.subheader("📌 Top Spending Categories")
        st.write(category_summary)

    # Show full transaction table
    st.subheader("📜 All Transactions")
    st.dataframe(df_transactions)
else:
    st.warning("⚠️ No transactions found! Please upload PDFs or enter transactions manually.")

# 📥 Download CSV
st.download_button("📥 Download Transactions as CSV", df_transactions.to_csv(index=False), "transactions.csv", "text/csv")
