import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Pro Ledger", layout="centered", page_icon="🏦")

# --- Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Session State for Login ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- LOGIN / SIGNUP LOGIC ---
def login_user(user, pwd):
    try:
        users_df = conn.read(worksheet="Users", ttl=0)
        user_data = users_df[(users_df['Username'] == user) & (users_df['Password'] == pwd)]
        if not user_data.empty:
            return True
    except:
        return False
    return False

def signup_user(new_user, new_pwd):
    try:
        users_df = conn.read(worksheet="Users", ttl=0)
        if new_user in users_df['Username'].values:
            return "Exists"
        
        new_row = pd.DataFrame([{"Username": new_user, "Password": new_pwd}])
        updated_users = pd.concat([users_df, new_row], ignore_index=True)
        conn.update(worksheet="Users", data=updated_users)
        return "Success"
    except:
        # Agar sheet khali ho
        new_row = pd.DataFrame([{"Username": new_user, "Password": new_pwd}])
        conn.update(worksheet="Users", data=new_row)
        return "Success"

# --- AUTHENTICATION UI ---
if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab1:
        user = st.text_input("Username", key="l_user")
        pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            if login_user(user, pwd):
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.rerun()
            else:
                st.error("Ghalat Username ya Password")

    with tab2:
        new_user = st.text_input("Choose Username", key="s_user")
        new_pwd = st.text_input("Choose Password", type="password", key="s_pwd")
        if st.button("Create Account"):
            result = signup_user(new_user, new_pwd)
            if result == "Success":
                st.success("Account ban gaya! Ab Login tab mein jayein.")
            elif result == "Exists":
                st.warning("Ye Username pehle se maujood hai.")

    st.stop()

# --- ACTUAL LEDGER (After Login) ---
st.title(f"🏦 {st.session_state['username']}'s Ledger")
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "username": ""}))

# --- FORM ---
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        person = col1.text_input("Person Name")
        amt = col1.number_input("Amount", min_value=0.0)
        curr = col2.selectbox("Currency", ["PKR", "USD", "EUR"])
        cat = col2.radio("Type", ["Received (+)", "Sent (-)"])
        
        date_val = st.date_input("Date", datetime.now())
        reason = st.text_input("Reason")
        submit = st.form_submit_button("Save Record")

if submit and person and amt > 0:
    # Main Transaction Sheet Read karein (Sheet1)
    df = conn.read(worksheet="Sheet1", ttl=0)
    
    final_amt = amt if cat == "Received (+)" else -amt
    new_entry = pd.DataFrame([{
        "Owner": st.session_state['username'], # User ka naam save ho raha hai
        "Name": person, "Amount": final_amt, "Currency": curr,
        "Type": cat, "Date": date_val.strftime("%Y-%m-%d"), "Reason": reason
    }])
    
    updated_df = pd.concat([df, new_entry], ignore_index=True)
    conn.update(worksheet="Users", data=updated_df) # Note: Yahan worksheet check karein
    st.success("Saved!")
    st.balloons()

# --- HISTORY ---
if st.checkbox("Show My History"):
    history = conn.read(worksheet="Sheet1", ttl=0)
    # Sirf us bande ka data dikhao jo login hai
    user_history = history[history['Owner'] == st.session_state['username']]
    st.dataframe(user_history.sort_values("Date", ascending=False))
