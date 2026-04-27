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

# --- 2. UI STYLING (Aapke original design ke mutabiq) ---
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

# --- 3. SESSION & LOGIN CHECK ---
if 'logged_in' not in st.session_state:
    user_in_url = st.query_params.get("user", "")
    if user_in_url:
        st.session_state.update({'logged_in': True, 'username': user_in_url})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 4. LOGIN & REGISTRATION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.query_params["user"] = u
                    st.rerun()
            else:
                st.error("Invalid Credentials")
                
    with tab2:
        new_u = st.text_input("Choose Username", key="reg_u")
        new_p = st.text_input("Choose Password", type="password", key="reg_p")
        if st.button("Register Account"):
            if new_u and new_p:
                users = conn.read(worksheet="Users", ttl=0)
                if new_u in users['Username'].values:
                    st.warning("Username already exists!")
                else:
                    new_user_df = pd.concat([users, pd.DataFrame([{"Username": new_u, "Password": new_p}])], ignore_index=True)
                    conn.update(worksheet="Users", data=new_user_df)
                    st.success("Account Created! Please Login.")
    st.stop()

# --- 5. MASTER LOGIC TOGGLE (Sidebar Navigation) ---
st.sidebar.markdown(f"### 👤 {st.session_state['username'].upper()}")
# Naya feature toggle
view_mode = st.sidebar.radio("Switch View", ["My Dashboard", "Master Pool Logic"])

if st.sidebar.button("Logout 🚪"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()

# Data Load
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# --- CASE 1: MASTER POOL LOGIC (Naya Feature) ---
if view_mode == "Master Pool Logic":
    st.markdown("<h1 class='main-title'>🏛️ BACK-HAND MASTER POOL</h1>", unsafe_allow_html=True)
    
    # Sab owners ka total jama
    total_pool = all_recs['Amount'].sum() if not all_recs.empty else 0.0
    st.metric("Total Back-hand Cash", f"PKR {total_pool:,.0f}")
    
    st.markdown("---")
    st.write("### 👥 All Registered Owners Summary")
    if not all_recs.empty:
        # Group by owner to see each person's total
        summary = all_recs.groupby('Owner')['Amount'].sum().reset_index()
        summary.columns = ['Owner Username', 'Net Contribution']
        st.table(summary)
    else:
        st.info("No data available in the system.")

# --- CASE 2: ORIGINAL DASHBOARD (No Changes) ---
else:
    st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

    # Individual calculations (Same as before)
    total_received = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
    total_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
    net_balance = total_received - total_sent

    st.markdown("### 📊 Account Status")
    c1, c2 = st.columns(2)
    c1.metric("Received", f"{total_received:,.0f}")
    c2.metric("Sent", f"{total_sent:,.0f}")
    st.metric("Net Balance", f"{net_balance:,.0f}", delta=net_balance)
    st.markdown("---")

    # Transaction Confirmation
    if st.session_state['confirm_mode']:
        preview = st.session_state['temp_data']
        st.warning("⚠️ **VERIFY DETAILS**")
        updated_running_bal = net_balance + preview['Amount']
        st.markdown(f"""
        <div class="confirm-card">
            <b>Name:</b> {preview['Name']}<br>
            <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
            <b>Action:</b> {preview['Type']}<br>
            <b>Date:</b> {preview['Date']} | <b>Time:</b> {preview['Time']}<br>
            <b>Reason:</b> {preview['Reason']}
        </div>
        """, unsafe_allow_html=True)
        cy, cn = st.columns(2)
        if cy.button("✅ Confirm & Save"):
            preview['Balance'] = updated_running_bal
            conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
            st.success("Transaction Saved!")
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.rerun()
        if cn.button("❌ Edit"):
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.rerun()
        st.stop()

    # Form (Wahi purana)
    with st.expander("➕ Add New Transaction", expanded=True):
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            n_in = col1.text_input("Name")
            a_in = col1.number_input("Amount", min_value=0.0)
            d_in = col2.date_input("Date", datetime.now())
            t_in_val = col2.time_input("Time", datetime.now().time())
            type_in = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
            r_in = st.text_input("Reason / Remarks")
            if st.form_submit_button("Preview"):
                if n_in and a_in > 0:
                    final_amt = a_in if type_in == "Received (+)" else -a_in
                    st.session_state['temp_data'] = {
                        "Owner": st.session_state['username'], "Name": n_in, "Amount": final_amt, 
                        "Currency": "PKR", "Type": type_in, "Date": d_in.strftime("%Y-%m-%d"), 
                        "Time": t_in_val.strftime("%H:%M:%S"), "Reason": r_in, "Balance": 0.0
                    }
                    st.session_state['confirm_mode'] = True
                    st.rerun()

    # History Table (Wahi purana)
    st.markdown("### 📖 View History")
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=[False, False]), use_container_width=True, hide_index=True)
