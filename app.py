import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. APP CONFIG & BRANDING REMOVAL ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

st.markdown("""
    <style>
    footer {display: none !important; visibility: hidden !important;}
    header {display: none !important; visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stFooter"] {display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 38px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 25px; background-color: #FFD700; color: black; font-weight: bold; height: 50px; }
    .confirm-box { background-color: #161a25; padding: 20px; border: 1px solid #FFD700; border-radius: 10px; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. REFRESH-PROOF LOGIC (URL Persistence) ---
# URL se login status check karein
query_params = st.query_params
url_user = query_params.get("user", "")

if 'logged_in' not in st.session_state:
    if url_user: # Agar URL mein user hai toh login rakho
        st.session_state.update({'logged_in': True, 'username': url_user})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- 3. AUTHENTICATION SECTION ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>✨ ZARKASH</h1>", unsafe_allow_html=True)
    auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with auth_tab1:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pass")
        if st.button("Access Dashboard"):
            users_df = conn.read(worksheet="Users", ttl=0)
            if not users_df.empty and u in users_df['Username'].values:
                stored_p = str(users_df[users_df['Username'] == u]['Password'].values[0])
                if str(p) == stored_p:
                    st.session_state.update({'logged_in': True, 'username': u})
                    # URL mein user save karein taake refresh par ghaib na ho
                    st.query_params["user"] = u
                    st.rerun()
                else: st.error("❌ Invalid Password")
            else: st.error("❌ User not found")
    
    with auth_tab2:
        nu = st.text_input("New Username", key="s_user")
        np = st.text_input("New Password", type="password", key="s_pass")
        if st.button("Register & Join"):
            if nu and np:
                users_df = conn.read(worksheet="Users", ttl=0)
                if nu in users_df['Username'].values: st.warning("Username taken")
                else:
                    new_u = pd.DataFrame([{"Username": nu, "Password": np}])
                    conn.update(worksheet="Users", data=pd.concat([users_df, new_u], ignore_index=True))
                    st.success("✅ Registered! Now Login.")
    st.stop()

# --- 4. MAIN LEDGER (REFRESH STABLE) ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

all_records = conn.read(worksheet="Sheet1", ttl=0)
my_records = all_records[all_records['Owner'] == st.session_state['username']]

# --- CONFIRMATION PREVIEW ---
if st.session_state['confirm_mode']:
    t_data = st.session_state['temp_data']
    st.warning("⚠️ **CHECK AGAIN: IS THIS CORRECT?**")
    st.markdown(f"""
    <div class="confirm-box">
        <b>Payee:</b> {t_data['Name']}<br>
        <b>Amount:</b> PKR {abs(t_data['Amount']):,}<br>
        <b>Type:</b> {t_data['Type']}<br>
        <b>Reason:</b> {t_data['Reason']}
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Yes, Save Now"):
        conn.update(worksheet="Sheet1", data=pd.concat([all_records, pd.DataFrame([t_data])], ignore_index=True))
        st.success("Transaction Secured!")
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    if c2.button("❌ No, Fix it"):
        st.session_state.update({'confirm_mode': False, 'temp_data': None})
        st.rerun()
    st.stop()

# --- ENTRY FORM ---
with st.expander("➕ Add Transaction", expanded=True):
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("Name")
        amt = col1.number_input("Amount", min_value=0.0, step=500.0)
        t_type = col2.radio("Type", ["Received (+)", "Sent (-)"])
        date = col2.date_input("Date", datetime.now())
        reason = st.text_input("Description")
        
        if st.form_submit_button("Preview & Save"):
            if name and amt > 0:
                val = amt if t_type == "Received (+)" else -amt
                st.session_state['temp_data'] = {
                    "Owner": st.session_state['username'], "Name": name, 
                    "Amount": val, "Type": t_type, "Date": date.strftime("%Y-%m-%d"), 
                    "Time": datetime.now().strftime("%H:%M:%S"), "Reason": reason
                }
                st.session_state['confirm_mode'] = True
                st.rerun()

# Metrics Summary
if not my_records.empty:
    tin = my_records[my_records['Amount'] > 0]['Amount'].sum()
    tout = abs(my_records[my_records['Amount'] < 0]['Amount'].sum())
    st.markdown("### 📊 Account Status")
    m1, m2, m3 = st.columns(3)
    m1.metric("Received", f"{tin:,.0f}")
    m2.metric("Sent", f"{tout:,.0f}")
    st.metric("Net Balance", f"{(tin-tout):,.0f}", delta=(tin-tout))

# History
if st.checkbox("📖 View History"):
    st.dataframe(my_records.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)

# --- LOGOUT (Clears URL) ---
if st.sidebar.button("Logout"):
    st.query_params.clear() # URL se user ghaib karein
    st.session_state.update({'logged_in': False, 'username': ""})
    st.rerun()
