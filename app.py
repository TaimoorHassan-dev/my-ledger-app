import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG & BRANDING REMOVAL ---
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰"
)

# Deep Injection CSS to remove Streamlit footer and style the app
st.markdown("""
    <style>
    /* Force Hide All Streamlit Branding */
    footer {display: none !important; visibility: hidden !important; height: 0px !important;}
    header {display: none !important; visibility: hidden !important; height: 0px !important;}
    [data-testid="stHeader"], [data-testid="stFooter"], .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* Premium Styling */
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #888; font-size: 14px; margin-bottom: 25px; }
    
    /* Metrics & Forms */
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; color: #ffffff; }
    [data-testid="stForm"] { border: 1px solid #333; border-radius: 15px; background-color: #161a25; padding: 20px; }
    
    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 25px; background-color: #FFD700; 
        color: black; font-weight: bold; height: 50px; border: none;
    }
    
    /* Confirmation Box */
    .confirm-card { 
        background-color: #1e2433; padding: 20px; border: 2px solid #FFD700; 
        border-radius: 12px; margin-bottom: 20px; 
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. REFRESH-PROOF LOGIN LOGIC ---
query_params = st.query_params
url_user = query_params.get("user", "")

if 'logged_in' not in st.session_state:
    if url_user:
        st.session_state.update({'logged_in': True, 'username': url_user})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 3. AUTHENTICATION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Professional Digital Finance Management</p>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Login", "📝 Create Account"])
    
    with t1:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Log In"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and u in users_df['Username'].values:
                stored_p = str(users_df[users_df['Username'] == u]['Password'].values[0])
                if str(p) == stored_p:
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.query_params["user"] = u # Save in URL to handle refresh
                    st.rerun()
                else: st.error("❌ Incorrect Password.")
            else: st.error("❌ User not found.")
            
    with t2:
        nu = st.text_input("Choose Username", key="s_user")
        np = st.text_input("Choose Password", type="password", key="s_pass")
        if st.button("Register Account"):
            if nu and np:
                users_df = conn.read(worksheet="Users", ttl=0)
                if nu in users_df['Username'].values: st.warning("Username exists.")
                else:
                    new_user = pd.DataFrame([{"Username": nu, "Password": np}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_user], ignore_index=True))
                    st.success("✅ Registered! Please Login.")
    st.stop()

# --- 4. MAIN INTERFACE ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

all_recs = conn.read(worksheet="Sheet1", ttl=0)
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# --- CONFIRMATION VALIDATION SCREEN ---
if st.session_state['confirm_mode']:
    preview = st.session_state['temp_data']
    st.warning("⚠️ **CONFIRM TRANSACTION DETAILS**")
    st.markdown(f"""
    <div class="confirm-card">
        <b>Name:</b> {preview['Name']}<br>
        <b>Amount:</b> PKR {abs(preview['Amount']):,.1f}<br>
        <b>Transaction Type:</b> {preview['Type']}<br>
        <b>Reason:</b> {preview['Reason']}<br>
        <b>Date:</b> {preview['Date']}
    </div>
    """, unsafe_allow_html=True)
    
    col_y, col_n = st.columns(2)
    if col_y.button("✅ Confirm & Save"):
        conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
        st.success("Transaction Successfully Recorded!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if col_n.button("❌ Cancel / Edit"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- INPUT FORM ---
with st.expander("➕ Add New Transaction", expanded=True):
    with st.form("main_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        person = c1.text_input("Person/Entity Name")
        amount = c1.number_input("Amount (PKR)", min_value=0.0, step=100.0)
        t_type = c2.radio("Type", ["Received (+)", "Sent (-)"])
        date_v = c2.date_input("Date", datetime.now())
        reason = st.text_input("Description / Reason")
        
        if st.form_submit_button("Preview & Save"):
            if person and amount > 0 and reason:
                # Logic: Negative value for expenses
                final_val = amount if t_type == "Received (+)" else -amount
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": person, 
                    "Amount": final_val, "Currency": "PKR", "Type": t_type, 
                    "Date": date_v.strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": reason
                }
                st.session_state['confirm_mode'] = True
                st.rerun()
            else: st.error("⚠️ All fields are required.")

# Account Summary
if not my_recs.empty:
    total_in = my_recs[my_recs['Amount'] > 0]['Amount'].sum()
    total_out = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum())
    balance = total_in - total_out
    
    st.markdown("### 📊 Account Summary")
    m1, m2, m3 = st.columns(3)
    m1.metric("Income (+)", f"{total_in:,.0f}")
    m2.metric("Expenses (-)", f"{total_out:,.0f}")
    st.metric("Net Balance", f"{balance:,.0f}", delta=balance)
    st.markdown("---")

# History View
if st.checkbox("📖 View Detailed History"):
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# Sidebar Logout (Clears URL)
if st.sidebar.button("Logout"):
    st.query_params.clear()
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
