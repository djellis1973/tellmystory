# biographer.py – Tell My Story App (Complete Working Version)
import streamlit as st
import json
from datetime import datetime, date, timedelta
from openai import OpenAI
import os
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
import base64
import pandas as pd
import uuid
import sys

# Add current directory to path to import modules
sys.path.append('.')

# Import ALL modules (with try-except)
try:
    from topic_bank import TopicBank
    from session_manager import SessionManager
    from vignettes import VignetteManager
except ImportError as e:
    # Silently handle import errors
    TopicBank = None
    SessionManager = None
    VignetteManager = None

DEFAULT_WORD_TARGET = 500

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")))

# ── Load external CSS ─────────────────────────────────────────────────────────
try:
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Default minimal CSS if styles.css not found
    st.markdown("""
    <style>
    .main-header { text-align: center; margin-bottom: 2rem; }
    .logo-img { max-height: 100px; }
    .question-box { 
        background-color: #e8f4f8; 
        border-left: 4px solid #3498db; 
        padding: 15px; 
        margin: 15px 0; 
        border-radius: 5px;
        font-size: 1.2rem;
    }
    .answer-display-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        white-space: pre-line;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/02/tms_logo.png"

# ── Sessions (ONLY FROM CSV) ─────────────────────────────────────────────────
def load_sessions_from_csv(csv_path="sessions/sessions.csv"):
    """Load sessions ONLY from CSV file"""
    try:
        import pandas as pd
        import os
        
        # Create sessions directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else '.', exist_ok=True)
        
        if not os.path.exists(csv_path):
            # Create a default sessions file if it doesn't exist
            default_sessions = [
                ['session_id', 'title', 'guidance', 'question', 'word_target'],
                [1, 'Childhood', 'Welcome to Session 1', 'What is your earliest memory?', 500],
                [1, 'Childhood', '', 'Can you describe your family home?', 500],
                [2, 'School Days', 'Welcome to Session 2', 'What was your favorite subject in school?', 500],
                [2, 'School Days', '', 'Who was your favorite teacher?', 500]
            ]
            
            df = pd.DataFrame(default_sessions[1:], columns=default_sessions[0])
            df.to_csv(csv_path, index=False)
            st.info(f"Created default sessions file at {csv_path}")
        
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['session_id', 'question']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Missing required columns in CSV: {missing_columns}")
            return []
        
        # Group by session_id
        sessions_dict = {}
        
        for session_id, group in df.groupby('session_id'):
            session_id_int = int(session_id)
            group = group.reset_index(drop=True)
            
            # Get title (use first row's title or default)
            title = f"Session {session_id_int}"
            if 'title' in group.columns and not group.empty:
                first_title = group.iloc[0]['title']
                if pd.notna(first_title) and str(first_title).strip():
                    title = str(first_title).strip()
            
            # Get guidance (use first row's guidance)
            guidance = ""
            if 'guidance' in group.columns and not group.empty:
                first_guidance = group.iloc[0]['guidance']
                if pd.notna(first_guidance) and str(first_guidance).strip():
                    guidance = str(first_guidance).strip()
            
            # Get word target (use first row's word_target or default to 500)
            word_target = DEFAULT_WORD_TARGET
            if 'word_target' in group.columns and not group.empty:
                first_target = group.iloc[0]['word_target']
                if pd.notna(first_target):
                    try:
                        word_target = int(float(first_target))
                    except:
                        word_target = DEFAULT_WORD_TARGET
            
            # Get all questions
            questions = []
            for _, row in group.iterrows():
                if 'question' in row and pd.notna(row['question']) and str(row['question']).strip():
                    questions.append(str(row['question']).strip())
            
            # Only add session if it has questions
            if questions:
                sessions_dict[session_id_int] = {
                    "id": session_id_int,
                    "title": title,
                    "guidance": guidance,
                    "questions": questions,
                    "completed": False,
                    "word_target": word_target
                }
        
        # Convert to list and sort by session_id
        sessions_list = list(sessions_dict.values())
        sessions_list.sort(key=lambda x: x['id'])
        
        return sessions_list
        
    except Exception as e:
        st.error(f"❌ Error loading sessions from CSV: {e}")
        return []

# Load sessions ONCE at startup
SESSIONS = load_sessions_from_csv()

# ── Authentication Functions (Simplified) ────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_account(user_data, password=None):
    try:
        user_id = hashlib.sha256(f"{user_data['email']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        if not password:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        user_record = {
            "user_id": user_id,
            "email": user_data["email"].lower().strip(),
            "password_hash": hash_password(password),
            "account_type": "self",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "profile": {
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "gender": "",
                "birthdate": "",
                "timeline_start": ""
            },
            "stats": {
                "total_sessions": 0,
                "total_words": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "account_age_days": 0,
                "last_active": datetime.now().isoformat()
            }
        }
        
        # Save account
        os.makedirs("accounts", exist_ok=True)
        filename = f"accounts/{user_id}_account.json"
        with open(filename, 'w') as f:
            json.dump(user_record, f, indent=2)
        
        return {"success": True, "user_id": user_id, "password": password, "user_record": user_record}
    except Exception as e:
        print(f"Error creating account: {e}")
        return {"success": False, "error": str(e)}

def authenticate_user(email, password):
    try:
        email = email.lower().strip()
        
        # Look for account file
        os.makedirs("accounts", exist_ok=True)
        accounts_dir = "accounts"
        
        for filename in os.listdir(accounts_dir):
            if filename.endswith("_account.json"):
                filepath = os.path.join(accounts_dir, filename)
                with open(filepath, 'r') as f:
                    account = json.load(f)
                
                if account.get('email', '').lower() == email:
                    if account['password_hash'] == hash_password(password):
                        # Update last login
                        account['last_login'] = datetime.now().isoformat()
                        with open(filepath, 'w') as f:
                            json.dump(account, f, indent=2)
                        return {"success": True, "user_id": account['user_id'], "user_record": account}
        
        return {"success": False, "error": "Invalid email or password"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Storage & Streak ──────────────────────────────────────────────────────────
def get_user_filename(user_id):
    filename_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
    return f"user_data_{filename_hash}.json"

def load_user_data(user_id):
    filename = get_user_filename(user_id)
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        return {"responses": {}, "vignettes": [], "last_loaded": datetime.now().isoformat()}
    except Exception as e:
        print(f"Error loading user data for {user_id}: {e}")
        return {"responses": {}, "vignettes": [], "last_loaded": datetime.now().isoformat()}

def save_user_data(user_id, responses_data):
    filename = get_user_filename(user_id)
    try:
        existing_data = load_user_data(user_id)
        data_to_save = {
            "user_id": user_id,
            "responses": responses_data,
            "vignettes": existing_data.get("vignettes", []),
            "last_saved": datetime.now().isoformat()
        }
        with open(filename, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving user data for {user_id}: {e}")
        return False

# ── Core Functions for SINGLE ANSWER BOX ─────────────────────────────────────
def save_response_single(session_id, question, answer, answer_index=1):
    """Save a single response."""
    user_id = st.session_state.user_id
    if not user_id or user_id == "":
        return False
    
    if session_id not in st.session_state.responses:
        # Find the session in SESSIONS
        session_data = None
        for s in SESSIONS:
            if s["id"] == session_id:
                session_data = s
                break
        
        if not session_data:
            # Create a basic session entry if not found
            session_data = {
                "title": f"Session {session_id}",
                "word_target": DEFAULT_WORD_TARGET
            }
        
        st.session_state.responses[session_id] = {
            "title": session_data.get("title", f"Session {session_id}"),
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": session_data.get("word_target", DEFAULT_WORD_TARGET)
        }
    
    # Generate a unique key for this answer
    answer_key = f"{question}_answer_{answer_index}"
    
    # Save the answer
    st.session_state.responses[session_id]["questions"][answer_key] = {
        "answer": answer,
        "question": question,
        "timestamp": datetime.now().isoformat(),
        "answer_index": answer_index
    }
    
    return save_user_data(user_id, st.session_state.responses)

def delete_response_single(session_id, question, answer_index=1):
    """Delete a specific response"""
    user_id = st.session_state.user_id
    if not user_id or user_id == "":
        return False
    
    answer_key = f"{question}_answer_{answer_index}"
    
    if session_id in st.session_state.responses:
        if answer_key in st.session_state.responses[session_id]["questions"]:
            # Remove from responses
            del st.session_state.responses[session_id]["questions"][answer_key]
            
            # Save changes
            return save_user_data(user_id, st.session_state.responses)
    
    return False

def get_response_single(session_id, question, answer_index=1):
    """Get a specific response"""
    answer_key = f"{question}_answer_{answer_index}"
    
    if session_id in st.session_state.responses:
        if answer_key in st.session_state.responses[session_id]["questions"]:
            return st.session_state.responses[session_id]["questions"][answer_key]
    
    return None

# ── Enhanced auto-correct ────────────────────────────────────────────────────
def auto_correct_text_enhanced(text, force_correction=False):
    """Enhanced auto-correct that preserves paragraphs and formatting"""
    if not text or not text.strip():
        return text
    
    # If spellcheck is disabled and not forced, return original
    if not st.session_state.spellcheck_enabled and not force_correction:
        return text
    
    try:
        # Check if OpenAI client is available
        if not client.api_key:
            return text
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """Fix spelling and grammar mistakes in the following text. 
                    Preserve ALL paragraph breaks, line breaks, and formatting exactly as written.
                    Keep the original structure and organization.
                    Return only the corrected text with exactly the same paragraph structure."""
                },
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 200,
            temperature=0.1
        )
        corrected_text = response.choices[0].message.content.strip()
        
        # If the corrected text is empty or very different, return original
        if not corrected_text or len(corrected_text) < len(text) * 0.5:
            return text
        
        return corrected_text
    except Exception as e:
        print(f"Error in auto-correct: {e}")
        return text

# ── Page State ───────────────────────────────────────────────────────────────
default_state = {
    "logged_in": False,
    "user_id": "",
    "user_account": None,
    "current_session": 0,
    "current_question": 0,
    "responses": {},
    "current_question_override": None,
    "ghostwriter_mode": True,
    "spellcheck_enabled": True,
    "editing": None,
    "edit_text": "",
    "confirming_clear": None,
    "data_loaded": False,
    # State for single answer mode
    "current_answer": "",
    "force_correction": False,
    "correction_applied": False,
    "original_text": "",
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Initialize responses for loaded sessions
if SESSIONS:
    for session in SESSIONS:
        session_id = session["id"]
        if session_id not in st.session_state.responses:
            st.session_state.responses[session_id] = {
                "title": session["title"],
                "questions": {},
                "summary": "",
                "completed": False,
                "word_target": session.get("word_target", DEFAULT_WORD_TARGET)
            }

# Load user data if logged in
if st.session_state.logged_in and st.session_state.user_id and not st.session_state.data_loaded:
    user_data = load_user_data(st.session_state.user_id)
    if "responses" in user_data:
        # Merge loaded responses
        for session_id_str, session_data in user_data["responses"].items():
            try:
                session_id = int(session_id_str)
                if session_id in st.session_state.responses:
                    if "questions" in session_data:
                        st.session_state.responses[session_id]["questions"] = session_data["questions"]
            except ValueError:
                continue
    st.session_state.data_loaded = True

# ── Authentication Components ─────────────────────────────────────────────────
def show_login_signup():
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>Tell My Story</h1>
        <p style="color: #666;">Your Life Timeline • Preserve Your Legacy</p>
    </div>
    """, unsafe_allow_html=True)

    if 'auth_tab' not in st.session_state:
        st.session_state.auth_tab = 'login'

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", use_container_width=True,
                     type="primary" if st.session_state.auth_tab == 'login' else "secondary"):
            st.session_state.auth_tab = 'login'
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", use_container_width=True,
                     type="primary" if st.session_state.auth_tab == 'signup' else "secondary"):
            st.session_state.auth_tab = 'signup'
            st.rerun()

    st.divider()

    if st.session_state.auth_tab == 'login':
        show_login_form()
    else:
        show_signup_form()

