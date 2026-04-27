import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px  # Naya library charts ke liye

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
    st.session_state.update({'logged_in': False, 'username': ""})

if 'confirm_mode' not in st.session_state:
    st.session_state.update({'confirm_mode': False, 'temp_data': None})

# (Login/Registration logic remains exactly as your original code)
if not st.session_state['logged_in']:
    st.markdown("<h1 class='main-title'>🏦 ZARKASH LEDGER</h1>", unsafe_allow_html=True)
    t_l, t_r = st.tabs(["🔐 Login", "📝 Register"])
    with t_l:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Enter Dashboard"):
            users = conn.read(worksheet="Users", ttl=0)
            if not users.empty and u in users['Username'].values:
                if str(p) == str(users[users['Username'] == u]['Password'].values[0]):
                    st.session_state.update({'logged_in': True, 'username': u})
                    st.rerun()
    with t_r:
        nu = st.text_input("New Username", key="r_u"); np = st.text_input("New Password", type="password", key="r_p")
        if st.button("Register"):
            users = conn.read(worksheet="Users", ttl=0)
            new_u = pd.concat([users, pd.DataFrame([{"Username": nu, "Password": np}])], ignore_index=True)
            conn.update(worksheet="Users", data=new_u); st.success("Created!")
    st.stop()

# --- 4. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)
tab_personal, tab_insights, tab_master = st.tabs(["📊 My Ledger", "📈 Insights", "🏛️ Master Logic"])

all_recs = conn.read(worksheet="Sheet1", ttl=0)
all_recs['Date'] = pd.to_datetime(all_recs['Date']) # Date conversion for charts

# --- TAB 1: PERSONAL LEDGER (Original Functionality) ---
with tab_personal:
    my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]
    t_rec = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
    t_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
    st.metric("Net Balance", f"PKR {t_rec - t_sent:,.0f}")
    
    # History with Date Sorting
    if not my_recs.empty:
        st.dataframe(my_recs.sort_values(by=["Date", "Time"], ascending=False), use_container_width=True, hide_index=True)

# --- TAB 2: NEW CHART FEATURE ---
with tab_insights:
    st.markdown("### 📊 User Contribution Analysis")
    
    # Feature 1: Chart Base Selection
    view_type = st.radio("View Basis:", ["Annual", "Monthly", "Seasonal"], horizontal=True)
    
    if not all_recs.empty:
        # Pre-processing data for charts
        chart_data = all_recs.copy()
        chart_data['Month'] = chart_data['Date'].dt.strftime('%B')
        chart_data['Year'] = chart_data['Date'].dt.year
        
        # Seasonal Logic
        def get_season(month):
            if month in [12, 1, 2]: return "Winter"
            elif month in [3, 4, 5]: return "Spring"
            elif month in [6, 7, 8]: return "Summer"
            else: return "Autumn"
        chart_data['Season'] = chart_data['Date'].dt.month.apply(get_season)

        if view_type == "Annual":
            group_col = "Year"
        elif view_type == "Monthly":
            group_col = "Month"
        else:
            group_col = "Season"

        # User wise summation
        user_sums = chart_data.groupby(['Owner', group_col])['Amount'].sum().reset_index()
        user_sums['Amount'] = user_sums['Amount'].apply(lambda x: max(0, x)) # Sirf positive additions dikhane ke liye

        fig = px.bar(user_sums, x=group_col, y="Amount", color="Owner", 
                     barmode="group", title=f"User Amount Comparison ({view_type})",
                     labels={"Amount": "Total Amount (PKR)", "Owner": "User Name"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available to show charts.")

# --- TAB 3: MASTER LOGIC ---
with tab_master:
    st.markdown("### 🏛️ Back-hand Master Logic")
    # Original Master Logic here
    summary = all_recs.groupby('Owner')['Amount'].sum().reset_index()
    st.table(summary)

if st.button("Logout"):
    st.session_state.clear(); st.rerun()
