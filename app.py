import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #161a25; border-radius: 5px; padding: 10px 20px; color: white; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION & LOGIN ---
if 'logged_in' not in st.session_state:
    user_in_url = st.query_params.get("user", "")
    if user_in_url:
        st.session_state.update({'logged_in': True, 'username': user_in_url})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Enter Dashboard"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.query_params["user"] = u
                st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# --- 4. MAIN INTERFACE WITH TABS ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Tabs create kar diye hain taake sidebar ka rona na rahe
tab_my, tab_master = st.tabs(["📊 My Personal Ledger", "🏛️ Back-hand Master Logic"])

# Data Load
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# --- TAB 1: PERSONAL LEDGER (No Changes) ---
with tab_my:
    total_received = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
    total_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
    net_balance = total_received - total_sent

    st.markdown("### 📊 Account Status")
    c1, c2 = st.columns(2)
    c1.metric("Received", f"{total_received:,.0f}")
    c2.metric("Sent", f"{total_sent:,.0f}")
    st.metric("Net Balance", f"{net_balance:,.0f}", delta=net_balance)
    
    # Entry Form with Time Fix
    with st.expander("➕ Add New Transaction", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            n_in = col1.text_input("Name")
            a_in = col1.number_input("Amount", min_value=0.0)
            d_in = col2.date_input("Date", datetime.now())
            t_in_val = col2.time_input("Time", datetime.now().time())
            type_in = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
            r_in = st.text_input("Reason")
            
            if st.form_submit_button("Preview"):
                if n_in and a_in > 0:
                    st.session_state['temp_data'] = {
                        "Owner": st.session_state['username'], "Name": n_in, 
                        "Amount": a_in if type_in == "Received (+)" else -a_in, 
                        "Currency": "PKR", "Type": type_in, "Date": d_in.strftime("%Y-%m-%d"), 
                        "Time": t_in_val.strftime("%H:%M:%S"), "Reason": r_in, "Balance": 0.0
                    }
                    st.session_state['confirm_mode'] = True
                    st.rerun()

    # History
    st.markdown("### 📖 View History")
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)

# --- TAB 2: MASTER LOGIC (Naya Feature) ---
with tab_master:
    st.markdown("### 🏛️ Back-hand System Summary")
    total_pool = all_recs['Amount'].sum() if not all_recs.empty else 0.0
    st.metric("System Total Pool (All Owners)", f"PKR {total_pool:,.0f}")
    
    st.markdown("---")
    st.write("### 👥 Breakdown by Registration")
    if not all_recs.empty:
        # Har owner ka total nikalne ke liye grouping
        summary = all_recs.groupby('Owner')['Amount'].sum().reset_index()
        summary.columns = ['Owner Name', 'Total Contribution']
        st.dataframe(summary, use_container_width=True, hide_index=True)

# Logout button end par
if st.button("Logout 🚪"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
