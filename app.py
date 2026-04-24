import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. SET APP IDENTITY ---
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰"
)

# --- 2. THE ULTIMATE FOOTER & BRANDING KILLER ---
st.markdown("""
    <style>
    /* Sab kuch hide karo jo Streamlit ka hai */
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"], [data-testid="stFooter"] {display: none !important;}
    
    /* Mobile screen spacing adjustment */
    .block-container {padding-top: 1rem !important; padding-bottom: 0rem !important;}
    
    /* Professional Gold Theme */
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 0px; }
    .stButton>button { width: 100%; border-radius: 30px; background-color: #FFD700; color: black; font-weight: bold; height: 55px; border: none; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 2px solid #FFD700; border-radius: 15px; }
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
                else: st.error("Wrong Password")
            else: st.error("User not found")
    st.stop()

# --- 5. ZARKASH DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)

# Data Persistence Logic
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# Transaction Confirmation UI
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    st.warning("⚠️ **VERIFY BEFORE SAVING**")
    st.markdown(f"""
    <div class="confirm-card">
        <b>Payee:</b> {preview['Name']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
        <b>Type:</b> {preview['Type']}<br>
        <b>Reason:</b> {preview['Reason']}
    </div>
    """, unsafe_allow_html=True)
    
    cy, cn = st.columns(2)
    if cy.button("✅ Confirm"):
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.success("Success!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if cn.button("❌ Edit"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# Main Entry Form
with st.expander("➕ New Transaction", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n_in = c1.text_input("Name")
        a_in = c1.number_input("Amount", min_value=0.0)
        t_in = c2.radio("Type", ["Received (+)", "Sent (-)"])
        r_in = st.text_input("Purpose")
        if st.form_submit_button("Preview"):
            if n_in and a_in > 0:
                final_amt = a_in if t_in == "Received (+)" else -a_in
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": n_in, "Amount": final_amt, 
                    "Type": t_in, "Date": datetime.now().strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": r_in
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# Financial Status
if not my_recs.empty:
    income = my_recs[my_recs['Amount'] > 0]['Amount'].sum()
    expense = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum())
    st.columns(3)[0].metric("Income", f"{income:,.0f}")
    st.columns(3)[1].metric("Sent", f"{expense:,.0f}")
    st.columns(3)[2].metric("Balance", f"{(income-expense):,.0f}")

if st.sidebar.button("Logout"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