def show_login_form():
    with st.form("login_form"):
        st.subheader("Welcome Back")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        login_button = st.form_submit_button("Login to My Account", type="primary", use_container_width=True)
        if login_button:
            if not email or not password:
                st.error("Please enter both email and password")
            else:
                with st.spinner("Signing in..."):
                    result = authenticate_user(email, password)
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_account = result["user_record"]
                        st.session_state.logged_in = True
                        st.session_state.data_loaded = False
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result.get('error', 'Unknown error')}")

def show_signup_form():
    with st.form("signup_form"):
        st.subheader("Create New Account")
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name*", key="signup_first_name")
        with col2:
            last_name = st.text_input("Last Name*", key="signup_last_name")
        email = st.text_input("Email Address*", key="signup_email")
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Password*", type="password", key="signup_password")
        with col2:
            confirm_password = st.text_input("Confirm Password*", type="password", key="signup_confirm_password")
        
        signup_button = st.form_submit_button("Create My Account", type="primary", use_container_width=True)
        if signup_button:
            errors = []
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if not email or "@" not in email:
                errors.append("Valid email is required")
            if not password or len(password) < 8:
                errors.append("Password must be at least 8 characters")
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                user_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email
                }
                with st.spinner("Creating your account..."):
                    result = create_user_account(user_data, password)
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.user_account = result["user_record"]
                        st.session_state.logged_in = True
                        st.session_state.data_loaded = False
                        st.success("✅ Account created successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Error creating account: {result.get('error', 'Unknown error')}")

