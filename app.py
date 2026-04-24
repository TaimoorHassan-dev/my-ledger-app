import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #FFD700; color: black; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- AUTHENTICATION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ Zarkash Ledger</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        l_user = st.text_input("Username", key="l_user")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and l_user in users_df['Username'].values:
                correct_pass = users_df[users_df['Username'] == l_user]['Password'].values[0]
                if str(l_pass) == str(correct_pass):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = l_user
                    st.rerun()
                else: st.error("❌ Password ghalat hai.")
            else: st.error("❌ User nahi mila.")

    with tab2:
        s_user = st.text_input("New Username", key="s_user")
        s_pass = st.text_input("New Password", type="password", key="s_pass")
        if st.button("Create Account"):
            if s_user and s_pass:
                users_df = conn.read(worksheet="Users", ttl=0)
                if s_user in users_df['Username'].values:
                    st.warning("Username pehle se maujood hai.")
                else:
                    new_u = pd.DataFrame([{"Username": s_user, "Password": s_pass}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_u], ignore_index=True))
                    st.success("✅ Account ban gaya! Ab Login karein.")
            else: st.warning("Fields bharein.")
    st.stop()

# --- MAIN LEDGER ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username']}'s Ledger</h1>", unsafe_allow_html=True)

with st.expander("➕ Nayi Entry Karein", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Naam (Name)")
        amount = col1.number_input("Raqam (Amount)", min_value=0.0)
        t_date = st.date_input("Date", datetime.now())
        
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        currency = col2.selectbox("Currency", ["PKR", "USD", "AED"])
        t_time = col2.time_input("Time", datetime.now().time())
        
        reason = st.text_input("Wajah (Reason)")
        save_btn = st.form_submit_button("Save Record")

if save_btn:
    if not person or amount <= 0 or not reason:
        st.error("⚠️ Sab fields bharna zaroori hain!")
    else:
        try:
            # Aik hi main sheet read hogi (Sheet1)
            main_df = conn.read(worksheet="Sheet1", ttl=0)
            final_amt = amount if t_type == "Received (+)" else -amount
            
            new_record = pd.DataFrame([{
                "Owner": st.session_state['username'], # Ye pehchan hai ke data kis ka hai
                "Name": person, "Amount": final_amt, "Currency": currency,
                "Type": t_type, "Date": t_date.strftime("%Y-%m-%d"),
                "Time": t_time.strftime("%H:%M:%S"), "Reason": reason
            }])
            
            conn.update(worksheet="Sheet1", data=pd.concat([main_df, new_record], ignore_index=True))
            st.success("✅ Record save ho gaya!")
            st.balloons()
        except:
            st.error("Data save karne mein masla hua.")

# --- HISTORY WITH PRIVACY FILTER ---
st.markdown("---")
if st.checkbox("📖 Meri Transaction History"):
    all_data = conn.read(worksheet="Sheet1", ttl=0)
    if not all_data.empty:
        # 🔒 Privacy Filter: Sirf wo data dikhao jahan Owner login wale user ke barabar ho
        my_data = all_data[all_data['Owner'] == st.session_state['username']]
        if not my_data.empty:
            st.dataframe(my_data.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True)
        else:
            st.info("Aapka abhi tak koi record nahi hai.")

if st.sidebar.button("Log Out"):
    st.session_state.update({"logged_in": False, "username": ""})
    st.rerun()
