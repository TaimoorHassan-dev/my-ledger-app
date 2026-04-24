import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# Custom CSS for Styling
st.markdown("""
    <style>
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; }
    /* Minus amount ko red dikhane ke liye */
    .minus-text { color: #ff4b4b; font-weight: bold; }
    /* Plus amount ko green dikhane ke liye */
    .plus-text { color: #00ff00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- AUTHENTICATION (Login/Signup) ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ Zarkash Ledger</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    with tab1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({"logged_in": True, "username": u})
                    st.rerun()
                else: st.error("Ghalat Password")
            else: st.error("User nahi mila")
    with tab2:
        nu, np = st.text_input("New Username", key="s_u")
        if st.button("Register"):
            users = conn.read(worksheet="Users", ttl=0)
            if nu in users['Username'].values: st.warning("Username taken")
            else:
                conn.update(worksheet="Users", data=pd.concat([users, pd.DataFrame([{"Username": nu, "Password": "123"}])], ignore_index=True))
                st.success("Registered!")
    st.stop()

# --- MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username']}'s Ledger</h1>", unsafe_allow_html=True)

# Data Reading
all_data = conn.read(worksheet="Sheet1", ttl=0)
my_data = all_data[all_data['Owner'] == st.session_state['username']]

# --- CALCULATION LOGIC (Addition & Subtraction) ---
if not my_data.empty:
    # Received (+) ko jama karein
    total_in = my_data[my_data['Amount'] > 0]['Amount'].sum()
    # Sent (-) ko jama karein (lekin display ke liye positive dikhayenge)
    total_out = abs(my_data[my_data['Amount'] < 0]['Amount'].sum())
    # Asli Balance: IN - OUT
    net_balance = total_in - total_out

    st.markdown("### 📊 Hisab Kitab Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Kul Aamad (+)", f"{total_in:,}")
    c2.metric("Kul Kharcha (-)", f"{total_out:,}", delta_color="inverse")
    
    # Balance agar negative ho jaye toh red dikhayega
    st.metric("Maujooda Balance", f"{net_balance:,}", delta=net_balance, delta_color="normal")
    st.markdown("---")

# --- TRANSACTION FORM ---
with st.expander("➕ Nayi Entry (Aamad ya Kharcha)", expanded=True):
    with st.form("ledger_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Naam")
        amount = col1.number_input("Raqam (Amount)", min_value=0.0)
        
        # Yahan se "Sent (-)" select karne par minus logic chalegi
        t_type = col2.radio("Naoiyat (Type)", ["Received (+)", "Sent (-)"])
        date_v = st.date_input("Tareekh", datetime.now())
        reason = st.text_input("Wajah (Reason)")
        
        if st.form_submit_button("Save Record"):
            if person and amount > 0:
                # LOGIC: Agar "Sent" hai toh raqam ke saath (-) laga do
                final_amt = amount if t_type == "Received (+)" else -amount
                
                new_row = pd.DataFrame([{
                    "Owner": st.session_state['username'],
                    "Name": person,
                    "Amount": final_amt,
                    "Currency": "PKR",
                    "Type": t_type,
                    "Date": date_v.strftime("%Y-%m-%d"),
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Reason": reason
                }])
                conn.update(worksheet="Sheet1", data=pd.concat([all_data, new_row], ignore_index=True))
                st.success(f"Record mehfooz! {'Minus' if final_amt < 0 else 'Plus'} entry ho gayi.")
                st.rerun()
            else: st.error("Naam aur Raqam likhna zaroori hai!")

# --- HISTORY VIEW ---
if st.checkbox("📖 Show Detail History"):
    if not my_data.empty:
        # Visual styling for dataframe
        st.dataframe(my_data.sort_values(by=["Date"], ascending=False), use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state.update({"logged_in": False, "username": ""})
    st.rerun()
