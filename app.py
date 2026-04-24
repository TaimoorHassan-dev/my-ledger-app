import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

conn = st.connection("gsheets", type=GSheetsConnection)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- AUTHENTICATION SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>✨ Zarkash Ledger</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
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
            else: st.error("❌ User nahi mila.")

    with tab2:
        s_user = st.text_input("New Username", key="s_user")
        s_pass = st.text_input("New Password", type="password", key="s_pass")
        if st.button("Create My Account"):
            if s_user and s_pass:
                users_df = conn.read(worksheet="Users", ttl=0)
                if s_user in users_df['Username'].values:
                    st.warning("Ye naam pehle se maujood hai.")
                else:
                    # 1. User ko 'Users' sheet mein add karein
                    new_u = pd.DataFrame([{"Username": s_user, "Password": s_pass}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_u], ignore_index=True))
                    
                    # 2. Naye User ke liye alag sheet (Tab) banayein
                    empty_df = pd.DataFrame(columns=["Name", "Amount", "Currency", "Type", "Date", "Time", "Reason"])
                    # Streamlit GSheets connection naya tab banane ke liye conn.update hi use karta hai
                    conn.update(worksheet=s_user, data=empty_df)
                    
                    st.success(f"✅ Account ban gaya! Aapki personal sheet '{s_user}' bhi ban gayi hai.")
            else:
                st.warning("Fields fill karein.")
    st.stop()

# --- MAIN LEDGER SECTION ---
st.title(f"🏦 {st.session_state['username']}'s Ledger")

# Transaction Form
with st.expander("➕ Nayi Transaction", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Naam")
        amount = col1.number_input("Raqam", min_value=0.0)
        t_date = st.date_input("Date", datetime.now())
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        currency = col2.selectbox("Currency", ["PKR", "USD"])
        t_time = col2.time_input("Time", datetime.now().time())
        reason = st.text_input("Wajah")
        save_btn = st.form_submit_button("Save Record")

if save_btn:
    if not person or amount <= 0 or not reason:
        st.error("⚠️ Sab fields bharna zaroori hain!")
    else:
        try:
            # Sirf is user ki apni sheet read karein
            user_sheet = st.session_state['username']
            current_df = conn.read(worksheet=user_sheet, ttl=0)
            
            final_amt = amount if t_type == "Received (+)" else -amount
            new_record = pd.DataFrame([{
                "Name": person, "Amount": final_amt, "Currency": currency,
                "Type": t_type, "Date": t_date.strftime("%Y-%m-%d"),
                "Time": t_time.strftime("%H:%M:%S"), "Reason": reason
            }])
            
            updated_data = pd.concat([current_df, new_record], ignore_index=True)
            conn.update(worksheet=user_sheet, data=updated_data)
            st.success("✅ Record aapki personal sheet mein save ho gaya!")
        except:
            st.error("Sheet access mein masla hai.")

# History
if st.checkbox("📖 Show History"):
    my_data = conn.read(worksheet=st.session_state['username'], ttl=0)
    st.dataframe(my_data.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True)

if st.sidebar.button("Log Out"):
    st.session_state.update({"logged_in": False, "username": ""})
    st.rerun()
