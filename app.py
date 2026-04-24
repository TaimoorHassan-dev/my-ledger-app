import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION (New Name & Icon) ---
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰"  # Ye icon browser tab par nazar aayega
)

# --- 2. FORCED BRANDING REMOVAL & STYLING ---
st.markdown("""
    <style>
    /* Sab se pehle footer aur header ko block karein */
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"], [data-testid="stFooter"], .stDeployButton {display: none !important;}
    
    /* App ki look professional banayein */
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
    
    /* Confirmation Card */
    .confirm-card { 
        background-color: #1e2433; padding: 20px; border: 2px solid #FFD700; 
        border-radius: 12px; margin-bottom: 20px; 
    }
    
    /* Standard UI fixes */
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #FFD700; color: black; font-weight: bold; height: 50px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. REFRESH-PROOF (LOGIN PERSISTENCE) ---
# URL parameters se user check karein
q_params = st.query_params
current_user_url = q_params.get("user", "")

if 'logged_in' not in st.session_state:
    if current_user_url:
        st.session_state.update({'logged_in': True, 'username': current_user_url})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 4. AUTHENTICATION SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your Professional Finance Partner</p>", unsafe_allow_html=True)
    
    tab_login, tab_reg = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab_login:
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u_input in users['Username'].values:
                stored_p = str(users[users['Username'] == u_input]['Password'].values[0])
                if str(p_input) == stored_p:
                    st.session_state.update({'logged_in': True, 'username': u_input})
                    st.query_params["user"] = u_input  # URL mein save karein
                    st.rerun()
                else: st.error("❌ Wrong Password")
            else: st.error("❌ User not found")

    with tab_reg:
        nu = st.text_input("New User")
        np = st.text_input("New Pass", type="password")
        if st.button("Register Now"):
            if nu and np:
                users = conn.read(worksheet="Users", ttl=0)
                if nu in users['Username'].values: st.warning("Name taken")
                else:
                    conn.update(worksheet="Users", data=pd.concat([users, pd.DataFrame([{"Username": nu, "Password": np}])], ignore_index=True))
                    st.success("✅ Success! Please login.")
    st.stop()

# --- 5. MAIN LEDGER ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}</h1>", unsafe_allow_html=True)

# Data Fetching
all_data = conn.read(worksheet="Sheet1", ttl=0)
my_data = all_data[all_data['Owner'] == st.session_state['username']]

# --- PRE-SAVE CONFIRMATION VALIDATION ---
if st.session_state['confirm_mode']:
    t = st.session_state['temp_data']
    st.warning("⚠️ **CHECK CAREFULLY BEFORE SAVING**")
    st.markdown(f"""
    <div class="confirm-card">
        <b>Name:</b> {t['Name']}<br>
        <b>Amount:</b> PKR {abs(t['Amount']):,.0f}<br>
        <b>Type:</b> {t['Type']}<br>
        <b>Reason:</b> {t['Reason']}
    </div>
    """, unsafe_allow_html=True)
    
    c_y, c_n = st.columns(2)
    if c_y.button("✅ Yes, Everything is Correct"):
        conn.update(worksheet="Sheet1", data=pd.concat([all_data, pd.DataFrame([t])], ignore_index=True))
        st.success("Transaction Locked!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if c_n.button("❌ No, Let me Change it"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- ENTRY FORM ---
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        p_name = col1.text_input("Person Name")
        p_amt = col1.number_input("Amount (PKR)", min_value=0.0, step=500.0)
        p_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        p_date = col2.date_input("Date", datetime.now())
        p_reason = st.text_input("Reason")
        
        if st.form_submit_button("Preview & Save"):
            if p_name and p_amt > 0:
                val = p_amt if p_type == "Received (+)" else -p_amt
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": p_name, 
                    "Amount": val, "Currency": "PKR", "Type": p_type, 
                    "Date": p_date.strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": p_reason
                }
                st.session_state['confirm_mode'] = True
                st.rerun()
            else: st.error("⚠️ Please fill details.")

# Summary Metrics
if not my_data.empty:
    i = my_data[my_data['Amount'] > 0]['Amount'].sum()
    o = abs(my_data[my_data['Amount'] < 0]['Amount'].sum())
    st.markdown("### 📊 Status")
    st.columns(3)[0].metric("Income", f"{i:,.0f}")
    st.columns(3)[1].metric("Expenses", f"{o:,.0f}")
    st.columns(3)[2].metric("Balance", f"{(i-o):,.0f}", delta=(i-o))

# History
if st.checkbox("📖 View History"):
    st.dataframe(my_data.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# Logout
if st.sidebar.button("Logout"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