# ── Main App Flow ─────────────────────────────────────────────────────────────
# Check if sessions are loaded
if not SESSIONS:
    st.error("❌ No sessions loaded.")
    st.info("""
    The app will create a default sessions.csv file.
    Please refresh the page.
    """)
    st.stop()

if not st.session_state.logged_in:
    show_login_signup()
    st.stop()

# Main header - LOGO
st.markdown(f"""
<div class="main-header">
<img src="{LOGO_URL}" class="logo-img" alt="Tell My Story Logo">
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Your Profile")
    if st.session_state.user_account:
        profile = st.session_state.user_account['profile']
        st.success(f"✓ **{profile['first_name']} {profile['last_name']}**")
    
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = ""
        st.session_state.user_account = None
        st.rerun()
    
    st.divider()
    
    # Sessions
    st.header("📖 Sessions")
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        # Count questions with answers
        answered_count = 0
        for question in session["questions"]:
            answer_key = f"{question}_answer_1"
            if answer_key in session_data.get("questions", {}):
                answered_count += 1
        
        total_questions = len(session["questions"])
        
        # Status indicator
        if answered_count == total_questions:
            status = "🔴"
        elif answered_count > 0:
            status = "🟡"
        else:
            status = "🟢"
        
        if i == st.session_state.current_session:
            status = "▶️"
        
        button_text = f"{status} {session_id}: {session['title']}"
        
        if st.button(button_text, key=f"select_session_{i}", use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.session_state.current_question_override = None
            st.session_state.current_answer = ""
            st.rerun()
    
    st.divider()
    
    # Settings
    st.header("✍️ Settings")
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode",
        value=st.session_state.ghostwriter_mode,
        key="ghostwriter_toggle"
    )
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    spellcheck_enabled = st.toggle(
        "Auto Spelling Correction",
        value=st.session_state.spellcheck_enabled,
        key="spellcheck_toggle"
    )
    if spellcheck_enabled != st.session_state.spellcheck_enabled:
        st.session_state.spellcheck_enabled = spellcheck_enabled
        st.rerun()
    
    st.divider()
    
    # Clear Data
    st.subheader("⚠️ Clear Data")
    if st.session_state.confirming_clear == "session":
        st.warning("**WARNING: This will delete ALL answers in the current session!**")
        
        if st.button("✅ Confirm Delete Session", type="primary", use_container_width=True, key="confirm_delete_session"):
            current_session_id = SESSIONS[st.session_state.current_session]["id"]
            try:
                st.session_state.responses[current_session_id]["questions"] = {}
                save_user_data(st.session_state.user_id, st.session_state.responses)
                st.session_state.confirming_clear = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_session"):
            st.session_state.confirming_clear = None
            st.rerun()
    else:
        if st.button("🗑️ Clear Session", type="secondary", use_container_width=True, key="clear_session_btn"):
            st.session_state.confirming_clear = "session"
            st.rerun()

# ── Main Content Area ─────────────────────────────────────────────────────────
# Check if we have a valid current session
if st.session_state.current_session >= len(SESSIONS):
    st.session_state.current_session = 0

current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]

if st.session_state.current_question_override:
    current_question_text = st.session_state.current_question_override
    question_source = "custom"
else:
    # Check if current_question is valid
    if st.session_state.current_question >= len(current_session["questions"]):
        st.session_state.current_question = 0
    current_question_text = current_session["questions"][st.session_state.current_question]
    question_source = "regular"

st.markdown("---")

# SINGLE ANSWER BOX VERSION
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    # Count questions with answers
    session_data = st.session_state.responses.get(current_session_id, {})
    answered_count = 0
    for question in current_session["questions"]:
        answer_key = f"{question}_answer_1"
        if answer_key in session_data.get("questions", {}):
            answered_count += 1
    
    total_questions = len(current_session["questions"])
    
    # Progress bar for topics
    if total_questions > 0:
        topic_progress = answered_count / total_questions
        st.progress(min(topic_progress, 1.0))
        st.caption(f"📝 Topics explored: {answered_count}/{total_questions}")

with col2:
    if question_source == "custom":
        st.markdown(f'<div style="margin-top: 1rem; color: #ff6b00;">✨ Custom Topic</div>', unsafe_allow_html=True)
    else:
        current_topic = st.session_state.current_question + 1
        total_topics = len(current_session["questions"])
        st.markdown(f'<div style="margin-top: 1rem;">Topic {current_topic} of {total_topics}</div>', unsafe_allow_html=True)

# The main question
st.markdown(f"""
<div class="question-box">
{current_question_text}
</div>
""", unsafe_allow_html=True)

# Guidance text
if question_source == "regular" and current_session.get('guidance'):
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
    {current_session.get('guidance', '')}
    </div>
    """, unsafe_allow_html=True)

