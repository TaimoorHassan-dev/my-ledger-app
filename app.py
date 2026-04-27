import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px # Graph ke liye mandatory hai

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# --- 2. UI STYLING ---
st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #FFD700; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    .confirm-card { background-color: #161a25; padding: 20px; border: 1px solid #333; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { background-color: #161a25; border-radius: 5px; padding: 10px 20px; color: white; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. SESSION & LOGIN ---
if 'logged_in' not in st.session_state:
    user_in_url = st.query_params.get("user", "")
    if user_in_url:
        st.session_state.update({'logged_in': True, 'username': user_in_url})
    else:
        st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Enter Dashboard"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.rerun()
    st.stop()

# --- 4. DATA LOADING ---
all_recs = conn.read(worksheet="Sheet1", ttl=0)
if not all_recs.empty:
    all_recs['Date'] = pd.to_datetime(all_recs['Date'], errors='coerce')
    all_recs = all_recs.dropna(subset=['Date'])

st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)
tab_personal, tab_master = st.tabs(["📊 My Ledger", "🏛️ Master Logic"])

my_recs = all_recs[all_recs['Owner'] == st.session_state['username']] if not all_recs.empty else pd.DataFrame()

with tab_personal:
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
        st.markdown(f"""<div class="confirm-card"><b>Name:</b> {preview['Name']}<br><b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br><b>Action:</b> {preview['Type']}</div>""", unsafe_allow_html=True)
        cy, cn = st.columns(2)
        if cy.button("✅ Confirm & Save"):
            fresh_recs = conn.read(worksheet="Sheet1", ttl=0)
            preview['Balance'] = net_bal + preview['Amount']
            updated_df = pd.concat([fresh_recs, pd.DataFrame([preview])], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.success("Saved!"); st.rerun()
        if cn.button("❌ Edit"):
            st.session_state.update({'confirm_mode': False, 'temp_data': None}); st.rerun()
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
                            "Owner": st.session_state['username'], "Name": n_in, 
                            "Amount": a_in if type_in == "Received (+)" else -a_in, 
                            "Currency": "PKR", "Type": type_in, "Date": d_in.strftime("%Y-%m-%d"), 
                            "Time": t_in.strftime("%H:%M:%S"), "Reason": r_in, "Balance": 0.0
                        }
                        st.session_state['confirm_mode'] = True; st.rerun()

    st.markdown("### 📖 View History")
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True, hide_index=True)

# --- MASTER LOGIC AREA WITH ANALYSIS ---
with tab_master:
    st.markdown("### 🏛️ Back-hand Master Logic")
    if not all_recs.empty:
        # Total Cash Metric
        total_pool = all_recs['Amount'].sum()
        st.metric("Total System Cash", f"PKR {total_pool:,.0f}")
        
        # 📈 NEW ANALYSIS FEATURE: Top Senders
        st.markdown("#### 🏆 Top User Analysis")
        # Sirf positive transactions (Received) count karein
        sent_data = all_recs[all_recs['Amount'] > 0].groupby('Owner')['Amount'].sum().reset_index()
        sent_data = sent_data.sort_values(by='Amount', ascending=False)
        
        if not sent_data.empty:
            fig = px.bar(sent_data, x='Owner', y='Amount', 
                         title="Most Active Senders (Total PKR Received)",
                         labels={'Owner': 'User', 'Amount': 'Total Money Sent'},
                         color='Amount', color_continuous_scale='Sunset')
            st.plotly_chart(fig, use_container_width=True)
            
            # Ranking Table
            st.write("#### Ranking Table")
            st.table(sent_data.rename(columns={'Owner': 'User', 'Amount': 'Total Contribution'}))
        else:
            st.info("No transaction data available for analysis.")

if st.button("Logout"):
    st.session_state.clear(); st.rerun()
