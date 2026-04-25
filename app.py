import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Family Zarkash Ledger", layout="centered", page_icon="🏦")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; }
    .vault-card { background: linear-gradient(45deg, #1e2632, #161a25); padding: 15px; border-left: 5px solid #FFD700; border-radius: 5px; margin-bottom: 20px; }
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION & LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 FAMILY LEDGER</h1>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.rerun()
    st.stop()

# --- 4. MASTER DATA FETCH ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Name'] == st.session_state['username']]

# --- 5. SIDEBAR: MASTER VAULT (The Feature You Asked For) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['username'].upper()}")
    if st.button("Logout"):
        st.session_state.update({'logged_in': False, 'username': ""})
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🏛️ FAMILY MASTER VAULT")
    
    if not all_recs.empty:
        # Sari family ka combined total
        total_pool = all_recs['Amount'].sum()
        st.markdown(f"""
            <div class="vault-card">
                <small>Total Combined Balance</small><br>
                <span style="font-size:22px; color:#FFD700; font-weight:bold;">PKR {total_pool:,.0f}</span>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 👥 Member Balances")
        member_totals = all_recs.groupby('Name')['Amount'].sum().reset_index()
        st.table(member_totals)

# --- 6. MAIN DASHBOARD (User Interface) ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Personal Status
personal_bal = my_recs['Amount'].sum() if not my_recs.empty else 0.0
st.metric("Your Personal Total", f"PKR {personal_bal:,.0f}")
st.markdown("---")

# --- 7. NEW TRANSACTION (Personal & Pool Impact) ---
with st.expander("➕ Add/Withdraw Payment", expanded=True):
    with st.form("family_form", clear_on_submit=True):
        amt = st.number_input("Amount", min_value=0.0)
        action = st.radio("Action", ["Send Money (+)", "Withdraw (-)"], horizontal=True)
        note = st.text_input("Reason (e.g. Bike Payment)")
        
        if st.form_submit_button("Preview & Save"):
            if amt > 0:
                final_amt = amt if action == "Send Money (+)" else -amt
                
                # Logic: Withdraw check for individual
                if action == "Withdraw (-)" and abs(final_amt) > personal_bal:
                    st.error("You don't have enough balance!")
                else:
                    new_entry = {
                        "Owner": "FamilyPool",
                        "Name": st.session_state['username'],
                        "Amount": final_amt,
                        "Currency": "PKR",
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Time": datetime.now().strftime("%H:%M:%S"),
                        "Type": action,
                        "Reason": note,
                        "Balance": personal_bal + final_amt
                    }
                    # Save to Sheet
                    updated_df = pd.concat([all_recs, pd.DataFrame([new_entry])], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    st.success("Record Updated!")
                    st.rerun()

# --- 8. PERSONAL HISTORY ---
st.markdown("### 📖 My History")
if not my_recs.empty:
    st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True, hide_index=True)