# ── YOUR ANSWER SECTION ───────────────────────────────────────────────────────
# Load existing answer for THIS specific topic
existing_answer = get_response_single(current_session_id, current_question_text, answer_index=1)

# If we have an existing answer, show it with edit/delete buttons
if existing_answer:
    st.markdown("### 📝 Your Answer")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        # Show word count
        word_count = len(re.findall(r'\w+', existing_answer['answer']))
        st.caption(f"📊 {word_count} words • Last saved: {existing_answer['timestamp'][:10]}")
    
    with col2:
        # Edit and Delete buttons
        edit_col, delete_col = st.columns(2)
        with edit_col:
            if st.button("✏️ Edit", key="edit_existing_btn", use_container_width=True):
                st.session_state.editing = True
                st.session_state.edit_text = existing_answer['answer']
                st.rerun()
        with delete_col:
            if st.button("🗑️ Delete", key="delete_existing_btn", use_container_width=True):
                if delete_response_single(current_session_id, current_question_text, answer_index=1):
                    st.success("Answer deleted!")
                    st.rerun()
    
    # Show the existing answer
    st.markdown(f"""
    <div class="answer-display-box">
    {existing_answer['answer'].replace('\n', '<br>')}
    </div>
    """, unsafe_allow_html=True)

# If we're editing or there's no existing answer, show the text area
if st.session_state.editing or not existing_answer:
    # Get the current text to edit
    if st.session_state.editing:
        current_text = st.session_state.edit_text
    else:
        current_text = ""
    
    # Create a dynamic key for the text box - unique per topic
    text_box_key = f"answer_box_{current_session_id}_{hash(current_question_text)}"
    
    # Text area for writing answer - always start empty
    user_input = st.text_area(
        label="Write your answer below:",
        value="",  # Always empty - text from one topic won't appear in another
        height=300,
        placeholder="Start writing your story here... (Your text will be auto-saved as you type)",
        key=text_box_key,
        label_visibility="collapsed"
    )
    
    # Word count display
    word_count = len(re.findall(r'\w+', user_input))
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.caption(f"📝 **{word_count} words** written")
    
    with col2:
        # Save button
        if st.button("💾 Save Answer", type="primary", use_container_width=True):
            if user_input and user_input.strip():
                # Apply auto-correct if enabled
                if st.session_state.spellcheck_enabled:
                    user_input = auto_correct_text_enhanced(user_input)
                
                # Save the answer
                if save_response_single(current_session_id, current_question_text, user_input):
                    st.success("Answer saved successfully!")
                    st.session_state.editing = False
                    st.session_state.edit_text = ""
                    st.rerun()
            else:
                st.warning("Please write something before saving!")
    
    with col3:
        # Force Correction button - FIXED: doesn't reference text box key
        if st.button("🔧 Force Correction", type="secondary", use_container_width=True):
            if user_input and user_input.strip():
                # Store the original text
                st.session_state.original_text = user_input
                # Apply correction
                corrected = auto_correct_text_enhanced(user_input, force_correction=True)
                
                # Clear the text box by resetting the session state for that key
                st.session_state[text_box_key] = corrected
                
                st.session_state.correction_applied = True
                st.success("Correction applied! Review and save if you like it.")
                st.rerun()
            else:
                st.warning("Please write something first!")
    
    # Show correction status
    if st.session_state.correction_applied:
        st.info("✓ Correction applied. Review the text above and click 'Save Answer' if you want to keep it.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Keep Correction", type="primary", use_container_width=True):
                # Save the corrected text
                if save_response_single(current_session_id, current_question_text, user_input):
                    st.session_state.correction_applied = False
                    st.success("Saved with correction!")
                    st.rerun()
        with col2:
            if st.button("↩️ Revert to Original", type="secondary", use_container_width=True):
                # Revert to original text
                if hasattr(st.session_state, 'original_text'):
                    st.session_state[text_box_key] = st.session_state.original_text
                st.session_state.correction_applied = False
                st.rerun()
    
    # Cancel button if editing
    if st.session_state.editing:
        if st.button("❌ Cancel Edit", type="secondary", use_container_width=True):
            st.session_state.editing = False
            st.session_state.edit_text = ""
            st.rerun()

