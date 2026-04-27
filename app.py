import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered")

st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Connection Setup
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Enter Dashboard"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.rerun()
    st.stop()

# --- 3. DATA LOADING ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
if not all_recs.empty:
    all_recs['Date'] = pd.to_datetime(all_recs['Date'], errors='coerce')
    all_recs = all_recs.dropna(subset=['Date'])

# --- 4. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

my_recs = all_recs[all_recs['Owner'] == st.session_state['username']] if not all_recs.empty else pd.DataFrame()
current_bal = my_recs['Amount'].sum() if not my_recs.empty else 0.0

st.metric("Net Balance", f"PKR {current_bal:,.0f}")

# --- DIRECT SAVE FORM (No more preview issues) ---
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n = col1.text_input("Name")
        a = col1.number_input("Amount", min_value=0.0)
        d = col2.date_input("Date", datetime.now())
        t = col2.time_input("Time", datetime.now().time())
        type_tx = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
        r = st.text_input("Reason")
        
        if st.form_submit_button("Save Transaction"):
            if n and a > 0:
                # Naya data tayyar karein
                new_data = {
                    "Owner": st.session_state['username'],
                    "Name": n,
                    "Amount": a if type_tx == "Received (+)" else -a,
                    "Currency": "PKR",
                    "Date": d.strftime("%Y-%m-%d"),
                    "Time": t.strftime("%H:%M:%S"),
                    "Type": type_tx,
                    "Reason": r,
                    "Balance": current_bal + (a if type_tx == "Received (+)" else -a)
                }
                
                # Sheet update logic
                fresh_sheet = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([fresh_sheet, pd.DataFrame([new_data])], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success("✅ Recorded Successfully!")
                st.rerun()
            else:
                st.error("Please fill Name and Amount.")

# --- VIEW HISTORY ---
st.markdown("### 📖 History")
if not my_recs.empty:
    st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True, hide_index=True)

if st.button("Logout"):
    st.session_state.clear(); st.rerun()
