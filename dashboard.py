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
    from db import get_notices, add_notice, delete_notice, authenticate_user, register_user
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
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
        color: #f3f4f6;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.12);
    }
    .hero-banner {
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        padding: 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.2);
    }
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: white;
        margin-bottom: 5px;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
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

with st.sidebar:
    st.markdown("<h2 style='font-family:Space Grotesk; font-weight:700;'>🎓 AI NoticeBoard</h2>", unsafe_allow_html=True)
    
    if API_ONLINE:
        st.markdown("<span style='color:#34d399;'>●</span> **Flask REST API:** `CONNECTED`", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#fbbf24;'>●</span> **Flask REST API:** `OFFLINE (FALLBACK LIVE)`", unsafe_allow_html=True)
        if not FALLBACK_AVAILABLE:
            st.error("Error: Local files are unreachable. Ensure database files are present!")
            st.stop()
            
    st.markdown("---")
    
    if st.session_state.user is None:
        st.markdown("### 🔐 User Login")
        auth_action = st.radio("Select Action", ["Sign In", "Create Account"])
        
        login_username = st.text_input("Username", key="auth_user")
        login_password = st.text_input("Password", type="password", key="auth_pass")
        
        reg_role = "student"
        reg_branch = "All"
        reg_year = "All"
        if auth_action == "Create Account":
            reg_role = st.selectbox("Role", ["student", "admin"])
            if reg_role == "student":
                reg_branch = st.selectbox("Branch", ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"])
                reg_year = st.selectbox("Current Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
                
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
                    if API_ONLINE:
                        try:
                            res = requests.post(f"{BACKEND_URL}/api/auth/register", json={
                                "username": login_username,
                                "password": login_password,
                                "role": reg_role,
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
                        result = register_user(login_username, login_password, reg_role, reg_branch, reg_year)
                        if result["success"]:
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error(result["message"])
    else:
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

if st.session_state.user is None:
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">🎓 AI-Powered Smart NoticeBoard</h1>
        <p class="hero-subtitle">The next-generation digital noticeboard hub featuring modern OCR, NLP summaries, categorization, and contextual chatbot support.</p>
    </div>
    """, unsafe_allow_html=True)
    st.info("💡 **Welcome!** Please login or register as a student in the sidebar panel to explore.")
    st.stop()

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
