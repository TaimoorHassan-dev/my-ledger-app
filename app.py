import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# CSS for UI
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Connection initialization
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})
if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# Login Logic
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
# Date cleaning with error handling
if not all_recs.empty:
    all_recs['Date'] = pd.to_datetime(all_recs['Date'], errors='coerce')
    all_recs = all_recs.dropna(subset=['Date'])

# --- 4. MAIN UI ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📊 My Ledger", "📈 Insights"])

with tab1:
    my_recs = all_recs[all_recs['Owner'] == st.session_state['username']] if not all_recs.empty else pd.DataFrame()
    net_bal = my_recs['Amount'].sum() if not my_recs.empty else 0.0
    st.metric("Net Balance", f"PKR {net_bal:,.0f}")

    if st.session_state['confirm_mode']:
        # Preview Section
        preview = st.session_state['temp_data']
        st.markdown(f"""<div class="confirm-card">
            <b>Name:</b> {preview['Name']}<br>
            <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
            <b>Reason:</b> {preview['Reason']}</div>""", unsafe_allow_html=True)
        
        c_y, c_n = st.columns(2)
        if c_y.button("✅ Confirm & Save"):
            try:
                # 1. Purana data load karein
                fresh_data = conn.read(worksheet="Sheet1", ttl=0)
                # 2. Naya row add karein
                new_entry = pd.DataFrame([preview])
                final_df = pd.concat([fresh_data, new_entry], ignore_index=True)
                # 3. Sheet update karein
                conn.update(worksheet="Sheet1", data=final_df)
                
                st.session_state.update({'confirm_mode': False, 'temp_data': None})
                st.success("Record Saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")
        
        if c_n.button("❌ Edit"):
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.rerun()
    else:
        # Input Form
        with st.expander("➕ Add New Transaction", expanded=True):
            with st.form("ledger_form"):
                n = st.text_input("Name")
                a = st.number_input("Amount", min_value=0.0)
                type_tx = st.radio("Type", ["Received (+)", "Withdraw (-)"])
                r = st.text_input("Reason")
                if st.form_submit_button("Preview"):
                    if n and a > 0:
                        st.session_state['temp_data'] = {
                            "Owner": st.session_state['username'],
                            "Name": n,
                            "Amount": a if type_tx == "Received (+)" else -a,
                            "Currency": "PKR",
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Time": datetime.now().strftime("%H:%M:%S"),
                            "Type": type_tx,
                            "Reason": r,
                            "Balance": net_bal + (a if type_tx == "Received (+)" else -a)
                        }
                        st.session_state['confirm_mode'] = True
                        st.rerun()

    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by="Date", ascending=False), use_container_width=True)

if st.button("Logout"):
    st.session_state.clear(); st.rerun()
