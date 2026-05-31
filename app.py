import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import calendar
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Subsea Panel Manpower", layout="wide", page_icon="🎛️")

# --- LIGHT BLUE CORPORATE & DYNAMIC STATUS CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    /* Default cursor for clickable elements */
    div[data-testid="stSelectbox"] *, div[data-testid="stDateInput"] *, div[data-baseweb="select"], div[data-baseweb="select"] *, input[type="button"], input[type="submit"] { cursor: pointer !important; }
    /* Override for text inputs to show the standard typing cursor (I-beam) */
    div[data-testid="stTextInput"] input { cursor: text !important; }
    
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 5px; }
    .cal-header { text-align: center; font-weight: 700; color: white; padding: 8px; border-radius: 4px; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; background: linear-gradient(135deg, #3B82F6, #60A5FA); box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2); }
    .cal-day { position: relative; border: 1px solid #BFDBFE; border-top: 4px solid #93C5FD; border-radius: 6px; padding: 8px; min-height: 95px; background-color: #FFFFFF; transition: all 0.2s ease; cursor: default; }
    .cal-day-ok { border-top: 4px solid #10B981 !important; }
    .cal-day-modified { border-top: 4px solid #F59E0B !important; } 
    .cal-day-issue { border-top: 4px solid #8B5CF6 !important; } 
    .cal-day-today { background-color: #EFF6FF !important; border: 2px solid #2563EB !important; box-shadow: 0 0 10px rgba(37, 99, 235, 0.15); }
    .cal-day-date { font-weight: 800; color: #1E3A8A; border-bottom: 1px solid #F3F4F6; margin-bottom: 6px; padding-bottom: 2px; font-size: 16px;}
    .cal-day.empty { background-color: transparent !important; border: none !important; box-shadow: none !important; }
    .visible-content { display: flex; flex-direction: column; gap: 4px; }
    .warning-badge { background: #FAF5FF; color: #7C3AED; border: 1px dashed #8B5CF6; border-radius: 4px; font-size: 10px; padding: 3px 5px; font-weight: 800; line-height: 1.1;}
    .shift-details { opacity: 0; visibility: hidden; position: absolute; top: -10px; right: calc(100% + 12px); width: max-content; min-width: 180px; background: rgba(255, 255, 255, 0.98); z-index: 100; padding: 12px; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.2); border: 2px solid #60A5FA; display: flex; flex-direction: column; gap: 5px; transform: translateX(15px) scale(0.95); transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); pointer-events: none; backdrop-filter: blur(4px); }
    .cal-day:nth-child(7n+1) .shift-details, .cal-day:nth-child(7n+2) .shift-details { right: auto; left: calc(100% + 12px); transform: translateX(-15px) scale(0.95); }
    .cal-day:hover { z-index: 50; border-color: #3B82F6 !important; background-color: #EFF6FF !important; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);}
    .cal-day:hover .shift-details { opacity: 1; visibility: visible; transform: translateX(0) scale(1.05); }
    .shift-block { font-size: 11px; padding: 4px 6px; border-radius: 4px; border: 1px solid transparent; display: flex; align-items: baseline; gap: 4px;}
    .shift-header { font-weight: 800; min-width: 45px;}
    .shift-personnel { flex-grow: 1; white-space: normal; line-height: 1.3;}
    .shift-a { background-color: #EFF6FF; color: #1E3A8A; border-left: 3px solid #3B82F6;} 
    .shift-b { background-color: #FFFBEB; color: #92400E; border-left: 3px solid #F59E0B;} 
    .shift-c { background-color: #FAF5FF; color: #581C87; border-left: 3px solid #9333EA;} 
    .shift-wo { background-color: #F8FAFC; color: #64748B; border-left: 3px solid #94A3B8; font-style: italic;} 
    .stRadio > div[role="radiogroup"] { display: flex; flex-direction: column; gap: 12px; }
    .stRadio > div[role="radiogroup"] > label { background: #FFFFFF; border: 2px solid #1E3A8A; padding: 14px 16px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); cursor: pointer; }
    .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    .stRadio > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p { font-weight: 700; color: #1E3A8A; font-size: 15px; margin: 0; }
    .stRadio > div[role="radiogroup"] > label:hover { background: #EFF6FF; border-color: #2563EB; transform: translateX(6px); box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1); }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) { background: #DBEAFE !important; border: 2px solid #1E3A8A !important; box-shadow: 0 4px 10px rgba(30, 58, 138, 0.2); }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) div[data-testid="stMarkdownContainer"] p { color: #1E3A8A !important; }
    .mini-cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; padding: 10px 0; }
    .mini-cal-header { text-align: center; font-weight: 800; color: #64748B; font-size: 12px; padding-bottom: 5px; border-bottom: 2px solid #E2E8F0; text-transform: uppercase; }
    .mini-cal-day { border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px; min-height: 70px; background: #FFFFFF; display: flex; flex-direction: column; gap: 3px; }
    .mini-cal-day.empty { background: transparent; border: none; box-shadow: none; }
    .mini-cal-today { border: 2px solid #2563EB !important; background: #EFF6FF !important; }
    .mini-cal-date { font-size: 12px; font-weight: 800; color: #1E3A8A; align-self: flex-end; margin-bottom: 2px; }
    .mini-shift { font-size: 11px; font-weight: 800; color: white; border-radius: 4px; padding: 3px; text-align: center; width: 100%; letter-spacing: 0.5px;}
    .bg-a { background-color: #3B82F6; } .bg-b { background-color: #F59E0B; } .bg-c { background-color: #9333EA; } .bg-wo { background-color: #94A3B8; } .bg-leave { background-color: #EF4444; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SECURITY PORTAL (AUTHENTICATION)
# =========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-top: 8vh; font-size: 3rem;'>🌊 Subsea Panel Manpower Management 🎛️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 1.1rem; margin-bottom: 2rem;'>Secure Operational Dashboard</p>", unsafe_allow_html=True)
    
    col_spacer1, col_login, col_spacer2 = st.columns([1, 1.2, 1])
    with col_login:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center; color: #3B82F6; margin-bottom: 20px;'>🔐 Authentication Required</h3>", unsafe_allow_html=True)
            username = st.text_input("👤 Username", placeholder="Enter your credentials")
            password = st.text_input("🔑 Password", type="password", placeholder="••••••••")
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 Unlock Dashboard", type="primary", use_container_width=True)
            
            if submit:
                if username == "Subsea" and password == "Subsea@05":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Authentication Failed: Invalid username or password.")
    
    st.stop()


# =========================================================
# GOOGLE SHEETS MULTI-TAB PERSISTENCE ENGINE 
# =========================================================
WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTH_NAMES = list(calendar.month_name)[1:]
SPREADSHEET_ID = "1KD0tl3MjCumuovdLaN_hS2f_dDBZKNXyuDOUiuKV-jk"

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def save_data_to_db():
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID)

    # 1. Save Schedule to Sheet 1
    ws_sched = sheet.sheet1
    ws_sched.clear()
    df_sched = st.session_state.schedule.copy()
    df_sched['Date'] = df_sched['Date'].astype(str) 
    sched_data = [df_sched.columns.values.tolist()] + df_sched.values.tolist()
    ws_sched.update(range_name='A1', values=sched_data)

    # 2. Save Manpower to Sheet 2
    try:
        ws_man = sheet.worksheet("Manpower")
    except:
        ws_man = sheet.add_worksheet(title="Manpower", rows="50", cols="20")
    
    ws_man.clear()
    df_man = st.session_state.manpower.copy()
    man_data = [df_man.columns.values.tolist()] + df_man.values.tolist()
    ws_man.update(range_name='A1', values=man_data)

def init_default_manpower():
    st.session_state.manpower = pd.DataFrame({
        'Emp_ID': ['E01', 'E02', 'E03', 'E04', 'E05', 'E06', 'E07', 'E08', 'E09'],
        'Name': ['Srajan', 'Anna', 'Swami', 'David', 'Edward', 'Frank', 'Grace', 'Harry', 'Ian'],
        'Role': ['Senior', 'Senior', 'Junior', 'Senior', 'Senior', 'Junior', 'Junior', 'Junior', 'Junior'],
        'Week_Off': ['Sunday', 'Tuesday', 'Thursday', 'Saturday', 'Friday', 'Monday', 'Tuesday', 'Wednesday', 'Friday']
    })

def generate_schedule():
    today = datetime.date.today()
    start_date = datetime.date(today.year - 1, 1, 1) 
    dates = [start_date + datetime.timedelta(days=x) for x in range(1095)]
    schedule_data = []
    for d in dates:
        for _, row in st.session_state.manpower.iterrows():
            shift_assigned = get_shift_for_date(d, row['Week_Off'])
            schedule_data.append({'Date': d, 'Name': row['Name'], 'Role': row['Role'], 'Shift': shift_assigned})
    st.session_state.schedule = pd.DataFrame(schedule_data)

def sync_roster_updates(old_df, new_df):
    curr_sched = st.session_state.schedule.copy()
    today = datetime.date.today()
    old_wo_map = dict(zip(old_df['Name'], old_df['Week_Off']))
    
    valid_names = new_df['Name'].tolist()
    curr_sched = curr_sched[curr_sched['Name'].isin(valid_names)]
    
    role_map = dict(zip(new_df['Name'], new_df['Role']))
    curr_sched['Role'] = curr_sched['Name'].map(role_map)
    
    old_names = old_df['Name'].tolist()
    added_names = [n for n in valid_names if n not in old_names]
    
    if added_names:
        new_users_df = new_df[new_df['Name'].isin(added_names)]
        start_date = datetime.date(today.year - 1, 1, 1) 
        dates = [start_date + datetime.timedelta(days=x) for x in range(1095)]
        
        new_rows = []
        for d in dates:
            for _, row in new_users_df.iterrows():
                new_rows.append({
                    'Date': d, 
                    'Name': row['Name'], 
                    'Role': row['Role'], 
                    'Shift': get_shift_for_date(d, row['Week_Off'])
                })
        curr_sched = pd.concat([curr_sched, pd.DataFrame(new_rows)], ignore_index=True)
        
    changed_wo_names = []
    for _, row in new_df.iterrows():
        name = row['Name']
        if name in old_names and row['Week_Off'] != old_wo_map.get(name):
            changed_wo_names.append((name, old_wo_map[name], row['Week_Off']))
            
    if changed_wo_names:
        for index, row in curr_sched.iterrows():
            if row['Date'] >= today:
                for name, old_wo, new_wo in changed_wo_names:
                    if row['Name'] == name:
                        old_baseline_shift = get_shift_for_date(row['Date'], old_wo)
                        if row['Shift'] == old_baseline_shift:
                            new_baseline_shift = get_shift_for_date(row['Date'], new_wo)
                            curr_sched.at[index, 'Shift'] = new_baseline_shift
                            
    curr_sched['Date'] = pd.to_datetime(curr_sched['Date']).dt.date
    return curr_sched

def load_or_generate_data():
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID)

    try:
        ws_man = sheet.worksheet("Manpower")
        man_data = ws_man.get_all_records()
        if man_data:
            st.session_state.manpower = pd.DataFrame(man_data)
        else:
            init_default_manpower()
    except Exception:
        init_default_manpower()

    try:
        ws_sched = sheet.sheet1
        sched_data = ws_sched.get_all_records()
        if not sched_data:
            raise ValueError("Sheet is empty")
        df = pd.DataFrame(sched_data)
        df['Date'] = pd.to_datetime(df['Date']).dt.date 
        st.session_state.schedule = df
    except Exception:
        generate_schedule()
        save_data_to_db()

def get_shift_for_date(curr_date, week_off_day):
    wo_idx = WEEK_DAYS.index(week_off_day)
    curr_idx = curr_date.weekday()
    diff = (curr_idx - wo_idx) % 7
    if diff == 0: return 'WO'
    elif diff in [1, 2]: return 'B'
    elif diff in [3, 4]: return 'A'
    elif diff in [5, 6]: return 'C'

def check_shift_health(shift_df):
    if len(shift_df) == 0: return False, "Unmanned Shift"
    srs = len(shift_df[shift_df['Role'] == 'Senior'])
    jrs = len(shift_df[shift_df['Role'] == 'Junior'])
    if srs == 0: return False, "No Sr Engg"
    if srs == 1 and jrs == 0: return False, "1 Person Only"
    if jrs > 1 and srs == 0: return False, "Jrs Only (Fatal)"
    return True, ""

def determine_day_status(day_data, curr_date):
    has_issue = False
    is_modified = False
    for s in ['A', 'B', 'C']:
        shift_personnel = day_data[day_data['Shift'] == s]
        health_ok, _ = check_shift_health(shift_personnel)
        if not health_ok:
            has_issue = True
            break
    if has_issue: return "issue"
    if 'Leave' in day_data['Shift'].values: is_modified = True
    shift_counts = day_data[day_data['Shift'].isin(['A', 'B', 'C'])].groupby('Name').size()
    if (shift_counts > 1).any(): is_modified = True
    if not is_modified:
        for _, row in day_data.iterrows():
            if row['Shift'] not in ['Leave', 'WO']:
                manpower_row = st.session_state.manpower[st.session_state.manpower['Name'] == row['Name']]
                if not manpower_row.empty:
                    expected = get_shift_for_date(curr_date, manpower_row['Week_Off'].values[0])
                    if expected != row['Shift']: 
                        is_modified = True
                        break
    if is_modified: return "modified"
    return "ok"

def get_eligible_replacements(target_date, target_shift, df_sched, manpower, exclude_name=None):
    avail_enggs = []
    prev_date = target_date - datetime.timedelta(days=1)
    next_date = target_date + datetime.timedelta(days=1)

    for e in manpower['Name']:
        if e == exclude_name: continue

        e_shifts_curr = df_sched[(df_sched['Date'] == target_date) & (df_sched['Name'] == e)]['Shift'].tolist()
        e_shift_curr = e_shifts_curr[0] if e_shifts_curr else None

        if e_shift_curr == target_shift: continue
        e_role = manpower[manpower['Name'] == e]['Role'].values[0]

        if e_shift_curr == 'WO':
            avail_enggs.append(f"{e} ({e_role}) - Pull from WO")
        else:
            is_eligible = False
            reason = ""
            if target_shift == 'A':
                e_shifts_prev = df_sched[(df_sched['Date'] == prev_date) & (df_sched['Name'] == e)]['Shift'].tolist()
                if e_shift_curr == 'B': is_eligible, reason = True, "Double Shift (A + B today)"
                elif 'C' in e_shifts_prev: is_eligible, reason = True, "Double Shift (Prev C + A today)"
            elif target_shift == 'B':
                if e_shift_curr == 'A': is_eligible, reason = True, "Double Shift (A + B today)"
                elif e_shift_curr == 'C': is_eligible, reason = True, "Double Shift (B + C today)"
            elif target_shift == 'C':
                e_shifts_next = df_sched[(df_sched['Date'] == next_date) & (df_sched['Name'] == e)]['Shift'].tolist()
                if e_shift_curr == 'B': is_eligible, reason = True, "Double Shift (B + C today)"
                elif 'A' in e_shifts_next: is_eligible, reason = True, "Double Shift (C today + Next A)"

            if is_eligible:
                avail_enggs.append(f"{e} ({e_role}) - {reason}")
    return avail_enggs

# --- INITIALIZE STATE ON BOOT ---
if 'manpower' not in st.session_state or 'schedule' not in st.session_state:
    load_or_generate_data()

# --- GLOBAL TIME LOGIC & STATE ---
utc_now = datetime.datetime.utcnow()
ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
now_hour = ist_now.hour

if 6 <= now_hour < 14: active_s = 'A'
elif 14 <= now_hour < 22: active_s = 'B'
else: active_s = 'C'
today_date = datetime.date.today()
today_data = st.session_state.schedule[st.session_state.schedule['Date'] == today_date]
active_personnel = today_data[today_data['Shift'] == active_s]

if 'view_year' not in st.session_state: st.session_state.view_year = ist_now.year
if 'view_month' not in st.session_state: st.session_state.view_month = ist_now.month

def change_month(delta):
    new_m = st.session_state.view_month + delta
    if new_m > 12:
        st.session_state.view_month = 1
        st.session_state.view_year += 1
    elif new_m < 1:
        st.session_state.view_month = 12
        st.session_state.view_year -= 1
    else:
        st.session_state.view_month = new_m

# =========================================================
# SIDEBAR RE-ARCHITECTURE 
# =========================================================
with st.sidebar:
    st.markdown("### 📡 Live Dashboard")

    if not active_personnel.empty:
        personnel_str = ", ".join([f"{r['Name']}({'Sr' if r['Role'] == 'Senior' else 'Jr'})" for _, r in active_personnel.iterrows()])
        st.success(f"**🟢 Active: Shift {active_s} ({personnel_str})**")
    else:
        st.error(f"**🟣 Active: Shift {active_s} (UNMANNED)**")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🌊 Navigation")
    
    page = st.radio("Select Module", ["📅 Monthly Calendar", "🔄 Shift Exchange", "🏖️ Leave Planner", "🗓️ Shift Planner", "👥 Manpower Roster"], label_visibility="collapsed")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# =========================================================
# MAIN CONTENT ROUTING
# =========================================================

if page == "📅 Monthly Calendar":
    st.markdown("<h1 style='text-align: center; color: #1E3A8A; margin-bottom: 1.5rem;'>Subsea Shift Calendar</h1>", unsafe_allow_html=True)
    
    col_time, col_controls = st.columns(2)
    with col_time:
        main_clock_html = """
        <div style="background: linear-gradient(135deg, #EFF6FF, #DBEAFE); padding: 15px; border-radius: 8px; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; height: 100%;">
            <div style="text-align: center;">
                <div style="font-size: 12px; color: #3B82F6; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Current IST Time</div>
                <div id="main-time" style="font-size: 24px; font-family: monospace; color: #1E3A8A; font-weight: 900; margin-top: 4px;">--</div>
            </div>
        </div>
        <script>
            function getOrdinal(n) {
                let s = ["th", "st", "nd", "rd"];
                let v = n % 100;
                return n + (s[(v - 20) % 10] || s[v] || s[0]);
            }
            function updateMainClock() {
                const now = new Date();
                const day = getOrdinal(now.getDate());
                const month = now.toLocaleString('en-IN', { month: 'short' });
                const year = now.getFullYear();
                const timeStr = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                document.getElementById('main-time').innerText = day + ' ' + month + ', ' + year + ' • ' + timeStr;
            }
            setInterval(updateMainClock, 1000); updateMainClock();
        </script>
        """
        components.html(main_clock_html, height=95)
        
    with col_controls:
        st.write("") 
        st.write("")
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            st.button("◀ Previous", on_click=change_month, args=(-1,), use_container_width=True)
        with nav_col2:
            month_name = calendar.month_name[st.session_state.view_month]
            st.markdown(f"<h3 style='text-align: center; color: #1E3A8A; margin-top: -7px; margin-bottom: 0;'>{month_name} {st.session_state.view_year}</h3>", unsafe_allow_html=True)
        with nav_col3:
            st.button("Next ▶", on_click=change_month, args=(1,), use_container_width=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    cal = calendar.monthcalendar(st.session_state.view_year, st.session_state.view_month)
    html_calendar = "<div class='cal-grid'>"
    for day in WEEK_DAYS: html_calendar += f"<div class='cal-header'>{day[:3]}</div>"
        
    df_sched = st.session_state.schedule
    for week in cal:
        for day in week:
            if day == 0: html_calendar += "<div class='cal-day empty'></div>"
            else:
                curr_date = datetime.date(st.session_state.view_year, st.session_state.view_month, day)
                day_data = df_sched[df_sched['Date'] == curr_date]
                status = determine_day_status(day_data, curr_date)
                status_class = f" cal-day-{status}"
                is_today = " cal-day-today" if curr_date == today_date else ""
                
                html_calendar += f"<div class='cal-day{status_class}{is_today}'><div class='cal-day-date'>{day}</div>"
                
                visible_html = "<div class='visible-content'>"
                curr_shift_data = day_data[day_data['Shift'] == active_s]
                visible_html += f"<div class='shift-block shift-{active_s.lower()}'><span class='shift-header'>Shift {active_s}:</span>"
                if not curr_shift_data.empty:
                    names = [f"{r['Name']}({'Sr' if r['Role'] == 'Senior' else 'Jr'})" for _, r in curr_shift_data.iterrows()]
                    visible_html += f"<span class='shift-personnel'>{', '.join(names)}</span>"
                else: visible_html += "<span class='shift-personnel' style='color:#EF4444; font-weight:bold;'>Unmanned</span>"
                visible_html += "</div>"
                
                details_html = "<div class='shift-details'>"
                for s in ['A', 'B', 'C']:
                    shift_personnel = day_data[day_data['Shift'] == s]
                    health_ok, warning_msg = check_shift_health(shift_personnel)
                    if not health_ok: visible_html += f"<div class='warning-badge'>⚠️ Shift {s}: {warning_msg}</div>"
                    
                    details_html += f"<div class='shift-block shift-{s.lower()}'><span class='shift-header'>Shift {s}:</span>"
                    names = [f"{r['Name']}({'Sr' if r['Role'] == 'Senior' else 'Jr'})" for _, r in shift_personnel.iterrows()]
                    details_html += f"<span class='shift-personnel'>{', '.join(names) if names else 'Unmanned'}</span></div>"
                    
                wo_personnel = day_data[day_data['Shift'] == 'WO']
                if not wo_personnel.empty:
                    names = ", ".join(wo_personnel['Name'].tolist())
                    details_html += f"<div class='shift-block shift-wo'><span class='shift-header'>WO:</span><span class='shift-personnel'>{names}</span></div>"
                
                details_html += "</div>" 
                visible_html += "</div>" 
                html_calendar += visible_html + details_html + "</div>"
    html_calendar += "</div>"
    st.markdown(html_calendar, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SHIFT EXCHANGE ENGINE
# ---------------------------------------------------------
elif page == "🔄 Shift Exchange":
    st.title("Operational Shift Exchange")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Originating Personnel")
        requester = st.selectbox("Select Engineer", st.session_state.manpower['Name'])
        req_date = st.date_input("Date of Operation")
        
        df_sched = st.session_state.schedule
        my_shift_data = df_sched[(df_sched['Date'] == req_date) & (df_sched['Name'] == requester)]
        
        if my_shift_data.empty: st.error("No schedule found for this date.")
        else:
            my_shifts = my_shift_data['Shift'].tolist()
            my_role = my_shift_data.iloc[0]['Role']
            st.info(f"Currently scheduled for: **{', '.join(my_shifts)}** | Role: **{my_role}**")
            
            with col2:
                if 'WO' not in my_shifts and 'Leave' not in my_shifts:
                    st.subheader("Action Strategy")
                    action_type = st.radio("Exchange Type:", ["Mutual Shift Swap", "Mark Leave & Handover Shift"])
                    
                    if action_type == "Mutual Shift Swap":
                        target_shift = st.selectbox("Swap into Shift", [s for s in ['A', 'B', 'C'] if s not in my_shifts])
                        target_data = df_sched[(df_sched['Date'] == req_date) & (df_sched['Shift'] == target_shift) & (df_sched['Role'] == my_role)]
                        
                        if not target_data.empty:
                            swap_target = st.selectbox("Select Compatible Personnel", target_data['Name'].tolist())
                            if st.button("Execute Mutual Swap", type="primary"):
                                st.session_state.schedule.loc[my_shift_data.index[0], 'Shift'] = target_shift
                                st.session_state.schedule.loc[target_data[target_data['Name'] == swap_target].index[0], 'Shift'] = my_shifts[0]
                                save_data_to_db()
                                st.success("Shift successfully swapped. Calendar will highlight this day in yellow.")
                        else: st.error(f"No {my_role} currently assigned to Shift {target_shift}.")
                            
                    elif action_type == "Mark Leave & Handover Shift":
                        avail_enggs = get_eligible_replacements(req_date, my_shifts[0], df_sched, st.session_state.manpower, requester)
                        rep = st.selectbox("Select Available Personnel to Backfill", avail_enggs) if avail_enggs else None
                        
                        if not rep: st.error("No eligible engineers available for safe continuous double shift or WO pull.")
                        elif st.button("Authorize Leave & Handover", type="primary"):
                            st.session_state.schedule.loc[my_shift_data.index[0], 'Shift'] = 'Leave'
                            rep_name = rep.split(" (")[0]
                            rep_role = st.session_state.manpower[st.session_state.manpower['Name'] == rep_name]['Role'].values[0]
                            new_row = {'Date': req_date, 'Name': rep_name, 'Role': rep_role, 'Shift': my_shifts[0]}
                            st.session_state.schedule = pd.concat([st.session_state.schedule, pd.DataFrame([new_row])], ignore_index=True)
                            save_data_to_db()
                            st.success(f"{requester} marked Leave. Shift handed over to {rep_name}.")
                else:
                    st.warning("Engineer is off-duty (WO/Leave). No operational shift to exchange.")

# ---------------------------------------------------------
# 3. LEAVE PLANNER
# ---------------------------------------------------------
elif page == "🏖️ Leave Planner":
    st.title("Leave Management Engine")
    st.markdown("---")
    
    df_sched = st.session_state.schedule
    
    col_book, col_cancel = st.columns(2)
    
    with col_book:
        st.markdown("<h3 style='color: #1E3A8A;'>🏖️ Book New Leave</h3>", unsafe_allow_html=True)
        leave_engg = st.selectbox("Select Engineer", st.session_state.manpower['Name'], key="book_engg")
        date_selection = st.date_input("Select Leave Range", value=(today_date, today_date + datetime.timedelta(days=1)))
        
        if len(date_selection) == 2:
            start_date, end_date = date_selection
            leave_dates = [start_date + datetime.timedelta(days=x) for x in range((end_date - start_date).days + 1)]
        elif len(date_selection) == 1: leave_dates = [date_selection[0]]
        else: leave_dates = []

        if st.button("Generate Leave Impact Report", key="btn_impact"):
            st.session_state.temp_leave_dates = leave_dates
            
        if hasattr(st.session_state, 'temp_leave_dates'):
            leave_records = df_sched[(df_sched['Date'].isin(st.session_state.temp_leave_dates)) & (df_sched['Name'] == leave_engg)]
            
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #3B82F6;'>Shift Coverage Configuration</h4>", unsafe_allow_html=True)
            coverage_plan = {}
            has_operational_shifts = False
            
            for idx, row in leave_records.iterrows():
                if row['Shift'] in ['WO', 'Leave']: continue
                has_operational_shifts = True
                
                st.markdown(f"**🗓️ {row['Date'].strftime('%d %b, %Y')} — Shift {row['Shift']}**")
                avail_enggs = get_eligible_replacements(row['Date'], row['Shift'], df_sched, st.session_state.manpower, leave_engg)
                coverage_plan[idx] = st.selectbox(f"Resolution", ["Leave Unmanned (Short-Staffed)"] + avail_enggs, key=f"cov_{idx}")
                st.write("") 
                
            if not has_operational_shifts:
                st.info("No operational shifts are affected during this date range (Engineer is already on WO/Leave).")
                if st.button("Acknowledge Leave", key="btn_ack"):
                    for idx in leave_records.index: st.session_state.schedule.loc[idx, 'Shift'] = 'Leave'
                    if 'temp_leave_dates' in st.session_state: del st.session_state['temp_leave_dates']
                    save_data_to_db()
                    st.success("Registered. Calendar dates will highlight yellow.")
                    st.rerun()
            else:
                if st.button("Execute Master Leave Plan", type="primary", key="btn_exec"):
                    for idx, row in leave_records.iterrows():
                        if row['Shift'] in ['WO', 'Leave']:
                            st.session_state.schedule.loc[idx, 'Shift'] = 'Leave'
                            continue
                            
                        orig_shift = row['Shift']
                        st.session_state.schedule.loc[idx, 'Shift'] = 'Leave'
                        
                        selection = coverage_plan[idx]
                        if selection != "Leave Unmanned (Short-Staffed)":
                            rep_name = selection.split(" (")[0]
                            rep_role = st.session_state.manpower[st.session_state.manpower['Name'] == rep_name]['Role'].values[0]
                            new_row = {'Date': row['Date'], 'Name': rep_name, 'Role': rep_role, 'Shift': orig_shift}
                            st.session_state.schedule = pd.concat([st.session_state.schedule, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.schedule.reset_index(drop=True, inplace=True)
                    save_data_to_db()
                    if 'temp_leave_dates' in st.session_state: del st.session_state['temp_leave_dates']
                    st.success("Leave Block Approved and Matrix Updated!")
                    st.rerun()

    with col_cancel:
        st.markdown("<h3 style='color: #1E3A8A;'>❌ Cancel Planned Leave</h3>", unsafe_allow_html=True)
        cancel_engg = st.selectbox("Select Engineer to Cancel Leave", st.session_state.manpower['Name'], key="cancel_engg")
        future_leaves = df_sched[(df_sched['Name'] == cancel_engg) & (df_sched['Shift'] == 'Leave') & (df_sched['Date'] >= today_date)]
        
        if future_leaves.empty:
            st.info(f"{cancel_engg} does not have any upcoming leave scheduled.")
        else:
            st.warning("Canceling a leave restores the original mathematical shift and removes any replacement personnel assigned to cover it.")
            leave_options = {row['Date'].strftime('%d %b, %Y'): row['Date'] for _, row in future_leaves.iterrows()}
            selected_date_str = st.selectbox("Select Leave Date to Cancel", list(leave_options.keys()), key="cancel_date")
            target_cancel_date = leave_options[selected_date_str]
            
            if st.button("Cancel Leave & Restore Matrix", type="primary", key="btn_cancel"):
                idx_to_restore = future_leaves[future_leaves['Date'] == target_cancel_date].index[0]
                wo_day = st.session_state.manpower[st.session_state.manpower['Name'] == cancel_engg]['Week_Off'].values[0]
                restored_shift = get_shift_for_date(target_cancel_date, wo_day)
                st.session_state.schedule.loc[idx_to_restore, 'Shift'] = restored_shift
                
                if restored_shift not in ['WO', 'Leave']:
                    others_on_shift = df_sched[(df_sched['Date'] == target_cancel_date) & (df_sched['Shift'] == restored_shift) & (df_sched['Name'] != cancel_engg)]
                    for other_idx, other_row in others_on_shift.iterrows():
                        other_wo = st.session_state.manpower[st.session_state.manpower['Name'] == other_row['Name']]['Week_Off'].values[0]
                        other_default = get_shift_for_date(target_cancel_date, other_wo)
                        if other_default != restored_shift:
                            st.session_state.schedule = st.session_state.schedule.drop(other_idx)
                            st.toast(f"System automatically removed {other_row['Name']} from covering Shift {restored_shift}.")
                
                st.session_state.schedule.reset_index(drop=True, inplace=True)
                save_data_to_db()
                st.success(f"Leave canceled. {cancel_engg} successfully restored to Shift {restored_shift}.")
                st.rerun()

    # --- LEAVE & SHORTFALL OVERVIEW DASHBOARD ---
    st.markdown("---")
    st.markdown("<h2 style='color: #1E3A8A;'>📊 System Overview</h2>", unsafe_allow_html=True)
    col_l1, col_l2 = st.columns(2)
    
    with col_l1:
        st.markdown("#### Upcoming Approved Leaves")
        future_lvs = df_sched[(df_sched['Shift'] == 'Leave') & (df_sched['Date'] >= today_date)].copy()
        if not future_lvs.empty:
            future_lvs['Date'] = future_lvs['Date'].apply(lambda x: x.strftime('%d %b, %Y'))
            st.dataframe(future_lvs[['Date', 'Name', 'Role']].sort_values('Date'), hide_index=True, use_container_width=True)
        else: st.info("No upcoming leaves scheduled.")

    with col_l2:
        st.markdown("#### ⚠️ Unmanned / Failing Shifts")
        shortfalls = []
        check_dates = [today_date + datetime.timedelta(days=x) for x in range(30)]
        for d in check_dates:
            day_data = df_sched[df_sched['Date'] == d]
            for s in ['A', 'B', 'C']:
                shift_personnel = day_data[day_data['Shift'] == s]
                health_ok, msg = check_shift_health(shift_personnel)
                if not health_ok: shortfalls.append({'Date': d, 'Shift': s, 'Issue': msg, 'Current Staff': len(shift_personnel)})
        
        if shortfalls:
            sf_df = pd.DataFrame(shortfalls)
            sf_df_display = sf_df.copy()
            sf_df_display['Date'] = sf_df_display['Date'].apply(lambda x: x.strftime('%d %b, %Y'))
            st.dataframe(sf_df_display, hide_index=True, use_container_width=True)
            
            sf_options = [f"{row['Date'].strftime('%d %b, %Y')} - Shift {row['Shift']} ({row['Issue']})" for _, row in sf_df.iterrows()]
            selected_sf = st.selectbox("Select Shift to Reinforce", sf_options, key="sf_select")
            sf_idx = sf_options.index(selected_sf)
            target_date = shortfalls[sf_idx]['Date']
            target_shift = shortfalls[sf_idx]['Shift']
            
            avail_enggs = get_eligible_replacements(target_date, target_shift, df_sched, st.session_state.manpower)
            reinforcement = st.selectbox("Deploy Engineer", avail_enggs, key="sf_deploy") if avail_enggs else None
            
            if not reinforcement: st.error("No eligible engineers available for safe continuous double shift or WO pull.")
            elif st.button("Assign Extra Shift", type="primary", key="btn_assign_ot"):
                rep_name = reinforcement.split(" (")[0]
                rep_role = st.session_state.manpower[st.session_state.manpower['Name'] == rep_name]['Role'].values[0]
                new_row = {'Date': target_date, 'Name': rep_name, 'Role': rep_role, 'Shift': target_shift}
                st.session_state.schedule = pd.concat([st.session_state.schedule, pd.DataFrame([new_row])], ignore_index=True)
                st.session_state.schedule.reset_index(drop=True, inplace=True)
                save_data_to_db()
                st.success(f"{rep_name} deployed to cover shortfall!")
                st.rerun()
        else: st.success("All operational shifts for the next 30 days are fully manned and healthy.")

# ---------------------------------------------------------
# 4. MONTHLY SHIFT PLANNER (MANUAL OVERRIDE)
# ---------------------------------------------------------
elif page == "🗓️ Shift Planner":
    st.markdown("<h1 style='color: #1E3A8A; margin-bottom: 0;'>🗓️ Monthly Master Shift Planner</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Dates flow vertically. Assign primary and double shifts manually for the entire month.</p>", unsafe_allow_html=True)

    col_y, col_m, _ = st.columns([1, 1, 2])
    plan_year = col_y.selectbox("Select Year", range(ist_now.year - 1, ist_now.year + 2), index=1, key="plan_y")
    plan_month_name = col_m.selectbox("Select Month", MONTH_NAMES, index=ist_now.month - 1, key="plan_m")
    plan_month = MONTH_NAMES.index(plan_month_name) + 1

    df_sched = st.session_state.schedule.copy()
    
    # Filter isolating the selected month
    mask = (df_sched['Date'].apply(lambda x: x.year) == plan_year) & (df_sched['Date'].apply(lambda x: x.month) == plan_month)
    month_data = df_sched[mask].copy()

    if month_data.empty:
        st.warning("No data generated for this month yet.")
    else:
        # Custom aggregation to combine multiple shifts into readable tags (A+B, B+C, etc)
        def agg_shifts(s):
            shifts = set(s)
            if 'A' in shifts and 'B' in shifts: return 'A+B'
            if 'B' in shifts and 'C' in shifts: return 'B+C'
            if 'C' in shifts and 'A' in shifts: return 'C+A'
            if 'Leave' in shifts: return 'Leave'
            if 'WO' in shifts: return 'WO'
            return s.iloc[0] if not s.empty else 'Unmanned'

        month_data = month_data.sort_values('Date')
        
        # Pivot operation: Dates become rows, Names become columns
        pivot_df = month_data.pivot_table(index='Date', columns='Name', values='Shift', aggfunc=agg_shifts).reset_index()
        
        # Pre-compute Health Status for each Day
        status_list = []
        for d_obj in pivot_df['Date']:
            day_data = month_data[month_data['Date'] == d_obj]
            day_status = "✅ OK"
            for s in ['A', 'B', 'C']:
                shift_personnel = day_data[day_data['Shift'] == s]
                ok, msg = check_shift_health(shift_personnel)
                if not ok:
                    day_status = "⚠️ ISSUE"
                    break
            status_list.append(day_status)
        
        pivot_df.insert(1, 'Status', status_list)
        
        # Build strict column configurations
        col_cfg = {
            "Date": st.column_config.DateColumn("Date", disabled=True, format="DD MMM (ddd)"),
            "Status": st.column_config.TextColumn("Day Status", disabled=True)
        }
        
        # Dynamically append each engineer as a selectable column
        for name in pivot_df.columns[2:]: 
            role_val = st.session_state.manpower.loc[st.session_state.manpower['Name'] == name, 'Role'].values[0]
            role_abbr = "Sr" if role_val == "Senior" else "Jr"
            col_cfg[name] = st.column_config.SelectboxColumn(
                f"{name} ({role_abbr})", 
                options=['A', 'B', 'C', 'WO', 'Leave', 'A+B', 'B+C', 'C+A'],
                required=True,
                width="small"
            )
        
        st.markdown("### Interactive Planning Grid")
        st.caption("The 'Day Status' column calculates health based on the currently saved database. Changing drop-downs will not update the status until you click 'Commit Master Plan'.")
        
        edited_pivot = st.data_editor(pivot_df, column_config=col_cfg, use_container_width=True, hide_index=True)
        
        if st.button("Commit Master Plan", type="primary"):
            # Pandas melt operation to return the vertical matrix back to transactional format
            melted = edited_pivot.melt(id_vars=['Date', 'Status'], var_name='Name', value_name='Shift')
            melted = melted.drop(columns=['Status'])
            
            # Expansion Engine: Safely split double shifts back into multiple mathematical rows
            expanded_rows = []
            for _, row in melted.iterrows():
                shifts = []
                if row['Shift'] == 'A+B': shifts = ['A', 'B']
                elif row['Shift'] == 'B+C': shifts = ['B', 'C']
                elif row['Shift'] == 'C+A': shifts = ['C', 'A']
                else: shifts = [row['Shift']]
                
                for s in shifts:
                    expanded_rows.append({'Date': row['Date'], 'Name': row['Name'], 'Shift': s})
                    
            melted = pd.DataFrame(expanded_rows)
            
            # Re-map the roles since they were absorbed during the pivot
            role_map = dict(zip(st.session_state.manpower['Name'], st.session_state.manpower['Role']))
            melted['Role'] = melted['Name'].map(role_map)
            
            # Reorder columns to ensure database integrity: Date, Name, Role, Shift
            melted = melted[['Date', 'Name', 'Role', 'Shift']]
            
            # Remove old data for this specific month from the main schedule memory
            st.session_state.schedule = df_sched[~mask]
            
            # Append newly melted data and enforce sorting integrity
            st.session_state.schedule = pd.concat([st.session_state.schedule, melted], ignore_index=True)
            st.session_state.schedule = st.session_state.schedule.sort_values(by=['Date', 'Name']).reset_index(drop=True)
            
            save_data_to_db()
            st.success(f"Master plan for {plan_month_name} {plan_year} successfully committed to the database! The Calendar and Day Statuses have been updated.")
            st.rerun()

# ---------------------------------------------------------
# 5. MANPOWER ROSTER (MINI CALENDAR & EXPORT)
# ---------------------------------------------------------
elif page == "👥 Manpower Roster":
    st.markdown("<h1 style='color: #1E3A8A; margin-bottom: 0;'>Panel Manpower Configuration</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Manage personnel details and view individual schedule trajectories.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    srs = len(st.session_state.manpower[st.session_state.manpower['Role'] == 'Senior'])
    jrs = len(st.session_state.manpower[st.session_state.manpower['Role'] == 'Junior'])
    
    col1.markdown(f"<div style='background: white; border: 1px solid #BFDBFE; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'><h4 style='color: #1E3A8A; margin: 0;'>Total Headcount</h4><h2 style='color: #3B82F6; margin: 0;'>{srs + jrs}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div style='background: white; border: 1px solid #BFDBFE; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'><h4 style='color: #1E3A8A; margin: 0;'>Senior Engineers</h4><h2 style='color: #10B981; margin: 0;'>{srs}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div style='background: white; border: 1px solid #BFDBFE; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);'><h4 style='color: #1E3A8A; margin: 0;'>Junior Engineers</h4><h2 style='color: #8B5CF6; margin: 0;'>{jrs}</h2></div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    edited_df = st.data_editor(
        st.session_state.manpower, num_rows="dynamic", use_container_width=True,
        column_config={
            "Role": st.column_config.SelectboxColumn("Designation", options=["Senior", "Junior"], required=True),
            "Week_Off": st.column_config.SelectboxColumn("Fixed Week Off", options=WEEK_DAYS, required=True)
        }
    )
    
    if st.button("Commit Roster Updates", type="primary"):
        old_manpower = st.session_state.manpower.copy()
        st.session_state.manpower = edited_df
        
        st.session_state.schedule = sync_roster_updates(old_manpower, edited_df)
        
        save_data_to_db()
        st.success("Roster saved! Global matrices updated securely without losing leaves.")

    # --- ADVANCED EXCEL EXPORT COMPONENT ---
    st.markdown("---")
    st.markdown("<h2 style='color: #1E3A8A;'>📥 Export Monthly Schedule (Excel)</h2>", unsafe_allow_html=True)
    st.markdown("Generate a formatted, color-coded Excel `.xlsx` file of the shift matrix.")
    
    col_ex1, col_ex2, col_ex3 = st.columns([1, 1, 2])
    ex_year = col_ex1.selectbox("Export Year", range(ist_now.year - 1, ist_now.year + 2), index=1, key="ex_y")
    ex_month_name = col_ex2.selectbox("Export Month", MONTH_NAMES, index=ist_now.month - 1, key="ex_m")
    ex_month = MONTH_NAMES.index(ex_month_name) + 1
    
    export_df = st.session_state.schedule.copy()
    export_df['Year'] = export_df['Date'].apply(lambda x: x.year)
    export_df['Month'] = export_df['Date'].apply(lambda x: x.month)
    
    month_data = export_df[(export_df['Year'] == ex_year) & (export_df['Month'] == ex_month)].copy()
    
    if not month_data.empty:
        month_data['Date_Col'] = month_data['Date'].apply(lambda x: x.strftime('%d\n%a'))
        
        pivot_df = month_data.pivot_table(index=['Name', 'Role'], columns='Date_Col', values='Shift', aggfunc='first').fillna('Unmanned')
        ordered_cols = sorted(pivot_df.columns.tolist(), key=lambda x: int(x.split('\n')[0]))
        pivot_df = pivot_df[ordered_cols]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook  = writer.book
            worksheet = workbook.add_worksheet('Shift Matrix')
            
            title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': '#1E3A8A', 'bg_color': '#EFF6FF', 'align': 'left', 'valign': 'vcenter', 'border': 1})
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#3B82F6', 'font_color': '#FFFFFF', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
            name_fmt = workbook.add_format({'bold': True, 'bg_color': '#F8FAFC', 'border': 1, 'align': 'left', 'valign': 'vcenter'})
            
            shift_colors = {
                'A': workbook.add_format({'bg_color': '#DBEAFE', 'font_color': '#1D4ED8', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True}),
                'B': workbook.add_format({'bg_color': '#FEF3C7', 'font_color': '#B45309', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True}),
                'C': workbook.add_format({'bg_color': '#F3E8FF', 'font_color': '#7E22CE', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True}),
                'WO': workbook.add_format({'bg_color': '#F1F5F9', 'font_color': '#64748B', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'italic': True}),
                'Leave': workbook.add_format({'bg_color': '#FEE2E2', 'font_color': '#B91C1C', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bold': True}),
                'Unmanned': workbook.add_format({'bg_color': '#FFFFFF', 'font_color': '#CBD5E1', 'align': 'center', 'valign': 'vcenter', 'border': 1})
            }
            
            num_cols = len(pivot_df.columns) + 2
            worksheet.merge_range(0, 0, 1, num_cols - 1, f"Subsea Panel Shift Matrix: {ex_month_name} {ex_year}", title_fmt)
            
            worksheet.write(2, 0, "Engineer Name", header_fmt)
            worksheet.write(2, 1, "Role", header_fmt)
            worksheet.set_column(0, 0, 18) 
            worksheet.set_column(1, 1, 10) 
            
            for col_num, date_str in enumerate(pivot_df.columns):
                worksheet.write(2, col_num + 2, date_str, header_fmt)
                worksheet.set_column(col_num + 2, col_num + 2, 7)
                
            for row_num, (index_tuple, row_data) in enumerate(pivot_df.iterrows()):
                name, role = index_tuple
                worksheet.write(row_num + 3, 0, name, name_fmt)
                worksheet.write(row_num + 3, 1, role, name_fmt)
                
                for col_num, val in enumerate(row_data):
                    fmt = shift_colors.get(val, shift_colors['Unmanned'])
                    worksheet.write(row_num + 3, col_num + 2, val, fmt)
                    
        excel_data = output.getvalue()
        
        col_ex3.markdown("<br>", unsafe_allow_html=True)
        col_ex3.download_button(
            label=f"💾 Download {ex_month_name} {ex_year} Excel File",
            data=excel_data,
            file_name=f"Subsea_Schedule_{ex_year}_{ex_month:02d}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type='primary',
            use_container_width=True
        )
    else:
        st.warning("No schedule data generated for this specific month yet.")

    # --- INDIVIDUAL SCHEDULE MINI CALENDAR ---
    st.markdown("---")
    st.markdown("<h2 style='color: #1E3A8A;'>📅 Individual Profile & Schedule</h2>", unsafe_allow_html=True)
    
    view_engg = st.selectbox("Select Personnel to Inspect", st.session_state.manpower['Name'])
    
    col_m1, col_m2, _ = st.columns([1, 1, 3])
    mini_year = col_m1.selectbox("Profile Year", range(ist_now.year - 1, ist_now.year + 2), index=1, key="mini_cal_y")
    
    mini_month_name = col_m2.selectbox("Profile Month", MONTH_NAMES, index=ist_now.month - 1, key="mini_cal_m")
    mini_month = MONTH_NAMES.index(mini_month_name) + 1
    
    mini_cal = calendar.monthcalendar(mini_year, mini_month)
    personal_sched = st.session_state.schedule[st.session_state.schedule['Name'] == view_engg]
    
    mini_html = "<div class='mini-cal-grid'>"
    for day in WEEK_DAYS:
        mini_html += f"<div class='mini-cal-header'>{day[:3]}</div>"
        
    for week in mini_cal:
        for day in week:
            if day == 0:
                mini_html += "<div class='mini-cal-day empty'></div>"
            else:
                curr_d = datetime.date(mini_year, mini_month, day)
                day_shifts = personal_sched[personal_sched['Date'] == curr_d]['Shift'].tolist()
                
                is_today_class = " mini-cal-today" if curr_d == today_date else ""
                
                mini_html += f"<div class='mini-cal-day{is_today_class}'>"
                mini_html += f"<div class='mini-cal-date'>{day}</div>"
                
                if not day_shifts:
                    mini_html += "<div class='mini-shift' style='background: #E2E8F0; color: #475569;'>N/A</div>"
                else:
                    for s in day_shifts:
                        bg_class = f"bg-{s.lower()}"
                        mini_html += f"<div class='mini-shift {bg_class}'>{s}</div>"
                mini_html += "</div>"
                
    mini_html += "</div>"
    st.markdown(mini_html, unsafe_allow_html=True)
