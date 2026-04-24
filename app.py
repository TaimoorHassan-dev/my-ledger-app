import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Zarkash Digital Ledger", 
    layout="centered", 
    page_icon="💸"
)

# Professional CSS to hide Streamlit branding and style the app
st.markdown("""
    <style>
    /* HIDE STREAMLIT BRANDING (Footer, Header, and Menu) */
    header {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    #MainMenu {visibility: hidden; display: none !important;}
    .stDeployButton {display:none !important;}
    
    /* Global Styles */
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #888; font-size: 16px; margin-bottom: 25px; }
    
    /* Metrics & Dashboard Styling */
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #888; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Form & Button Styling */
    [data-testid="stForm"] { border: 1px solid #333; border-radius: 12px; padding: 20px; background-color: #111; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FFD700; color: black; font-weight: bold; border: none; height: 45px; }
    .stButton>button:hover { background-color: #e6c200; color: black; }
    </style>
    """, unsafe_allow_html=True)

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

# --- 2. AUTHENTICATION SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your Professional Digital Finance Ledger</p>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
    
    with auth_tab1:
        u = st.text_input("Username", key="l_user", placeholder="Enter username")
        p = st.text_input("Password", type="password", key="l_pass", placeholder="Enter password")
        if st.button("Enter Dashboard"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and u in users_df['Username'].values:
                # Password validation
                stored_p = str(users_df[users_df['Username'] == u]['Password'].values[0])
                if str(p) == stored_p:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("❌ Invalid Password.")
            else: st.error("❌ User not found.")

    with auth_tab2:
        nu = st.text_input("Choose Username", key="s_user")
        np = st.text_input("Choose Password", type="password", key="s_pass")
        if st.button("Register & Join"):
            if nu and np:
                users_df = conn.read(worksheet="Users", ttl=0)
                if nu in users_df['Username'].values: st.warning("⚠️ Username taken.")
                else:
                    new_user = pd.DataFrame([{"Username": nu, "Password": np}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_user], ignore_index=True))
                    st.success("✅ Registered! Now please Login.")
            else: st.warning("⚠️ Fill all fields.")
    st.stop()

# --- 3. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Fetch Data
all_records = conn.read(worksheet="Sheet1", ttl=0)
user_records = all_records[all_records['Owner'] == st.session_state['username']]

# Financial Summary Metrics
if not user_records.empty:
    total_in = user_records[user_records['Amount'] > 0]['Amount'].sum()
    total_out = abs(user_records[user_records['Amount'] < 0]['Amount'].sum())
    current_bal = total_in - total_out

    st.markdown("### 📈 Account Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Received (+)", f"{total_in:,.0f}")
    c2.metric("Sent (-)", f"{total_out:,.0f}", delta_color="inverse")
    st.metric("Net Balance", f"{current_bal:,.0f}", delta=current_bal)
    st.markdown("---")

# New Entry Form
with st.expander("➕ Add New Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        p_name = col1.text_input("Person / Company Name")
        p_amount = col1.number_input("Amount (PKR)", min_value=0.0, step=500.0)
        
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        t_date = col2.date_input("Date", datetime.now())
        
        p_reason = st.text_input("Purpose / Description")
        
        if st.form_submit_button("Save Transaction"):
            if p_name and p_amount > 0 and p_reason:
                # Logic: Subtract if Sent
                val = p_amount if t_type == "Received (+)" else -p_amount
                
                new_row = pd.DataFrame([{
                    "Owner": st.session_state['username'],
                    "Name": p_name, "Amount": val, "Currency": "PKR",
                    "Type": t_type, "Date": t_date.strftime("%Y-%m-%d"),
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": p_reason
                }])
                
                conn.update(worksheet="Sheet1", data=pd.concat([all_records, new_row], ignore_index=True))
                st.success("✅ Record Saved!")
                st.rerun()
            else: st.error("⚠️ All fields are mandatory.")

# Detailed Table View
if st.checkbox("📖 View Detailed History"):
    if not user_records.empty:
        st.dataframe(
            user_records.sort_values(by=["Date", "Time"], ascending=False), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No records found for your account.")

# Sidebar Logout
if st.sidebar.button("Logout"):
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
