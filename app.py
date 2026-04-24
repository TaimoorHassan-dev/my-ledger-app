import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG ---
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰"
)

# --- 2. THE ULTIMATE BRANDING REMOVAL ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"], [data-testid="stFooter"] {display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 30px; background-color: #FFD700; color: black; font-weight: bold; height: 55px; border: none; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 2px solid #FFD700; border-radius: 15px; }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. REFRESH-PROOF SYSTEM ---
query_params = st.query_params
if 'logged_in' not in st.session_state:
    user_in_url = query_params.get("user", "")
    if user_in_url:
        st.session_state.update({'logged_in': True, 'username': user_in_url})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 4. SECURE ACCESS ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.query_params["user"] = u
                    st.rerun()
    st.stop()

# --- 5. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Fetch Data
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# LIVE BALANCE FOR HEADER
net_balance = my_recs['Amount'].sum() if not my_recs.empty else 0.0

st.write(f"Total Available Balance")
st.markdown(f"## PKR {net_balance:,.0f}")
st.markdown("---")

# --- TRANSACTION CONFIRMATION ---
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    st.warning("⚠️ **VERIFY BEFORE SAVING**")
    
    # Calculate Running Balance for the sheet
    new_bal = net_balance + preview['Amount']
    
    st.markdown(f"""
    <div class="confirm-card">
        <b>Name:</b> {preview['Name']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
        <b>Action:</b> {preview['Type']}<br>
        <b>Reason:</b> {preview['Reason']}
    </div>
    """, unsafe_allow_html=True)
    
    cy, cn = st.columns(2)
    if cy.button("✅ Confirm & Add"):
        # Add the Balance to the record
        preview['Balance'] = new_bal
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.success("Transaction Saved!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if cn.button("❌ Edit Again"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- ENTRY FORM (Wahi purana template) ---
with st.expander("➕ Add New Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n_in = col1.text_input("Name")
        a_in = col1.number_input("Amount", min_value=0.0, step=100.0)
        
        t_in = col2.radio("Action", ["Received (+)", "Withdraw (-)"])
        r_in = st.text_input("Reason / Remarks")
        
        if st.form_submit_button("Preview"):
            if n_in and a_in > 0:
                final_amt = a_in if t_in == "Received (+)" else -a_in
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], 
                    "Name": n_in, 
                    "Amount": final_amt, 
                    "Type": t_in, 
                    "Date": datetime.now().strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), 
                    "Reason": r_in,
                    "Balance": 0.0 # Placeholder
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# History Table
st.markdown(" ")
show_history = st.checkbox("📖 View Transaction History", value=True)
if show_history:
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)

if st.sidebar.button("Logout"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
