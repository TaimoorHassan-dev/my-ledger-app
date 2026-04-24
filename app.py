import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIGURATION & FORCED BRANDING REMOVAL ---
st.set_page_config(
    page_title="Zarkash Digital Ledger", 
    layout="centered", 
    page_icon="💸"
)

# Aggressive CSS to remove all Streamlit footers, headers, and branding
st.markdown("""
    <style>
    /* Absolute Force Hide for Footer and Header */
    header {visibility: hidden !important; display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    .stDeployButton {display:none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* Global Professional Styling */
    body { background-color: #0e1117; }
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #888; font-size: 16px; margin-bottom: 25px; }
    
    /* Metrics & Dashboard Styling */
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; color: #ffffff; }
    [data-testid="stMetricLabel"] { color: #aaaaaa; text-transform: uppercase; letter-spacing: 1px; font-size: 12px; }
    
    /* Form & Button Styling */
    [data-testid="stForm"] { border: 1px solid #333; border-radius: 15px; padding: 25px; background-color: #161a25; }
    .stButton>button { 
        width: 100%; 
        border-radius: 25px; 
        background-color: #FFD700; 
        color: black; 
        font-weight: bold; 
        border: none; 
        height: 50px;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #e6c200; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# Connection to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Initialize Session State for Authentication
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
                stored_p = str(users_df[users_df['Username'] == u]['Password'].values[0])
                if str(p) == stored_p:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("❌ Invalid Password.")
            else: st.error("❌ Username not found.")

    with auth_tab2:
        nu = st.text_input("New Username", key="s_user", placeholder="e.g. taimoor")
        np = st.text_input("New Password", type="password", key="s_pass")
        if st.button("Register Now"):
            if nu and np:
                users_df = conn.read(worksheet="Users", ttl=0)
                if nu in users_df['Username'].values: st.warning("⚠️ Username already taken.")
                else:
                    new_user = pd.DataFrame([{"Username": nu, "Password": np}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_user], ignore_index=True))
                    st.success("✅ Account created! Please Login.")
            else: st.warning("⚠️ Please fill all fields.")
    st.stop()

# --- 3. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Fetch Transactions
all_records = conn.read(worksheet="Sheet1", ttl=0)
user_records = all_records[all_records['Owner'] == st.session_state['username']]

# Financial Summary Metrics
if not user_records.empty:
    total_in = user_records[user_records['Amount'] > 0]['Amount'].sum()
    total_out = abs(user_records[user_records['Amount'] < 0]['Amount'].sum())
    current_bal = total_in - total_out

    st.markdown("### 📈 Performance Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income (+)", f"{total_in:,.0f}")
    c2.metric("Total Expense (-)", f"{total_out:,.0f}", delta_color="inverse")
    st.metric("Current Balance", f"{current_bal:,.0f}", delta=current_bal)
    st.markdown("---")

# New Entry Form
with st.expander("➕ Add New Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        p_name = col1.text_input("Person / Payee Name")
        p_amount = col1.number_input("Amount (PKR)", min_value=0.0, step=500.0)
        
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        t_date = col2.date_input("Date", datetime.now())
        
        p_reason = st.text_input("Purpose / Description")
        
        if st.form_submit_button("Save Transaction"):
            if p_name and p_amount > 0 and p_reason:
                # Logic: Negative value if 'Sent'
                val = p_amount if t_type == "Received (+)" else -p_amount
                
                new_row = pd.DataFrame([{
                    "Owner": st.session_state['username'],
                    "Name": p_name, "Amount": val, "Currency": "PKR",
                    "Type": t_type, "Date": t_date.strftime("%Y-%m-%d"),
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": p_reason
                }])
                
                conn.update(worksheet="Sheet1", data=pd.concat([all_records, new_row], ignore_index=True))
                st.success("✅ Transaction Saved Successfully!")
                st.rerun()
            else: st.error("⚠️ All fields are mandatory.")

# Detailed Data Table
st.markdown("---")
if st.checkbox("📖 View Detailed History"):
    if not user_records.empty:
        st.dataframe(
            user_records.sort_values(by=["Date", "Time"], ascending=False), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No transaction history available.")

# Sidebar Logout
if st.sidebar.button("Logout"):
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
