import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; margin-bottom: 10px; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #161a25; border-radius: 5px; padding: 10px 20px; color: white; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})
if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# --- LOGIN LOGIC ---
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    tab_log, tab_reg = st.tabs(["🔐 Login", "📝 Register"])
    with tab_log:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
            else: st.error("Invalid Credentials")
    st.stop()

# --- 4. DATA LOADING ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
if not all_recs.empty:
    all_recs['Date'] = pd.to_datetime(all_recs['Date'], errors='coerce')
    all_recs = all_recs.dropna(subset=['Date'])

# --- 5. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)
tab_personal, tab_insights, tab_master = st.tabs(["📊 My Ledger", "📈 Insights", "🏛️ Master Logic"])

with tab_personal:
    my_recs = all_recs[all_recs['Owner'] == st.session_state['username']] if not all_recs.empty else pd.DataFrame()
    t_rec = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
    t_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
    net_bal = t_rec - t_sent

    st.markdown("### 📊 Status")
    c1, c2 = st.columns(2)
    c1.metric("Received", f"{t_rec:,.0f}")
    c2.metric("Sent", f"{t_sent:,.0f}")
    st.metric("Net Balance", f"PKR {net_bal:,.0f}")

    if st.session_state['confirm_mode']:
        preview = st.session_state['temp_data']
        st.warning("⚠️ **VERIFY DETAILS**")
        st.markdown(f"""<div class="confirm-card">
            <b>Name:</b> {preview['Name']}<br>
            <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
            <b>Action:</b> {preview['Type']}</div>""", unsafe_allow_html=True)
        
        col_y, col_n = st.columns(2)
        if col_y.button("✅ Confirm & Save"):
            # Naya record add karna
            new_row = pd.DataFrame([preview])
            updated_df = pd.concat([all_recs, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.success("Record Saved Successfully!")
            st.rerun()
        if col_n.button("❌ Edit"):
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.rerun()
    else:
        with st.expander("➕ Add Transaction", expanded=True):
            with st.form("entry_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                n_in = col1.text_input("Name")
                a_in = col1.number_input("Amount", min_value=0.0)
                d_in = col2.date_input("Date", datetime.now())
                t_in = col2.time_input("Time", datetime.now().time())
                type_in = st.radio("Action", ["Received (+)", "Withdraw (-)"], horizontal=True)
                r_in = st.text_input("Reason")
                
                if st.form_submit_button("Preview"):
                    if n_in and a_in > 0:
                        st.session_state['temp_data'] = {
                            "Owner": st.session_state['username'], 
                            "Name": n_in, 
                            "Amount": a_in if type_in == "Received (+)" else -a_in,
                            "Currency": "PKR", 
                            "Type": type_in, 
                            "Date": d_in.strftime("%Y-%m-%d"), 
                            "Time": t_in.strftime("%H:%M:%S"), 
                            "Reason": r_in, 
                            "Balance": net_bal + (a_in if type_in == "Received (+)" else -a_in)
                        }
                        st.session_state['confirm_mode'] = True
                        st.rerun()

    st.markdown("### 📖 View History")
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True, hide_index=True)

with tab_insights:
    st.markdown("### 📈 Amount Analysis")
    if not all_recs.empty:
        df_c = all_recs.copy()
        df_c['Month'] = df_c['Date'].dt.strftime('%b')
        user_sums = df_c[df_c['Amount'] > 0].groupby(['Owner', 'Month'])['Amount'].sum().reset_index()
        fig = px.bar(user_sums, x='Month', y="Amount", color="Owner", barmode="group", color_discrete_sequence=["#FFD700", "#1E90FF"])
        st.plotly_chart(fig, use_container_width=True)

with tab_master:
    if not all_recs.empty:
        master_summary = all_recs.groupby('Owner')['Amount'].sum().reset_index()
        master_summary.columns = ['User', 'Net Balance']
        st.table(master_summary)

if st.button("Logout"):
    st.session_state.clear()
    st.rerun()
