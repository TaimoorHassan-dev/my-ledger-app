import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lifetime Ledger", layout="centered")
st.title("💰 My Smart Ledger")

# Google Sheets Connection (ttl=0 adds real-time updates)
conn = st.connection("gsheets", type=GSheetsConnection, ttl=0)

try:
    df = conn.read()
except Exception:
    df = pd.DataFrame(columns=['Name', 'Amount', 'Currency', 'Type', 'Date', 'Time', 'Reason'])

with st.form("transaction_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        person_name = st.text_input("Person Name")
        amount = st.number_input("Amount", min_value=0.0)
    with col2:
        currency = st.selectbox("Currency", ["PKR", "USD", "AED", "EUR"])
        t_type = st.radio("Type", ["Received (+)", "Sent (-)"])

    reason = st.text_input("Reason / Purpose")
    submit = st.form_submit_button("Save Data")

if submit and person_name and amount > 0:
    final_amount = amount if t_type == "Received (+)" else -amount
    new_row = {
        "Name": person_name, 
        "Amount": final_amount, 
        "Currency": currency, 
        "Type": t_type, 
        "Date": datetime.now().strftime("%Y-%m-%d"), 
        "Time": datetime.now().strftime("%H:%M:%S"), 
        "Reason": reason
    }
    
    # Naya data purane data mein add karna
    updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Google Sheet ko update karna
    conn.update(data=updated_df)
    st.success(f"Zabardast! {person_name} ka record save ho gaya.")

if st.checkbox("Show History"):
    # Fresh data read karke dikhana
    st.dataframe(conn.read().sort_index(ascending=False))
