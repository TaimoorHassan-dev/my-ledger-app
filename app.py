import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG (Restored) ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# Forced Footer Removal
st.markdown("""
    <style>
    footer {display: none !important; visibility: hidden !important;}
    header {display: none !important; visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #FFD700; color: black; font-weight: bold; height: 50px; }
    .confirm-box { background-color: #161a25; padding: 20px; border: 1px solid #FFD700; border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': "", 'confirm_mode': False, 'temp_data': None})

# --- AUTH LOGIC ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.rerun()
    st.stop()

# --- MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# Current Wallet Balance
current_wallet_bal = my_recs['Amount'].sum() if not my_recs.empty else 0.0

# --- CONFIRMATION VALIDATION ---
if st.session_state['confirm_mode']:
    data = st.session_state['temp_data']
    st.warning("⚠️ **CONFIRM TRANSACTION**")
    
    # Calculate New Balance
    new_bal = current_wallet_bal + data['Amount']
    
    st.markdown(f"""
    <div class="confirm-box">
        <b>Name:</b> {data['Name']}<br>
        <b>Amount:</b> PKR {abs(data['Amount']):,}<br>
        <b>Type:</b> {data['Type']}<br>
        <b>New Running Balance:</b> PKR {new_bal:,}
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes, Save it"):
        data['Balance'] = new_bal # Update balance column
        new_row = pd.DataFrame([data])
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, new_row], ignore_index=True))
        st.success("Saved Successfully!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if c2.button("❌ No, Edit it"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- INPUT FORM (Old Style with Withdraw) ---
with st.expander("➕ Add New Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        amt = col1.number_input("Amount (PKR)", min_value=0.0, step=100.0)
        t_type = col2.radio("Action", ["Received (+)", "Withdraw (-)"])
        date = col2.date_input("Date", datetime.now())
        reason = st.text_input("Reason")
        
        submit = st.form_submit_button("Preview")
        
        if submit:
            if name and amt > 0:
                val = amt if t_type == "Received (+)" else -amt
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'],
                    "Name": name, "Amount": val, "Type": t_type, 
                    "Date": date.strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), 
                    "Reason": reason,
                    "Balance": 0.0 # Placeholder
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# Summary Metrics
if not my_recs.empty:
    st.markdown("### 📊 Status")
    st.metric("Total Balance", f"{current_wallet_bal:,.0f}")

if st.checkbox("📖 View History"):
    st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)

if st.sidebar.button("Logout"):
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
