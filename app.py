import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lifetime Ledger", layout="centered")
st.title("💰 My Smart Ledger")

# --- LOGIN LOGIC ---
# Aap apni marzi ka password yahan set kar sakte hain
APP_PASSWORD = "taimur-ledger" 

user_pass = st.sidebar.text_input("Enter Password", type="password")

if user_pass == APP_PASSWORD:
    st.sidebar.success("Access Granted")
    
    conn = st.connection("gsheets", type=GSheetsConnection)

    # --- INPUT FORM ---
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            person_name = st.text_input("Person Name")
            amount = st.number_input("Amount", min_value=0.0)
            manual_date = st.date_input("Select Date", datetime.now())
        
        with col2:
            currency = st.selectbox("Currency", ["PKR", "USD", "AED", "EUR"])
            t_type = st.radio("Type", ["Received (+)", "Sent (-)"])
            manual_time = st.time_input("Select Time", datetime.now().time())

        reason = st.text_input("Reason / Purpose")
        submit = st.form_submit_button("Save Data")

    if submit and person_name and amount > 0:
        existing_df = conn.read(ttl=0)
        final_amount = amount if t_type == "Received (+)" else -amount
        
        new_row = pd.DataFrame([{
            "Name": person_name, 
            "Amount": final_amount, 
            "Currency": currency, 
            "Type": t_type, 
            "Date": manual_date.strftime("%Y-%m-%d"), 
            "Time": manual_time.strftime("%H:%M:%S"), 
            "Reason": reason
        }])
        
        updated_df = pd.concat([existing_df, new_row], ignore_index=True)
        
        try:
            conn.update(data=updated_df)
            st.success(f"Record save ho gaya!")
            st.balloons()
        except Exception as e:
            st.error("Error: Data save nahi ho saka.")

    # --- HISTORY SECTION ---
    if st.checkbox("Show History"):
        history_df = conn.read(ttl=0)
        if not history_df.empty:
            st.dataframe(history_df.sort_values(by=["Date", "Time"], ascending=False))

else:
    if user_pass != "":
        st.error("Ghalat Password! Dobara koshish karein.")
    else:
        st.info("Sidebar mein password enter karein taake aap ledger use kar sakein.")
