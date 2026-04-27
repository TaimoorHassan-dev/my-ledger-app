import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px # Charts ke liye

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Zarkash Ledger", layout="centered", page_icon="💰")

# --- 2. UI STYLING (Aapka original design) ---
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

# --- 3. SESSION & LOGIN (Original) ---
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
    
    with tab_reg:
        nu = st.text_input("New Username", key="r_u")
        np = st.text_input("New Password", type="password", key="r_p")
        if st.button("Register"):
            if nu and np:
                users = conn.read(worksheet="Users", ttl=0)
                new_user = pd.concat([users, pd.DataFrame([{"Username": nu, "Password": np}])], ignore_index=True)
                conn.update(worksheet="Users", data=new_user)
                st.success("Account Created!")
    st.stop()

# --- 4. MAIN DASHBOARD ---
st.markdown(f"<h1 class='main-title'>🏦 {st.session_state['username'].upper()}'S LEDGER</h1>", unsafe_allow_html=True)

# Interface mein sirf aik "Insights" ka tab izafa kiya hai
tab_personal, tab_insights, tab_master = st.tabs(["📊 My Ledger", "📈 Insights", "🏛️ Master Logic"])

all_recs = conn.read(worksheet="Sheet1", ttl=0)
# Date column ko format karna zaroori hai charts ke liye
all_recs['Date'] = pd.to_datetime(all_recs['Date']) 
my_recs = all_recs[all_recs['Owner'] == st.session_state['username']]

# --- TAB 1: MY LEDGER (BILKUL SAME RAKHA HAI) ---
with tab_personal:
    t_rec = my_recs[my_recs['Amount'] > 0]['Amount'].sum() if not my_recs.empty else 0.0
    t_sent = abs(my_recs[my_recs['Amount'] < 0]['Amount'].sum()) if not my_recs.empty else 0.0
    net_bal = t_rec - t_sent

    st.markdown("### 📊 Status")
    c1, c2 = st.columns(2)
    c1.metric("Received", f"{t_rec:,.0f}")
    c2.metric("Sent", f"{t_sent:,.0f}")
    st.metric("Net Balance", f"{net_bal:,.0f}")

    if st.session_state['confirm_mode']:
        preview = st.session_state['temp_data']
        st.warning("⚠️ **VERIFY DETAILS**")
        st.markdown(f"""
        <div class="confirm-card">
            <b>Name:</b> {preview['Name']}<br>
            <b>Amount:</b> PKR {abs(preview['Amount']):,.0f}<br>
            <b>Action:</b> {preview['Type']}<br>
            <b>Date:</b> {preview['Date']} | <b>Time:</b> {preview['Time']}
        </div>
        """, unsafe_allow_html=True)
        
        cy, cn = st.columns(2)
        if cy.button("✅ Confirm & Save"):
            preview['Balance'] = net_bal + preview['Amount']
            conn.update(worksheet="Sheet1", data=pd.concat([all_recs, pd.DataFrame([preview])], ignore_index=True))
            st.session_state.update({'confirm_mode': False, 'temp_data': None})
            st.rerun()
        if cn.button("❌ Edit"):
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
                            "Owner": st.session_state['username'], "Name": n_in, 
                            "Amount": a_in if type_in == "Received (+)" else -a_in, 
                            "Currency": "PKR", "Type": type_in, "Date": d_in.strftime("%Y-%m-%d"), 
                            "Time": t_in.strftime("%H:%M:%S"), "Reason": r_in, "Balance": 0.0
                        }
                        st.session_state['confirm_mode'] = True
                        st.rerun()

    st.markdown("### 📖 View History")
    if not my_recs.empty:
        sorted_df = my_recs.sort_values(by=["Date", "Time"], ascending=[False, False])
        st.dataframe(sorted_df, use_container_width=True, hide_index=True)

# --- TAB 2: NAYA CHART SYSTEM (NEW INTERFACE) ---
with tab_insights:
    st.markdown("### 📈 User Wise Amount Analysis")
    view_type = st.radio("Select View:", ["Monthly", "Seasonal", "Annual"], horizontal=True)
    
    if not all_recs.empty:
        df_chart = all_recs.copy()
        df_chart['Month'] = df_chart['Date'].dt.strftime('%B')
        df_chart['Year'] = df_chart['Date'].dt.year
        
        # Season logic
        def get_season(m):
            if m in [12, 1, 2]: return "Winter"
            elif m in [3, 4, 5]: return "Spring"
            elif m in [6, 7, 8]: return "Summer"
            else: return "Autumn"
        df_chart['Season'] = df_chart['Date'].dt.month.apply(get_season)

        group_col = "Month" if view_type == "Monthly" else ("Year" if view_type == "Annual" else "Season")
        
        # Sirf positive additions (Received) ka chart
        summary_chart = df_chart[df_chart['Amount'] > 0].groupby(['Owner', group_col])['Amount'].sum().reset_index()
        
        fig = px.bar(summary_chart, x=group_col, y="Amount", color="Owner", 
                     title=f"Who Added More? ({view_type} View)", barmode="group",
                     labels={"Amount": "Total PKR Added"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet for charts.")

# --- TAB 3: MASTER LOGIC (BILKUL SAME) ---
with tab_master:
    st.markdown("### 🏛️ Back-hand Master Logic")
    if not all_recs.empty:
        summary = all_recs.groupby('Owner')['Amount'].sum().reset_index()
        summary.columns = ['Username', 'Total Balance']
        st.table(summary)

if st.button("Logout"):
    st.session_state.clear()
    st.rerun()
