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
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #161a25; border-radius: 5px; padding: 10px 20px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Connection establish karna
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. LOGIN & REGISTRATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with t1:
        u_log = st.text_input("Username", key="l_u")
        p_log = st.text_input("Password", type="password", key="l_p")
        if st.button("Enter Dashboard"):
            u_df = conn.read(worksheet="Users", ttl=0)
            if not u_df.empty and u_log in u_df['Username'].values:
                # Password check logic
                actual_p = str(u_df[u_df['Username'] == u_log]['Password'].values[0])
                if str(p_log) == actual_p:
                    st.session_state.update({'logged_in': True, 'username': u_log})
                    st.rerun()
                else: st.error("Ghalat Password!")
            else: st.error("User nahi mila!")

    with t2:
        u_reg = st.text_input("New Username", key="r_u")
        p_reg = st.text_input("New Password", type="password", key="r_p")
        if st.button("Create Account"):
            if u_reg and p_reg:
                u_df = conn.read(worksheet="Users", ttl=0)
                if u_reg in u_df['Username'].values:
                    st.warning("Ye naam pehle se hai!")
                else:
                    # Save naya user
                    new_u = pd.DataFrame([{"Username": u_reg, "Password": p_reg}])
                    updated_u = pd.concat([u_df, new_u], ignore_index=True)
                    conn.update(worksheet="Users", data=updated_u)
                    st.success("Account ban gaya! Ab Login karein.")
            else: st.error("Dono fields bharein.")
    st.stop()

# --- 4. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)
tab_personal, tab_master = st.tabs(["📊 My Ledger", "🏛️ Master Logic"])

# Data Read
all_data = conn.read(worksheet="Sheet1", ttl=0)
my_data = all_data[all_data['Owner'] == st.session_state['username']]

with tab_personal:
    # Calculation
    t_rec = my_data[my_data['Amount'] > 0]['Amount'].sum() if not my_data.empty else 0
    t_sent = abs(my_data[my_data['Amount'] < 0]['Amount'].sum()) if not my_data.empty else 0
    cur_bal = t_rec - t_sent

    st.markdown("### 📊 Status")
    col1, col2 = st.columns(2)
    col1.metric("Received", f"{t_rec:,.0f}")
    col2.metric("Sent", f"{t_sent:,.0f}")
    st.metric("Net Balance", f"{cur_bal:,.0f}")

    # Transaction Form (Direct Save - No Preview)
    with st.expander("➕ Add Transaction", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            f_name = c1.text_input("Name")
            f_amt = c1.number_input("Amount", min_value=0.0)
            f_date = c2.date_input("Date", datetime.now())
            f_time = c2.time_input("Time", datetime.now().time())
            f_type = st.radio("Type", ["Received (+)", "Withdraw (-)"], horizontal=True)
            f_reason = st.text_input("Reason")
            
            submit = st.form_submit_button("Save Transaction")
            if submit:
                if f_name and f_amt > 0:
                    real_amt = f_amt if f_type == "Received (+)" else -f_amt
                    # Naya record build karna
                    row = pd.DataFrame([{
                        "Owner": st.session_state['username'],
                        "Name": f_name,
                        "Amount": real_amt,
                        "Currency": "PKR",
                        "Date": f_date.strftime("%Y-%m-%d"),
                        "Time": f_time.strftime("%H:%M:%S"),
                        "Type": f_type,
                        "Reason": f_reason,
                        "Balance": cur_bal + real_amt
                    }])
                    updated_all = pd.concat([all_data, row], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_all)
                    st.success("Record save ho gaya!")
                    st.rerun()
                else:
                    st.error("Naam aur Amount lazmi hai!")

    #
