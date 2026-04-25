import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# --- 2. UI STYLING (Image Match) ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"], [data-testid="stFooter"] {display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
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
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>")
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
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
    with t2:
        st.info("Registration Feature Active")
    st.stop()

# --- 4. DATA FETCHING ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
# Current Logged-in User Data
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# --- 5. SIDEBAR (MASTER OWNER VIEW) ---
with st.sidebar:
    st.markdown(f"### 👤 User: {st.session_state['username'].upper()}")
    if st.button("Logout 🚪"):
        st.query_params.clear()
        st.session_state.update({'logged_in': False, 'username': ""})
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🌍 MASTER SHEET SUMMARY")
    if not all_recs.empty:
        # PURI SHEET KA HISAB (Saray Users ka mila kar)
        grand_received = all_recs[all_recs['Amount'] > 0]['Amount'].sum()
        grand_sent = abs(all_recs[all_recs['Amount'] < 0]['Amount'].sum())
        grand_balance = grand_received - grand_sent
        
        st.write(f"**Total Cash In:** {grand_received:,.0f}")
        st.write(f"**Total Cash Out:** {grand_sent:,.0f}")
        st.success(f"**Net Sheet Balance:** {grand_balance:,.0f}")
        
        st.markdown("---")
        st.markdown("#### 👥 User-wise Breakdown")
        user_summary = all_recs.groupby('Name')['Amount'].sum().reset_index()
        user_summary.columns = ['Name', 'Balance']
        st.table(user_summary)

# --- 6. MAIN INTERFACE ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Personal Account Status
personal_received = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
personal_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
personal_net = personal_received - personal_sent

st.markdown("### 📊 Your Account Status")
c1, c2 = st.columns(2)
c1.metric("Received", f"{personal_received:,.0f}")
c2.metric("Sent", f"{personal_sent:,.0f}")
st.metric("Net Balance", f"{personal_net:,.0f}")
st.markdown("---")

# --- 7. TRANSACTION & CONFIRMATION ---
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    # Back-hand running balance logic for specific person
    person_history = my_recs[my_recs['Name'] == preview['Name']]
    old_person_bal = person_history['Amount'].sum() if not person_history.empty else 0.0
    new_person_bal = old_person_bal + preview['Amount']
    
    st.markdown(f"""
    <div class="confirm-card">
        <b>Recording for:</b> {preview['Name']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
        <b>Action:</b> {preview['Type']}<br>
        <hr>
        <b>Person's Back-hand Balance:</b> PKR {new_person_bal:,.0f}
    </div>
    """, unsafe_allow_html=True)
    
    cy, cn = st.columns(2)
    if cy.button("✅ Confirm & Save"):
        preview['Balance'] = new_person_bal
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if cn.button("❌ Edit"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- 8. ENTRY FORM ---
with st.expander("➕ New Entry", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        n_in = col1.text_input("Name")
        a_in = col1.number_input("Amount", min_value=0.0)
        d_in = col2.date_input("Date", datetime.now())
        t_in = col2.time_input("Time", datetime.now().time())
        type_in = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
        r_in = st.text_input("Reason")
        
        if st.form_submit_button("Preview"):
            if n_in and a_in > 0:
                final_amt = a_in if type_in == "Received (+)" else -a_in
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": n_in, 
                    "Amount": final_amt, "Currency": "PKR", "Type": type_in,
                    "Date": d_in.strftime("%Y-%m-%d"), "Time": t_in.strftime("%H:%M:%S"),
                    "Reason": r_in, "Balance": 0.0
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# --- 9. HISTORY ---
if not my_recs.empty:
    st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)

