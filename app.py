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
    [data-testid="stHeader"], [data-testid="stFooter"] {display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION & LOGIN ---
if 'logged_in' not in st.session_state:
    user_in_url = st.query_params.get("user", "")
    st.session_state.update({'logged_in': bool(user_in_url), 'username': user_in_url or ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.query_params["user"] = u
                    st.rerun()
    with tab2: st.info("Create a new account here.")
    st.stop()

# --- 4. DATA & SIDEBAR ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['username'].upper()}")
    if st.button("Logout"):
        st.query_params.clear()
        st.session_state.update({'logged_in': False, 'username': ""})
        st.rerun()
    st.markdown("---")
    st.markdown("### 👥 Back-hand Balances")
    if not my_recs.empty:
        # Har individual user ka current total (Received - Withdraw)
        user_balances = my_recs.groupby('Name')['Amount'].sum().reset_index()
        user_balances.columns = ['Name', 'Available Balance']
        st.dataframe(user_balances, hide_index=True)

st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Main Dashboard Totals
net_bal = my_recs['Amount'].sum() if not my_recs.empty else 0.0
st.metric("Total Account Balance", f"PKR {net_bal:,.0f}")
st.markdown("---")

# --- 5. SMART BACK-HAND TRANSACTION ---
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    st.warning("⚠️ **VERIFY TRANSACTION**")
    
    # BACK-HAND CALCULATION:
    # 1. Is bande ka purana record nikalen
    person_name = preview['Name']
    person_history = my_recs[my_recs['Name'] == person_name]
    old_bal = person_history['Amount'].sum() if not person_history.empty else 0.0
    
    # 2. Nayi entry add kar ke balance nikalen (minus automatically handle hoga negative amount se)
    new_bal = old_bal + preview['Amount']
    
    st.markdown(f"""
    <div class="confirm-card">
        <b>Name:</b> {person_name}<br>
        <b>Type:</b> {preview['Type']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
        <hr>
        <b>Back-hand Balance:</b> PKR {old_bal:,.0f} ➡️ <span style="color:#FFD700;">PKR {new_bal:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Confirm"):
        preview['Balance'] = new_bal # Back-hand balance column update
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if c2.button("❌ Edit"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- 6. ENTRY FORM ---
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n_in = col1.text_input("Person Name")
        a_in = col1.number_input("Amount", min_value=0.0)
        d_in = col2.date_input("Date", datetime.now())
        t_in = col2.time_input("Time", datetime.now().time())
        type_in = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
        r_in = st.text_input("Reason")
        
        if st.form_submit_button("Preview & Save"):
            if n_in and a_in > 0:
                # Agar withdraw hai toh amount ko negative kar do back-hand ke liye
                final_amt = a_in if type_in == "Received (+)" else -a_in
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": n_in, 
                    "Amount": final_amt, "Currency": "PKR", "Type": type_in,
                    "Date": d_in.strftime("%Y-%m-%d"), "Time": t_in.strftime("%H:%M:%S"),
                    "Reason": r_in, "Balance": 0.0
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# --- 7. HISTORY ---
st.markdown("### 📖 History")
if not my_recs.empty:
    st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)
