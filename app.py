import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
# Premium finance icon and clean title
st.set_page_config(
    page_title="Zarkash Digital Ledger", 
    layout="centered", 
    page_icon="💸"
)

# Custom UI Styling for a modern dark theme
st.markdown("""
    <style>
    /* Main Title Styling */
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #888; font-size: 16px; margin-bottom: 25px; }
    
    /* Input Form Styling */
    [data-testid="stForm"] { border: 1px solid #333; border-radius: 10px; padding: 20px; background-color: #111; }
    
    /* Metrics Styling - Similar to bank apps */
    [data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #888; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Primary Button Styling */
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FFD700; color: black; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #e6c200; color: black; }
    </style>
    """, unsafe_allow_html=True)

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Authentication Session State
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

# --- 1. AUTHENTICATION SECTION (English Only) ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Your Professional Digital Finance Ledger</p>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Secure Login", "📝 Create Account"])
    
    with auth_tab1:
        u = st.text_input("Username", key="l_user", placeholder="Enter your username")
        p = st.text_input("Password", type="password", key="l_pass", placeholder="Enter your password")
        if st.button("Enter Dashboard"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and u in users_df['Username'].values:
                correct_pass = users_df[users_df['Username'] == u]['Password'].values[0]
                if str(p) == str(correct_pass):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
                else: st.error("❌ Incorrect Password. Please try again.")
            else: st.error("❌ Username not found. Please register.")

    with auth_tab2:
        nu = st.text_input("Choose a Username", key="s_user", placeholder="e.g., taimoor")
        np = st.text_input("Choose a Password", type="password", key="s_pass", placeholder="Use a strong password")
        if st.button("Register & Get Started"):
            if nu and np:
                users_df = conn.read(worksheet="Users", ttl=0)
                if nu in users_df['Username'].values: st.warning("⚠️ Username already exists.")
                else:
                    new_u = pd.DataFrame([{"Username": nu, "Password": np}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_u], ignore_index=True))
                    st.success("✅ Account created successfully! Please proceed to Login.")
            else: st.warning("⚠️ All fields are required for registration.")
    st.stop()

# --- 2. MAIN APP DASHBOARD (English Only) ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].title()}'s Ledger</h1>", unsafe_allow_html=True)

# Data Reading
all_data = conn.read(worksheet="Sheet1", ttl=0)
# Filter for specific user
my_data = all_data[all_data['Owner'] == st.session_state['username']]

# --- FINANCIAL SUMMARY (Metrics Section) ---
if not my_data.empty:
    in_sum = my_data[my_data['Amount'] > 0]['Amount'].sum()
    out_sum = abs(my_data[my_data['Amount'] < 0]['Amount'].sum())
    balance = in_sum - out_sum

    st.markdown("### 📊 Financial Account Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Received (+)", f"PKR {in_sum:,.1f}")
    c2.metric("Total Sent (-)", f"PKR {out_sum:,.1f}", delta_color="inverse")
    # Dynamic balance delta
    st.metric("Net Balance", f"PKR {balance:,.1f}", delta=balance, help="Your current cash flow status.")
    st.markdown("---")

# --- ADD NEW ENTRY FORM ---
with st.expander("➕ Add New Transaction (Income / Expense)", expanded=True):
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Person/Entity Name", placeholder="e.g., Sagar Trading Co.")
        # Amount validation: Must be positive
        amount = col1.number_input("Amount (PKR)", min_value=0.0, step=100.0)
        
        t_type = col2.radio("Transaction Type", ["Received (+)", "Sent (-)"])
        t_date = col2.date_input("Transaction Date", datetime.now())
        
        reason = st.text_input("Description / Purpose", placeholder="e.g., Monthly Salary or Utility Bill")
        
        # Centered form submission button
        if st.form_submit_button("Mehfooz Karein"):
            if person and amount > 0 and reason:
                # Backend Logic: 'Sent' applies a negative value
                final_amount = amount if t_type == "Received (+)" else -amount
                
                new_entry = pd.DataFrame([{
                    "Owner": st.session_state['username'],
                    "Name": person, "Amount": final_amount, "Currency": "PKR",
                    "Type": t_type, "Date": t_date.strftime("%Y-%m-%d"),
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": reason
                }])
                
                # Append data to the main sheet
                conn.update(worksheet="Sheet1", data=pd.concat([all_data, new_entry], ignore_index=True))
                st.success("✅ Transaction recorded successfully!")
                st.rerun() # Refresh dashboard instantly
            else: st.error("⚠️ Error: Please complete all fields before saving.")

# --- TRANSACTION HISTORY (PROFESSIONAL TABLE) ---
st.markdown("---")
if st.checkbox("📖 View Detailed Transaction History"):
    if not my_data.empty:
        # Display professional, searchable dataframe
        st.dataframe(
            my_data.sort_values(by="Date", ascending=False), 
            use_container_width=True, 
            hide_index=True # Hides the row numbers
        )
    else:
        st.info("ℹ️ No transactions recorded yet. Use the form above to add your first entry.")

# Sidebar Logout Button
st.sidebar.button("Log Out", on_click=lambda: st.session_state.update({'logged_in': False, 'username': ""}))
