import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Page Settings
st.set_page_config(page_title="Pro Ledger", layout="centered", page_icon="🏦")

# Connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- LOGIN / SIGNUP LOGIC ---
if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Member Access</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and u in users_df['Username'].values:
                # Password check logic
                stored_pwd = users_df[users_df['Username'] == u]['Password'].values[0]
                if str(p) == str(stored_pwd):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = u
                    st.rerun()
                else: st.error("Password ghalat hai!")
            else: st.error("User nahi mila! Pehle Sign Up karein.")

    with tab2:
        new_u = st.text_input("New Username", key="reg_user")
        new_p = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register Now"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and new_u in users_df['Username'].values:
                st.warning("Ye naam pehle se istemal mein hai.")
            else:
                new_user_data = pd.DataFrame([{"Username": new_u, "Password": new_p}])
                updated_users = pd.concat([users_df, new_user_data], ignore_index=True)
                conn.update(worksheet="Users", data=updated_users)
                st.success("Account ban gaya! Ab Login tab mein ja kar login karein.")
    st.stop()

# --- MAIN DASHBOARD (After Login) ---
st.title(f"🏦 {st.session_state['username']}'s Ledger")
st.sidebar.write(f"Logged in as: **{st.session_state['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.update({"logged_in": False, "username": ""})
    st.rerun()

# Transaction Form
with st.expander("➕ Nayi Entry Shamil Karein", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Kise diye / Kis se liye?")
        amt = col1.number_input("Raqam (Amount)", min_value=0.0)
        curr = col2.selectbox("Currency", ["PKR", "USD", "EUR"])
        cat = col2.radio("Type", ["Received (+)", "Sent (-)"])
        date_v = st.date_input("Date", datetime.now())
        reason = st.text_input("Wajah (Reason)")
        
        if st.form_submit_button("Data Save Karein"):
            # Pehle purana data read karein
            all_data = conn.read(worksheet="Sheet1", ttl=0)
            
            # Nayi row taiyar karein
            final_amt = amt if cat == "Received (+)" else -amt
            new_entry = pd.DataFrame([{
                "Owner": st.session_state['username'],
                "Name": person, "Amount": final_amt, "Currency": curr,
                "Type": cat, "Date": date_v.strftime("%Y-%m-%d"), "Reason": reason
            }])
            
            # Update Sheet
            updated_sheet = pd.concat([all_data, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_sheet)
            st.success("Record mehfooz ho gaya!")
            st.balloons()

# History Section
st.markdown("---")
if st.checkbox("📖 Meri History Dekhein"):
    history = conn.read(worksheet="Sheet1", ttl=0)
    # SECURITY FILTER: Sirf login bande ka data filter karein
    my_records = history[history['Owner'] == st.session_state['username']]
    
    if not my_records.empty:
        st.dataframe(my_records.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("Aapka abhi tak koi record nahi hai.")
