import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG & ABSOLUTE BRANDING REMOVAL ---
st.set_page_config(
    page_title="Zarkash Digital Ledger", 
    layout="centered", 
    page_icon="💸"
)

# Deep Injection CSS to kill the footer and header completely
st.markdown("""
    <style>
    /* Sab se pehle pura footer aur header block karein */
    footer {display: none !important; visibility: hidden !important; height: 0px !important;}
    header {display: none !important; visibility: hidden !important; height: 0px !important;}
    
    /* Specific elements ko target karein jo app mein nazar aate hain */
    .stDeployButton {display:none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    [data-testid="stAppViewBlockContainer"] {padding-top: 2rem !important; padding-bottom: 0rem !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* Background aur spacing adjustment */
    .stApp { bottom: 0px !important; }
    
    /* Global Professional Styling */
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; }
    .sub-title { text-align: center; color: #888; font-size: 16px; margin-bottom: 25px; }
    
    /* Metrics & Dashboard */
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; color: #ffffff; }
    [data-testid="stMetricLabel"] { color: #aaaaaa; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Form & Button */
    [data-testid="stForm"] { border: 1px solid #333; border-radius: 15px; padding: 25px; background-color: #161a25; }
    .stButton>button { 
        width: 100%; border-radius: 25px; background-color: #FFD700; 
        color: black; font-weight: bold; height: 50px; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

# --- 2. AUTHENTICATION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your Professional Digital Finance Ledger</p>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Access Ledger"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("Invalid Password")
            else: st.error("User not found")
    with t2:
        nu = st.text_input("New Username", key="s_u")
        np = st.text_input("New Password", type="password", key="s_p")
        if st.button("Sign Up"):
            if nu and np:
                users = conn.read(worksheet="Users", ttl=0)
                if nu in users['Username'].values: st.warning("Username taken")
                else:
                    conn.update(worksheet="Users", data=pd.concat([users, pd.DataFrame([{"Username": nu, "Password": np}])], ignore_index=True))
                    st.success("Registered! Go to Login.")
    st.stop()

# --- 3. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Fetch Data
all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

if not my_recs.empty:
    total_in = my_recs[my_recs['Amount'] > 0]['Amount'].sum()
    total_out = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum())
    bal = total_in - total_out

    st.markdown("### 📊 Financial Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Received (+)", f"{total_in:,.0f}")
    c2.metric("Sent (-)", f"{total_out:,.0f}")
    st.metric("Net Balance", f"{bal:,.0f}", delta=bal)
    st.markdown("---")

with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Person/Name")
        amt = col1.number_input("Amount", min_value=0.0)
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        date = col2.date_input("Date", datetime.now())
        reason = st.text_input("Description")
        if st.form_submit_button("Save"):
            if name and amt > 0:
                final_val = amt if t_type == "Received (+)" else -amt
                new_row = pd.DataFrame([{"Owner": st.session_state['username'], "Name": name, "Amount": final_val, "Type": t_type, "Date": date.strftime("%Y-%m-%d"), "Time": datetime.now().strftime("%H:%M:%S"), "Reason": reason}])
                conn.update(worksheet="Sheet1", data=pd.concat([all_recs, new_row], ignore_index=True))
                st.success("Record Saved!")
                st.rerun()

if st.checkbox("📖 View History"):
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

if st.sidebar.button("Logout"):
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
