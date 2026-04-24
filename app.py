import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lifetime Ledger", layout="centered")
st.title("💰 My Smart Ledger")

# Connection setup
conn = st.connection("gsheets", type=GSheetsConnection)

# Form for entry
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
    # Latest data read karein pehle
    existing_df = conn.read(ttl=0)
    
    final_amount = amount if t_type == "Received (+)" else -amount
    new_row = pd.DataFrame([{
        "Name": person_name, 
        "Amount": final_amount, 
        "Currency": currency, 
        "Type": t_type, 
        "Date": datetime.now().strftime("%Y-%m-%d"), 
        "Time": datetime.now().strftime("%H:%M:%S"), 
        "Reason": reason
    }])
    
    # Data merge karein
    updated_df = pd.concat([existing_df, new_row], ignore_index=True)
    
    try:
        conn.update(data=updated_df)
        st.success(f"Zabardast! {person_name} ka record save ho gaya.")
        st.balloons()
    except Exception as e:
        st.error("Error: Google Sheet ne data save nahi karne diya.")

# --- History Section ---
if st.checkbox("Show History"):
    # Yahan ttl=0 hona zaroori hai taake fresh data nazar aaye
    history_df = conn.read(ttl=0)
    if not history_df.empty:
        st.dataframe(history_df.sort_index(ascending=False))
    else:
        st.info("Abhi tak koi history nahi hai.")