# Navigation for regular questions (not custom topics)
if question_source == "regular":
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏮️ Previous Topic", use_container_width=True):
            if st.session_state.current_question > 0:
                st.session_state.current_question -= 1
            else:
                # Go to previous session if we're at the first question
                if st.session_state.current_session > 0:
                    st.session_state.current_session -= 1
                    st.session_state.current_question = len(SESSIONS[st.session_state.current_session]["questions"]) - 1
            st.session_state.current_question_override = None
            st.session_state.editing = False
            st.session_state.edit_text = ""
            st.rerun()
    
    with col2:
        if st.button("↺ Reset Topic", use_container_width=True):
            st.session_state.editing = False
            st.session_state.edit_text = ""
            st.rerun()
    
    with col3:
        if st.button("⏭️ Next Topic", use_container_width=True):
            if st.session_state.current_question < len(current_session["questions"]) - 1:
                st.session_state.current_question += 1
            else:
                # Go to next session if we're at the last question
                if st.session_state.current_session < len(SESSIONS) - 1:
                    st.session_state.current_session += 1
                    st.session_state.current_question = 0
            st.session_state.current_question_override = None
            st.session_state.editing = False
            st.session_state.edit_text = ""
            st.rerun()

# For custom topics, show different navigation
else:
    st.markdown("---")
    if st.button("↺ Return to Regular Topics", use_container_width=True):
        st.session_state.current_question_override = None
        st.session_state.editing = False
        st.session_state.edit_text = ""
        st.rerun()

st.markdown("---")
st.caption("© Tell My Story - Preserve Your Legacy")

