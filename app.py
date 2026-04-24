import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. APP CONFIG & MOBILE ICON SETUP ---
# Note: Mobile icon ke liye humne link inject kiya hai niche
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰" 
)

# Yeh code mobile browser ko bataye ga ke "Add to Home Screen" par naya icon use kare
# Maine yahan aik professional gold-finance icon ka link dala hai
st.markdown(
    f"""
    <link rel="apple-touch-icon" sizes="180x180" href="https://cdn-icons-png.flaticon.com/512/5839/5839888.png">
    <link rel="icon" type="image/png" sizes="32x32" href="https://cdn-icons-png.flaticon.com/512/5839/5839888.png">
    <link rel="icon" type="image/png" sizes="16x16" href="https://cdn-icons-png.flaticon.com/512/5839/5839888.png">
    """,
    unsafe_allow_html=True
)

# --- 2. FORCED BRANDING REMOVAL ---
st.markdown("""
    <style>
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"], [data-testid="stFooter"], .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #FFD700; color: black; font-weight: bold; height: 50px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 2px solid #FFD700; border-radius: 12px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. REFRESH-PROOF LOGIN ---
query_params = st.query_params
url_user = query_params.get("user", "")

if 'logged_in' not in st.session_state:
    if url_user:
        st.session_state.update({'logged_in': True, 'username': url_user})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 4. AUTHENTICATION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.query_params["user"] = u
                    st.rerun()
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if nu and np:
                users = conn.read(worksheet="Users", ttl=0)
                conn.update(worksheet="Users", data=pd.concat([users, pd.DataFrame([{"Username": nu, "Password": np}])], ignore_index=True))
                st.success("Registered! Now Login.")
    st.stop()

# --- 5. MAIN LEDGER ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)

all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# Confirmation Validation Logic
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    st.warning("⚠️ **CONFIRM DETAILS**")
    st.markdown(f"""
    <div class="confirm-card">
        <b>Name:</b> {preview['Name']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
        <b>Type:</b> {preview['Type']}<br>
        <b>Reason:</b> {preview['Reason']}
    </div>
    """, unsafe_allow_html=True)
    
    col_y, col_n = st.columns(2)
    if col_y.button("✅ Save"):
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.success("Saved!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if col_n.button("❌ Edit"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# Input Form
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        n = c1.text_input("Person Name")
        a = c1.number_input("Amount", min_value=0.0)
        t = c2.radio("Type", ["Received (+)", "Sent (-)"])
        r = st.text_input("Reason")
        if st.form_submit_button("Preview & Save"):
            if n and a > 0:
                val = a if t == "Received (+)" else -a
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": n, "Amount": val, 
                    "Type": t, "Date": datetime.now().strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": r
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# Summary & History
if not my_recs.empty:
    i = my_recs[my_recs['Amount'] > 0]['Amount'].sum()
    o = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum())
    st.columns(3)[0].metric("In", f"{i:,.0f}")
    st.columns(3)[1].metric("Out", f"{o:,.0f}")
    st.columns(3)[2].metric("Balance", f"{(i-o):,.0f}", delta=(i-o))

if st.checkbox("📖 Show History"):
    st.dataframe(my_recs.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

if st.sidebar.button("Logout"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
