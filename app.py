import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px

# --- 1. APP CONFIG & STYLING ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

st.markdown("""
    <style>
    header, footer, .stDeployButton, #MainMenu {visibility: hidden !important; display: none !important;}
    .main-title { color: #ffffff; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #FFD700; color: black; font-weight: bold; height: 45px; }
    /* Purana style wapis lane ke liye metrics design */
    [data-testid="stMetricValue"] { font-size: 40px; font-weight: bold; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. SESSION & LOGIN (As per your original) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': ""})

if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    # ... (Aapka purana login logic yahan aayega)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Enter Dashboard"):
        users = conn.read(worksheet="Users", ttl=0)
        if not users.empty and u in users['Username'].values:
            if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                st.session_state.update({'logged_in': True, 'username': u})
                st.rerun()
    st.stop()

# --- 3. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Tabs style ko purnay jaisa rakha hai
tab_personal, tab_insights, tab_master = st.tabs(["📊 My Ledger", "📈 Insights", "🏛️ Master Logic"])

all_recs = conn.read(worksheet="Sheet1", ttl=0)
all_recs['Date'] = pd.to_datetime(all_recs['Date'])

# --- TAB 1: MY LEDGER (Purna Design) ---
with tab_personal:
    my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]
    
    # Wohi bare numbers jo pehle thay
    t_rec = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0
    t_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Received", f"{t_rec:,.0f}")
    col2.metric("Sent", f"{t_sent:,.0f}")
    st.metric("Net Balance", f"PKR {t_rec - t_sent:,.0f}")
    
    st.markdown("---")
    st.markdown("### 📖 View History")
    if not my_recs.empty:
        # Purana table format
        display_df = my_recs.sort_values(by=["Date", "Time"], ascending=False)
        st.dataframe(display_df[['Amount', 'Currency', 'Date', 'Time', 'Type', 'Reason', 'Balance']], 
                     use_container_width=True, hide_index=True)

# --- TAB 2: INSIGHTS (Naya Feature) ---
with tab_insights:
    st.subheader("📈 Amount Analysis")
    view = st.segmented_control("Filter:", ["Monthly", "Seasonal", "Annual"], default="Monthly")
    
    chart_data = all_recs.copy()
    chart_data['Month'] = chart_data['Date'].dt.strftime('%b')
    
    if view == "Monthly":
        fig = px.bar(chart_data, x='Month', y='Amount', color='Owner', barmode='group', title="Monthly Comparison")
        st.plotly_chart(fig, use_container_width=True)
    # ... (Seasonal aur Annual logic bhi yahan work karegi)

# --- TAB 3: MASTER LOGIC ---
with tab_master:
    st.table(all_recs.groupby('Owner')['Amount'].sum().reset_index())

if st.button("Logout"):
    st.session_state.clear(); st.rerun()
