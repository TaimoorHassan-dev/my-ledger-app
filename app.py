import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Zarkash Ledger", 
    layout="centered", 
    page_icon="💰"
)

# Custom Styling
st.markdown("""
    <style>
    .main-title { color: #FFD700; text-align: center; font-size: 40px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FFD700; color: black; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Session State for Authentication
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- 1. AUTHENTICATION SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ Zarkash Ledger</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Apne Maali Hisab Kitab ka Jadeed Hal</p>", unsafe_allow_html=True)
    
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with auth_tab1:
        l_user = st.text_input("Username", key="l_user")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login Access"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and l_user in users_df['Username'].values:
                correct_pass = users_df[users_df['Username'] == l_user]['Password'].values[0]
                if str(l_pass) == str(correct_pass):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = l_user
                    st.rerun()
                else: st.error("❌ Password durust nahi hai.")
            else: st.error("❌ User nahi mila. Pehle account banayein.")

    with auth_tab2:
        s_user = st.text_input("Chunain Username", key="s_user")
        s_pass = st.text_input("Chunain Password", type="password", key="s_pass")
        if st.button("Create My Account"):
            if not s_user or not s_pass:
                st.warning("Username aur Password likhna zaroori hai.")
            else:
                users_df = conn.read(worksheet="Users", ttl=0)
                if not users_df.empty and s_user in users_df['Username'].values:
                    st.warning("Ye Username pehle se maujood hai.")
                else:
                    new_u = pd.DataFrame([{"Username": s_user, "Password": s_pass}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_u], ignore_index=True))
                    st.success("✅ Account ban gaya! Ab Login tab par jayein.")
    st.stop()

# --- 2. MAIN LEDGER SECTION ---
st.markdown(f"<h1 class='main-title'>✨ Zarkash Ledger</h1>", unsafe_allow_html=True)
st.sidebar.markdown(f"### 👤 User: {st.session_state['username']}")

# Transaction Form
with st.expander("➕ Nayi Transaction Shamil Karein", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            person = st.text_input("Naam (Person Name)")
            amount = st.number_input("Raqam (Amount)", min_value=0.0, step=10.0)
            t_date = st.date_input("Tareekh (Date)", datetime.now())
        with col2:
            t_type = st.radio("Type", ["Received (+)", "Sent (-)"])
            currency = st.selectbox("Currency", ["PKR", "USD", "AED"])
            t_time = st.time_input("Waqt (Time)", datetime.now().time())
        
        reason = st.text_input("Wajah (Reason / Purpose)")
        save_btn = st.form_submit_button("Mehfooz Karein (Save Record)")

# Validation and Saving Logic
if save_btn:
    # Condition: Jab tak tamam cheezein fill nahi hongi, save nahi hoga
    if not person or amount <= 0 or not reason:
        st.error("⚠️ Record save nahi hua! Naam, Raqam aur Wajah likhna lazmi hai.")
    else:
        try:
            main_df = conn.read(worksheet="Sheet1", ttl=0)
            final_amt = amount if t_type == "Received (+)" else -amount
            
            new_record = pd.DataFrame([{
                "Owner": st.session_state['username'],
                "Name": person,
                "Amount": final_amt,
                "Currency": currency,
                "Type": t_type,
                "Date": t_date.strftime("%Y-%m-%d"),
                "Time": t_time.strftime("%H:%M:%S"),
                "Reason": reason
            }])
            
            updated_data = pd.concat([main_df, new_record], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_data)
            st.success("✅ Shabaash! Record kamyabi se save ho gaya.")
            st.balloons()
        except Exception as e:
            st.error("Kuch masla hua, data save nahi ho saka.")

# --- 3. HISTORY SECTION ---
st.markdown("---")
if st.checkbox("📖 Meri History Dekhein"):
    history_df = conn.read(worksheet="Sheet1", ttl=0)
    # Filter for logged in user
    if not history_df.empty:
        my_history = history_df[history_df['Owner'] == st.session_state['username']]
        if not my_history.empty:
            st.dataframe(my_history.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True)
        else:
            st.info("Aapka koi record nahi mila.")

# Logout
if st.sidebar.button("Log Out"):
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.rerun()
