import streamlit as st
import os
import requests
import json
from datetime import datetime
from PIL import Image

# Setup Page Configuration
st.set_page_config(
    page_title="AI NoticeBoard | Smart Campus Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Server Configuration
BACKEND_URL = "https://ai-noticeboard-pn3r.onrender.com"

def is_backend_online():
    try:
        response = requests.get(f"{BACKEND_URL}/api/notices", timeout=1.0)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Direct imports for standalone flat fallback mode
try:
    from db import get_notices, add_notice, delete_notice, authenticate_user, register_user, is_valid_institutional_email, ADMIN_EMAIL_ERROR_MESSAGE
    from model import predict_category
    from engine import generate_summary, detect_deadlines
    from assistant import get_chatbot_response
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False

# Inject Custom Google Fonts and Premium Glassmorphic Styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .stApp {
        background: #0b1020;
        color: #f3f4f6;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.035);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 14px 44px rgba(0, 0, 0, 0.28);
        transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(129, 140, 248, 0.20);
        box-shadow: 0 18px 48px rgba(0, 0, 0, 0.34);
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-right: 6px;
    }
    .badge-exams { background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-placements { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-events { background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge-assignments { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-workshops { background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-general { background-color: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }
    .priority-high { color: #f87171; font-weight: 700; }
    .priority-medium { color: #fbbf24; font-weight: 700; }
    .priority-low { color: #34d399; font-weight: 700; }
    .chat-bubble-user {
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px 16px 0px 16px;
        padding: 14px 18px;
        margin-left: 20%;
        margin-bottom: 12px;
    }
    .chat-bubble-bot {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px 16px 16px 0px;
        padding: 14px 18px;
        margin-right: 20%;
        margin-bottom: 12px;
    }
    .auth-page {
        min-height: auto;
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
        padding: 0.35rem 1rem 0.75rem;
    }
    .auth-page::before {
        content: '';
        position: fixed;
        inset: 0;
        background: #0b1020;
        z-index: -1;
    }
    .auth-wrap {
        width: 100%;
        max-width: 980px;
        margin: 0 auto;
    }
    .auth-badge {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 50;
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        background: rgba(16, 185, 129, 0.14);
        border: 1px solid rgba(16, 185, 129, 0.32);
        color: #d1fae5;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }
    .auth-shell {
        min-height: auto;
        display: flex;
        align-items: flex-start;
        justify-content: flex-start;
    }
    .auth-hero {
        text-align: center;
        margin-bottom: 0.7rem;
        padding: 0 1rem;
    }
    .auth-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.14);
        border: 1px solid rgba(96, 165, 250, 0.20);
        color: #bfdbfe;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .auth-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(2.1rem, 4vw, 3.4rem);
        line-height: 1.05;
        font-weight: 800;
        color: #f8fafc;
        margin: 0.85rem 0 0.45rem;
    }
    .auth-subtitle {
        color: #cbd5e1;
        font-size: 1rem;
        line-height: 1.65;
        max-width: 42rem;
        margin: 0 auto;
    }
    .hero-row {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .hero-chip {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        padding: 0.68rem 0.9rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #e2e8f0;
        transition: transform 0.22s ease, border-color 0.22s ease, background 0.22s ease;
    }
    .hero-chip:hover {
        transform: translateY(-1px);
        border-color: rgba(96, 165, 250, 0.25);
        background: rgba(255, 255, 255, 0.06);
    }
    .hero-icon {
        width: 1.8rem;
        height: 1.8rem;
        display: grid;
        place-items: center;
        border-radius: 999px;
        background: rgba(99, 102, 241, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .auth-card-shell {
        width: 100%;
        max-width: 620px;
        margin: 0 auto;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        box-shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
        padding: 1rem 1.15rem 0.95rem;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }
    .auth-card-shell h2 {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.6rem;
        margin-bottom: 0.25rem;
        color: #f8fafc;
    }
    .auth-card-shell p {
        color: #cbd5e1;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    .auth-tabs {
        display: flex;
        gap: 0.7rem;
        margin-bottom: 1rem;
    }
    .auth-pill {
        flex: 1;
        text-align: center;
        padding: 0.75rem 0.95rem;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.04);
        color: #cbd5e1;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .auth-pill.active {
        background: rgba(59, 130, 246, 0.18);
        color: #ffffff;
        border-color: rgba(129, 140, 248, 0.45);
    }
    .auth-note {
        color: #94a3b8;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-top: 0.5rem;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    .stTextInput input, .stSelectbox [data-baseweb="select"] > div, .stTextArea textarea {
        background: rgba(9, 15, 29, 0.90) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.10) !important;
        border-radius: 14px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
    }
    .stTextInput input:focus, .stSelectbox [data-baseweb="select"] > div:focus-within, .stTextArea textarea:focus {
        border-color: rgba(129, 140, 248, 0.7) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.18) !important;
    }
    div[data-testid="stButton"] button {
        background: #2563eb;
        color: #ffffff;
        border: none;
        border-radius: 14px;
        padding: 0.78rem 1rem;
        font-weight: 700;
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.25);
        filter: brightness(1.05);
    }
    @media (max-width: 900px) {
        .auth-page {
            padding: 0.25rem 0.5rem 0.5rem;
        }
        .auth-title {
            font-size: clamp(1.8rem, 7vw, 2.4rem);
        }
        .auth-card-shell {
            padding: 0.9rem 0.9rem 0.8rem;
        }
        .auth-tabs {
            gap: 0.45rem;
        }
        .auth-pill {
            padding: 0.68rem 0.75rem;
        }
        .hero-chip {
            padding: 0.62rem 0.78rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialize
if 'user' not in st.session_state:
    st.session_state.user = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'ocr_cache' not in st.session_state:
    st.session_state.ocr_cache = ""
if 'ai_preview' not in st.session_state:
    st.session_state.ai_preview = None

API_ONLINE = is_backend_online()

if API_ONLINE:
    st.markdown("<div class='auth-badge'>● API Connected</div>", unsafe_allow_html=True)
elif not FALLBACK_AVAILABLE:
    st.error("Error: Local files are unreachable. Ensure database files are present!")
    st.stop()

if st.session_state.user is None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"], [data-testid="stSidebarNav"], section[data-testid="stSidebar"] {
                display: none !important;
                visibility: hidden !important;
                width: 0 !important;
                min-width: 0 !important;
                max-width: 0 !important;
                flex: 0 0 0 !important;
            }
            [data-testid="stAppViewContainer"] .main {
                padding-top: 0.15rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_auth_page():
    st.markdown("<div class='auth-page'><div class='auth-wrap'><div class='auth-shell'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='auth-hero'>
            <div class='auth-kicker'>AI NoticeBoard</div>
            <div class='auth-title'>AI-Powered Smart NoticeBoard</div>
            <div class='auth-subtitle'>Never Miss What Matters</div>
            <div class='auth-subtitle' style='margin-top:0.7rem;'>A focused campus workspace for notices, summaries, smart search, and deadline-aware communication.</div>
            <div class='hero-row'>
                <div class='hero-chip'><div class='hero-icon'>📢</div>Smart Notices</div>
                <div class='hero-chip'><div class='hero-icon'>🤖</div>AI Summaries</div>
                <div class='hero-chip'><div class='hero-icon'>🔍</div>Smart Search</div>
                <div class='hero-chip'><div class='hero-icon'>📅</div>Deadline Detection</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='auth-card-shell'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style='margin-bottom:0.35rem;'>
            <h2 style='margin:0;'>Access your campus workspace</h2>
            <p style='margin:0.35rem 0 0;'>Sign in to continue or create a new account for your role.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_action = st.radio("", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
    st.markdown(
        f"<div class='auth-tabs'><div class='auth-pill {'active' if auth_action == 'Sign In' else ''}'>Sign In</div><div class='auth-pill {'active' if auth_action == 'Create Account' else ''}'>Create Account</div></div>",
        unsafe_allow_html=True,
    )

    login_username = st.text_input("👤 Username", key="auth_user", placeholder="Enter your username")
    show_password = st.checkbox("Show password", value=False)
    password_input_type = "default" if show_password else "password"
    login_password = st.text_input("🔒 Password", type=password_input_type, key="auth_pass", placeholder="Enter your password")

    reg_role = "student"
    reg_branch = "All"
    reg_year = "All"
    reg_email = ""

    if auth_action == "Create Account":
        reg_role = st.selectbox("🎓 Role", ["student", "admin"])
        if reg_role == "student":
            reg_branch = st.selectbox("🏛️ Branch", ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"])
            reg_year = st.selectbox("📘 Current Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
        else:
            reg_email = st.text_input(
                "✉️ Institutional Email",
                placeholder="name@institution.edu.in",
                help="Required for Admin accounts only."
            )
            st.caption("Admin accounts must use an institutional email ending in .edu.in.")

    if st.button("Submit Credentials", use_container_width=True):
        if not login_username or not login_password:
            st.warning("Please fill in all credential fields!")
        else:
            if auth_action == "Sign In":
                if API_ONLINE:
                    try:
                        res = requests.post(f"{BACKEND_URL}/api/auth/login", json={
                            "username": login_username,
                            "password": login_password
                        })
                        payload = res.json()
                        if payload.get("success"):
                            st.session_state.user = payload["user"]
                            st.success(f"Welcome, {login_username}!")
                            st.rerun()
                        else:
                            st.error(payload.get("message", "Login failed."))
                    except Exception as e:
                        st.error(f"Network error: {e}")
                else:
                    result = authenticate_user(login_username, login_password)
                    if result["success"]:
                        st.session_state.user = result["user"]
                        st.success(f"Welcome, {login_username}! (Offline)")
                        st.rerun()
                    else:
                        st.error(result["message"])
            else:
                if reg_role == "admin" and not is_valid_institutional_email(reg_email):
                    st.error(ADMIN_EMAIL_ERROR_MESSAGE)
                else:
                    admin_email = reg_email.strip() if reg_role == "admin" else None
                    if API_ONLINE:
                        try:
                            res = requests.post(f"{BACKEND_URL}/api/auth/register", json={
                                "username": login_username,
                                "password": login_password,
                                "role": reg_role,
                                "email": admin_email,
                                "branch": reg_branch,
                                "year": reg_year
                            })
                            payload = res.json()
                            if payload.get("success"):
                                st.success("Account created! Please sign in.")
                            else:
                                st.error(payload.get("message", "Registration failed."))
                        except Exception as e:
                            st.error(f"Network error: {e}")
                    else:
                        result = register_user(login_username, login_password, reg_role, reg_branch, reg_year, admin_email)
                        if result["success"]:
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error(result["message"])

    st.markdown("<div class='auth-note'>Secure access for students, faculty, and administrators. The layout adapts automatically on smaller screens.</div>", unsafe_allow_html=True)
    st.markdown("</div></div></div>", unsafe_allow_html=True)

if st.session_state.user is None:
    render_auth_page()
    st.stop()

with st.sidebar:
    st.markdown("<h2 style='font-family:Space Grotesk; font-weight:700;'>🎓 AI NoticeBoard</h2>", unsafe_allow_html=True)
    if API_ONLINE:
        st.markdown("<div class='auth-badge' style='position: static; width: fit-content; margin-top: 0.25rem;'>● API Connected</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='auth-badge' style='position: static; width: fit-content; margin-top: 0.25rem; background: rgba(245, 158, 11, 0.14); border-color: rgba(245, 158, 11, 0.32); color: #fef3c7;'>● API Offline</div>", unsafe_allow_html=True)

u = st.session_state.user
st.markdown(f"### 👋 Welcome, **{u['username']}**")
st.markdown(f"**Role:** `{u['role'].upper()}`")
if u['role'] == 'student':
    st.markdown(f"**Branch:** `{u['branch']}`")
    st.markdown(f"**Year:** `{u['year']}`")
    
st.markdown("---")
st.markdown("### 🗺️ Navigation")
app_page = st.radio("Go To", [
    "📋 Main NoticeBoard",
    "🤖 AI Chatbot Assistant",
    "🚀 Smart Recommendations",
    "🛡️ Admin Panel" if u['role'] == 'admin' else None
])

st.markdown("---")
if st.button("Sign Out 🚪", use_container_width=True):
    st.session_state.user = None
    st.session_state.chat_history = []
    st.session_state.ocr_cache = ""
    st.session_state.ai_preview = None
    st.rerun()

USER_ROLE = st.session_state.user['role']
USER_BRANCH = st.session_state.user['branch']
USER_YEAR = st.session_state.user['year']

def load_all_notices(branch=None, year=None, category=None, priority=None, search=None):
    if API_ONLINE:
        try:
            params = {}
            if branch: params['branch'] = branch
            if year: params['year'] = year
            if category: params['category'] = category
            if priority: params['priority'] = priority
            if search: params['search'] = search
            res = requests.get(f"{BACKEND_URL}/api/notices", params=params)
            return res.json().get("notices", [])
        except:
            return []
    else:
        return get_notices(branch, year, category, priority, search)

if app_page == "📋 Main NoticeBoard":
    st.markdown("<h1 style='font-family:Space Grotesk; font-weight:800;'>📋 Campus NoticeBoard Feed</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_search, col_cat, col_prio = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search notices by title or keywords...", placeholder="Type exam, placement, workshop...")
    with col_cat:
        category_filter = st.selectbox("Category Filter", ["All", "Exams", "Placements", "Events", "Assignments", "Workshops", "General"])
    with col_prio:
        priority_filter = st.selectbox("Priority Filter", ["All", "High", "Medium", "Low"])
        
    if USER_ROLE == "student":
        notices = load_all_notices(branch=USER_BRANCH, year=USER_YEAR, category=category_filter, priority=priority_filter, search=search_query)
    else:
        notices = load_all_notices(branch="All", year="All", category=category_filter, priority=priority_filter, search=search_query)
        
    high_priority = [n for n in notices if n['priority'] == 'High']
    if high_priority:
        st.markdown("### 🚨 Urgent Notice Alerts")
        for u_notice in high_priority[:2]:
            st.warning(f"⚠️ **[{u_notice['category'].upper()}]** {u_notice['title']} - Deadlines: `{u_notice['deadlines'] or 'N/A'}`")
            
    st.markdown("---")
    
    if not notices:
        st.info("📭 No active notices matched your profile.")
    else:
        for idx, n in enumerate(notices):
            badge_class = f"badge-{n['category'].lower()}"
            priority_class = f"priority-{n['priority'].lower()}"
            
            st.markdown(f"""
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <span class="badge {badge_class}">{n['category']}</span>
                        <span style="font-size:0.85rem; color:#9ca3af;">Branch: <b>{n['branch']}</b> | Year: <b>{n['year']}</b></span>
                    </div>
                    <div>
                        <span class="badge-general">Priority: <span class="{priority_class}">{n['priority']}</span></span>
                    </div>
                </div>
                <h3 style="margin-top:0px; font-family:'Space Grotesk'; font-weight:700;">{n['title']}</h3>
                <p style="color:#cbd5e1; line-height:1.6;">{n['content']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_sum, col_dead = st.columns(2)
            with col_sum:
                with st.expander("🧠 View AI-Generated Summary"):
                    st.markdown(f"*{n['summary'] or 'No summary generated.'}*")
            with col_dead:
                with st.expander("⏳ Detected Deadlines & Attachments"):
                    if n['deadlines']:
                        st.markdown(f"🎯 **Deadlines Detected:** `{n['deadlines']}`")
                    else:
                        st.markdown("🎯 No specific deadline parsed.")
                    if n['file_path']:
                        st.markdown(f"📎 **Attached Document:** `{os.path.basename(n['file_path'])}`")
            st.markdown("<br>", unsafe_allow_html=True)

elif app_page == "🚀 Smart Recommendations":
    st.markdown("<h1 style='font-family:Space Grotesk; font-weight:800;'>🚀 Intelligent Notice Recommendations</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if USER_ROLE == "admin":
        st.info("ℹ️ Recommendations are generated for student profiles.")
    else:
        st.markdown(f"### 👤 Profile Vector: Branch = `{USER_BRANCH}` | Year = `{USER_YEAR}`")
        
        recs = []
        if API_ONLINE:
            try:
                res = requests.get(f"{BACKEND_URL}/api/recommendations", params={"branch": USER_BRANCH, "year": USER_YEAR})
                recs = res.json().get("notices", [])
            except:
                pass
        else:
            notices = get_notices(branch=USER_BRANCH, year=USER_YEAR)
            for n in notices:
                score = 0
                if n['priority'] == 'High': score += 10
                elif n['priority'] == 'Medium': score += 5
                if n['branch'] == USER_BRANCH: score += 8
                if n['year'] == USER_YEAR: score += 5
                
                n_copy = dict(n)
                n_copy['recommendation_score'] = score
                recs.append(n_copy)
            recs.sort(key=lambda x: x['recommendation_score'], reverse=True)
            
        if not recs:
            st.info("📭 No recommendations available.")
        else:
            top_rec = recs[0]
            st.markdown("### ⭐ Top Recommendation for You")
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(236, 72, 153, 0.1) 100%); border: 2px solid rgba(168, 85, 247, 0.4); border-radius:16px; padding:24px; margin-bottom:24px;">
                <span class="badge badge-events">MATCH SCORE: {top_rec.get('recommendation_score', 'N/A')} points</span>
                <h2 style="font-family:'Space Grotesk'; font-weight:800; color:white; margin-top:8px;">{top_rec['title']}</h2>
                <p style="color:#e2e8f0; font-size:1.05rem;">{top_rec['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 📋 Other Recommended Notices")
            for r in recs[1:5]:
                st.markdown(f"""
                <div class="glass-card">
                    <span class="badge badge-general">Score: {r.get('recommendation_score', 'N/A')} pts</span>
                    <b>{r['title']}</b>
                    <p style="font-size:0.9rem; color:#cbd5e1; margin-top:8px;">{r['summary']}</p>
                </div>
                """, unsafe_allow_html=True)

elif app_page == "🤖 AI Chatbot Assistant":
    st.markdown("<h1 style='font-family:Space Grotesk; font-weight:800;'>🤖 NLP NoticeBoard Assistant</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">🙋 **You:** {chat["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">🤖 **Assistant:** {chat["text"]}</div>', unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("chat_form", clear_on_submit=True):
        chat_query = st.text_input("💬 Ask your question:", placeholder="e.g., When are exams starting?")
        submit_chat = st.form_submit_button("Send Query 🚀")
        
    if submit_chat and chat_query:
        st.session_state.chat_history.append({"role": "user", "text": chat_query})
        
        if API_ONLINE:
            try:
                res = requests.post(f"{BACKEND_URL}/api/chatbot", json={
                    "query": chat_query,
                    "branch": USER_BRANCH,
                    "year": USER_YEAR
                })
                bot_reply = res.json().get("response", "Error fetching reply.")
            except Exception as e:
                bot_reply = f"Error: {e}"
        else:
            notices_list = get_notices(branch=USER_BRANCH, year=USER_YEAR)
            bot_reply = get_chatbot_response(chat_query, notices_list)
            
        st.session_state.chat_history.append({"role": "bot", "text": bot_reply})
        st.rerun()

elif app_page == "🛡️ Admin Panel" and USER_ROLE == "admin":
    st.markdown("<h1 style='font-family:Space Grotesk; font-weight:800;'>🛡️ Administrative Notice Manager</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    tab_upload, tab_manage = st.tabs(["📤 Publish New Notice", "⚙️ Manage Posted Notices"])
    
    with tab_upload:
        adm_title = st.text_input("Notice Title", placeholder="e.g. End Semester Exams Timetable")
        col_b, col_y, col_p = st.columns(3)
        with col_b:
            adm_branch = st.selectbox("Target Branch", ["All", "Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"])
        with col_y:
            adm_year = st.selectbox("Target Academic Year", ["All", "1st Year", "2nd Year", "3rd Year", "4th Year"])
        with col_p:
            adm_priority = st.selectbox("Notice Priority", ["High", "Medium", "Low"])
            
        st.markdown("---")
        input_mode = st.radio("Notice Input Method", ["Manual Text Entry", "Upload Document / Scan (Image/PDF)"])
        
        doc_text = ""
        uploaded_file = None
        
        if input_mode == "Manual Text Entry":
            doc_text = st.text_area("Type notice text details here:", height=200)
        else:
            uploaded_file = st.file_uploader("Upload Image notice or digital PDF", type=["png", "jpg", "jpeg", "pdf"])
            if uploaded_file is not None:
                st.success(f"File: `{uploaded_file.name}`")
                if st.button("🔍 Run AI OCR Text Extraction", use_container_width=True):
                    with st.spinner("Extracting text..."):
                        temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), uploaded_file.name)
                        with open(temp_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                            
                        if FALLBACK_AVAILABLE:
                            from server import perform_ocr
                            extracted = perform_ocr(temp_path)
                        else:
                            extracted = "[OCR module not linked]"
                            
                        st.session_state.ocr_cache = extracted
                        try: os.remove(temp_path)
                        except: pass
                        
            if st.session_state.ocr_cache:
                doc_text = st.text_area("Review/Edit extracted text:", value=st.session_state.ocr_cache, height=200)
                
        st.markdown("---")
        
        if st.button("🧠 Test Run AI NLP Pipeline", use_container_width=True):
            if not doc_text:
                st.warning("Please provide notice text.")
            else:
                pred_cat = predict_category(doc_text)
                gen_sum = generate_summary(doc_text, max_sentences=2)
                dates_parsed = detect_deadlines(doc_text)
                st.session_state.ai_preview = {
                    "category": pred_cat,
                    "summary": gen_sum,
                    "deadlines": dates_parsed
                }
                
        if st.session_state.ai_preview:
            ap = st.session_state.ai_preview
            st.markdown(f"🏷️ **Auto-Predicted Category:** `{ap['category']}`")
            st.markdown(f"📝 **Generated Summary:** *{ap['summary']}*")
            st.markdown(f"⏳ **Detected Deadlines/Dates:** `{ap['deadlines'] or 'None'}`")
            final_category = st.selectbox("Category Override", ["Exams", "Placements", "Events", "Assignments", "Workshops", "General"], index=["Exams", "Placements", "Events", "Assignments", "Workshops", "General"].index(ap['category']))
        else:
            final_category = "General"
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Publish Notice to Dashboard", type="primary", use_container_width=True):
            if not adm_title or not doc_text:
                st.error("Title and content are mandatory!")
            else:
                final_cat = final_category if st.session_state.ai_preview else predict_category(doc_text)
                final_sum = st.session_state.ai_preview["summary"] if st.session_state.ai_preview else generate_summary(doc_text, max_sentences=2)
                final_dead = st.session_state.ai_preview["deadlines"] if st.session_state.ai_preview else detect_deadlines(doc_text)
                
                if API_ONLINE:
                    try:
                        payload = {
                            "title": adm_title,
                            "branch": adm_branch,
                            "year": adm_year,
                            "priority": adm_priority,
                            "content": doc_text,
                            "category": final_cat
                        }
                        res = requests.post(f"{BACKEND_URL}/api/notices", data=payload)
                        if res.json().get("success"):
                            st.success("Notice published!")
                            st.session_state.ocr_cache = ""
                            st.session_state.ai_preview = None
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    res = add_notice(
                        title=adm_title,
                        content=doc_text,
                        summary=final_sum,
                        category=final_cat,
                        branch=adm_branch,
                        year=adm_year,
                        priority=adm_priority,
                        deadlines=final_dead,
                        file_path=None
                    )
                    if res["success"]:
                        st.success("Notice published offline!")
                        st.session_state.ocr_cache = ""
                        st.session_state.ai_preview = None
                        st.rerun()

    with tab_manage:
        st.markdown("### ⚙️ Delete or Edit Notices")
        adm_notices = load_all_notices()
        if not adm_notices:
            st.info("📭 No active notices.")
        else:
            for an in adm_notices:
                col_info, col_del = st.columns([6, 1])
                with col_info:
                    st.markdown(f"**{an['title']}** ({an['category']})")
                with col_del:
                    if st.button("Delete 🗑️", key=f"del_{an['id']}"):
                        if API_ONLINE:
                            try:
                                res = requests.delete(f"{BACKEND_URL}/api/notices/{an['id']}")
                                if res.json().get("success"):
                                    st.success("Deleted!")
                                    st.rerun()
                            except:
                                pass
                        else:
                            res = delete_notice(an['id'])
                            if res["success"]:
                                st.success("Deleted offline!")
                                st.rerun()
                st.markdown("<hr style='margin:10px 0px;'>", unsafe_allow_html=True)
