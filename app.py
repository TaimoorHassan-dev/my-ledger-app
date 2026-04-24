import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Lifetime Ledger", layout="centered", page_icon="💰")

# --- CUSTOM CSS FOR PROFESSIONAL LOOK ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    .login-box {
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #464b5d;
        background-color: #161b22;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def login():
    if st.session_state['password_input'] == "taimur-ledger": # Aapka Password
        st.session_state['authenticated'] = True
    else:
        st.error("❌ Ghalat Password! Dobara koshish karein.")

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    st.markdown("<h2 style='text-align: center;'>🔐 Secure Login</h2>", unsafe_allow_html=True)
    with st.container():
        st.text_input("Enter Password", type="password", key="password_input", on_change=login)
        st.info("Mehfuz access ke liye password enter karein.")
        st.stop() # Jab tak login nahi hoga, baqi code nahi chalega

# --- ACTUAL APP (After Successful Login) ---
st.markdown("<h1 style='text-align: center;'>💰 My Smart Ledger</h1>", unsafe_allow_html=True)
st.success("✅ Welcome, Taimur!")

conn = st.connection("gsheets", type=GSheetsConnection)

# --- TRANSACTION FORM ---
with st.expander("➕ Nayi Entry Karein", expanded=True):
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
    except:
        st.error("Error: Data save nahi ho saka.")

# --- HISTORY SECTION ---
st.markdown("---")
if st.checkbox("📖 Show Transaction History"):
    history_df = conn.read(ttl=0)
    if not history_df.empty:
        st.dataframe(history_df.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True)
    else:
        st.info("Abhi tak koi records nahi hain.")

# Logout Button in Sidebar
if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()
