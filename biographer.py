# tellmystory.py – Complete Working Version with ALL Fixes
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
import time
from io import BytesIO
import tempfile

# ============================================================================
# DOCX LIBRARY IMPORT FOR PUBLISHER
# ============================================================================
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Add current directory to path to import modules
sys.path.append('.')

# Import ALL modules
try:
    from topic_bank import TopicBank
    from session_manager import SessionManager
    from vignettes import VignetteManager
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Please ensure all .py files are in the same directory")
    # Set to None if import fails
    TopicBank = None
    SessionManager = None
    VignetteManager = None

DEFAULT_WORD_TARGET = 500

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ── Load external CSS ─────────────────────────────────────────────────────────
try:
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("styles.css not found – layout may look broken")

# ── Constants ─────────────────────────────────────────────────────────────────
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/02/tms_logo.png"

# ── Sessions (ONLY FROM CSV - NO HARDCODING) ─────────────────────────────────
def load_sessions_from_csv(csv_path="sessions/sessions.csv"):
    """Load sessions ONLY from CSV file - NO hardcoded fallback"""
    try:
        import pandas as pd
        import os
        
        # Create sessions directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else '.', exist_ok=True)
        
        if not os.path.exists(csv_path):
            # CSV doesn't exist - show error and return empty list
            st.error(f"❌ Sessions CSV file not found: {csv_path}")
            st.info("""
            Please create a `sessions/sessions.csv` file with this format:
            
            session_id,title,guidance,question,word_target
            1,Childhood,"Welcome to Session 1...","What is your earliest memory?",500
            1,Childhood,,"Can you describe your family home?",500
            
            Guidance only needs to be in the first row of each session.
            """)
            return []
        
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['session_id', 'question']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Missing required columns in CSV: {missing_columns}")
            st.info("CSV must have at least: session_id, question")
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
        
        if not sessions_list:
            st.warning("⚠️ No sessions found in CSV file")
            return []
        
        # REMOVED: st.success(f"✅ Loaded {len(sessions_list)} sessions from CSV")
        return sessions_list
        
    except Exception as e:
        st.error(f"❌ Error loading sessions from CSV: {e}")
        return []

# Load sessions ONCE at startup
SESSIONS = load_sessions_from_csv()

# ── Historical events – CSV only ──────────────────────────────────────────────
def create_default_events_csv():
    if not os.path.exists("historical_events.csv"):
        with open("historical_events.csv", "w", encoding="utf-8") as f:
            f.write("year_range,event,category,region,description\n")

def load_historical_events():
    create_default_events_csv()
    try:
        df = pd.read_csv("historical_events.csv")
        events_by_decade = {}
        for _, row in df.iterrows():
            decade = str(row['year_range']).strip()
            events_by_decade.setdefault(decade, []).append(row.to_dict())
        return events_by_decade
    except:
        return {}

def get_events_for_birth_year(birth_year):
    events_by_decade = load_historical_events()
    relevant = []
    start_decade = (birth_year // 10) * 10
    current_year = datetime.now().year
    for decade in range(start_decade, current_year + 10, 10):
        key = f"{decade}s"
        if key in events_by_decade:
            for ev in events_by_decade[key]:
                approx_year = int(key.replace('s', '')) + 5
                age = approx_year - birth_year
                if age >= 0:
                    ev_copy = ev.copy()
                    ev_copy['approx_age'] = age
                    relevant.append(ev_copy)
    relevant.sort(key=lambda x: x.get('year_range', '9999'))
    return relevant[:20]

# ── Email Configuration ───────────────────────────────────────────────────────
EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
    "sender_email": st.secrets.get("SENDER_EMAIL", ""),
    "sender_password": st.secrets.get("SENDER_PASSWORD", ""),
    "use_tls": True
}

# ── Authentication Functions ──────────────────────────────────────────────────
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    return stored_hash == hash_password(password)

def create_user_account(user_data, password=None):
    try:
        user_id = hashlib.sha256(f"{user_data['email']}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        if not password:
            password = generate_password()
        user_record = {
            "user_id": user_id,
            "email": user_data["email"].lower().strip(),
            "password_hash": hash_password(password),
            "account_type": user_data.get("account_for", "self"),
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "profile": {
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "gender": user_data.get("gender", ""),
                "birthdate": user_data.get("birthdate", ""),
                "timeline_start": user_data.get("birthdate", "")
            },
            "settings": {
                "email_notifications": True,
                "auto_save": True,
                "privacy_level": "private",
                "theme": "light",
                "email_verified": False
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
        save_account_data(user_record)
        return {"success": True, "user_id": user_id, "password": password, "user_record": user_record}
    except Exception as e:
        print(f"Error creating account: {e}")
        return {"success": False, "error": str(e)}

def save_account_data(user_record):
    try:
        os.makedirs("accounts", exist_ok=True)
        filename = f"accounts/{user_record['user_id']}_account.json"
        json.dump(user_record, open(filename, 'w'), indent=2)
        update_accounts_index(user_record)
        return True
    except Exception as e:
        print(f"Error saving account: {e}")
        return False

def update_accounts_index(user_record):
    try:
        index_file = "accounts/accounts_index.json"
        os.makedirs("accounts", exist_ok=True)
        index = json.load(open(index_file, 'r')) if os.path.exists(index_file) else {}
        index[user_record['user_id']] = {
            "email": user_record['email'],
            "first_name": user_record['profile']['first_name'],
            "last_name": user_record['profile']['last_name'],
            "created_at": user_record['created_at'],
            "account_type": user_record['account_type']
        }
        json.dump(index, open(index_file, 'w'), indent=2)
        return True
    except Exception as e:
        print(f"Error updating index: {e}")
        return False

def get_account_data(user_id=None, email=None):
    try:
        os.makedirs("accounts", exist_ok=True)
        if user_id:
            filename = f"accounts/{user_id}_account.json"
            if os.path.exists(filename):
                return json.load(open(filename, 'r'))
        if email:
            email = email.lower().strip()
            index_file = "accounts/accounts_index.json"
            if os.path.exists(index_file):
                index = json.load(open(index_file, 'r'))
                for uid, data in index.items():
                    if data.get("email", "").lower() == email:
                        filename = f"accounts/{uid}_account.json"
                        if os.path.exists(filename):
                            return json.load(open(filename, 'r'))
    except Exception as e:
        print(f"Error loading account: {e}")
    return None

def authenticate_user(email, password):
    try:
        account = get_account_data(email=email)
        if account and verify_password(account['password_hash'], password):
            account['last_login'] = datetime.now().isoformat()
            save_account_data(account)
            return {"success": True, "user_id": account['user_id'], "user_record": account}
        return {"success": False, "error": "Invalid email or password"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_welcome_email(user_data, credentials):
    try:
        if not EMAIL_CONFIG['sender_email'] or not EMAIL_CONFIG['sender_password']:
            print("Email not configured")
            return False
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_data['email']
        msg['Subject'] = "Welcome to Tell My Story - Your Account Details"
        body = f"""
        <html>
        <body style="font-family: Arial; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Welcome to Tell My Story, {user_data['first_name']}!</h2>
            <p>Thank you for creating your account.</p>
            <div style="background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0;">
                <h3 style="color: #2c3e50; margin-top: 0;">Your Account Details:</h3>
                <p><strong>Account ID:</strong> {credentials['user_id']}</p>
                <p><strong>Email:</strong> {user_data['email']}</p>
                <p><strong>Password:</strong> {credentials['password']}</p>
            </div>
            <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h4 style="color: #2c3e50; margin-top: 0;">Getting Started:</h4>
                <ol>
                    <li>Log in with your email and password</li>
                    <li>Start building your timeline from your birthdate: {user_data.get('birthdate', 'Not specified')}</li>
                    <li>Add memories, photos, and stories to your timeline</li>
                    <li>Share with family and friends</li>
                </ol>
            </div>
            <p>Your Tell My Story timeline starts from your birthdate and grows with you as you add more memories and milestones.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="#" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Start Your Journey</a>
            </div>
            <p style="color: #7f8c8d; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px;">
                If you didn't create this account, please ignore this email or contact support.<br>
                This is an automated message, please do not reply directly.
            </p>
        </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            if EMAIL_CONFIG['use_tls']:
                server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        print(f"Welcome email sent to {user_data['email']}")
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

def logout_user():
    keys = [
        'user_id', 'user_account', 'logged_in', 'show_profile_setup',
        'current_session', 'current_question', 'responses',
        'session_conversations', 'data_loaded', 'show_image_upload',
        'selected_images_for_prompt', 'image_prompt_mode',
        'show_vignette_modal', 'vignette_topic', 'vignette_content',
        'selected_vignette_type', 'current_vignette_list', 'editing_vignette_index',
        'show_vignette_manager', 'custom_topic_input', 'show_custom_topic_modal',
        'show_topic_browser', 'show_session_manager', 'show_session_creator',
        'editing_custom_session', 'show_vignette_detail', 'selected_vignette_id',
        'editing_vignette_id', 'selected_vignette_for_session', 'published_vignette',
        'show_image_gallery', 'show_publisher', 'current_export_format',
        'uploaded_images', 'image_descriptions'  # FIX: Added image storage
    ]
    for key in keys:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()

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

def update_streak():
    if "streak_days" not in st.session_state:
        st.session_state.streak_days = 1
    if "last_active" not in st.session_state:
        st.session_state.last_active = date.today().isoformat()
    if "total_writing_days" not in st.session_state:
        st.session_state.total_writing_days = 1
    today = date.today().isoformat()
    if st.session_state.last_active != today:
        try:
            last_date = date.fromisoformat(st.session_state.last_active)
            today_date = date.today()
            days_diff = (today_date - last_date).days
            if days_diff == 1:
                st.session_state.streak_days += 1
            elif days_diff > 1:
                st.session_state.streak_days = 1
            st.session_state.total_writing_days += 1
            st.session_state.last_active = today
        except:
            st.session_state.last_active = today

def get_streak_emoji(streak_days):
    if streak_days >= 30:
        return "🔥🔥🔥"
    elif streak_days >= 7:
        return "🔥🔥"
    elif streak_days >= 3:
        return "🔥"
    else:
        return "✨"

def estimate_year_from_text(text):
    try:
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        if years:
            return int(years[0])
    except:
        pass
    return None

def save_jot(text, estimated_year=None):
    if "quick_jots" not in st.session_state:
        st.session_state.quick_jots = []
    jot_data = {
        "text": text,
        "year": estimated_year,
        "date": datetime.now().isoformat(),
        "word_count": len(re.findall(r'\w+', text))
    }
    st.session_state.quick_jots.append(jot_data)
    return True

# ── Prompt Builder ────────────────────────────────────────────────────────────
def get_system_prompt():
    # Check if we have sessions loaded
    if not SESSIONS or st.session_state.current_session >= len(SESSIONS):
        return "No sessions available. Please check your CSV file."
    
    current_session = SESSIONS[st.session_state.current_session]
    current_question = (
        st.session_state.current_question_override
        or current_session["questions"][st.session_state.current_question]
    )
    historical_context = ""
    if st.session_state.user_account and st.session_state.user_account['profile'].get('birthdate'):
        try:
            birth_year = int(st.session_state.user_account['profile']['birthdate'].split(', ')[-1])
            events = get_events_for_birth_year(birth_year)
            if events:
                context_lines = []
                for event in events[:5]:
                    event_text = f"- {event['event']} ({event['year_range']})"
                    if event.get('region') == 'UK':
                        event_text += " [UK]"
                    if 'approx_age' in event and event['approx_age'] >= 0:
                        event_text += f" (Age {event['approx_age']})"
                    context_lines.append(event_text)
                historical_context = f"""
HISTORICAL CONTEXT (Born {birth_year}):
During their lifetime, these major events occurred:
{chr(10).join(context_lines)}
Consider how these historical moments might have shaped their experiences and perspectives.
"""
        except Exception as e:
            print(f"Error generating historical context: {e}")
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer with multiple award-winning books to your name.
CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"
{historical_context}
YOUR APPROACH:
1. Listen like an archivist
2. Think in scenes, sensory details, and emotional truth
3. Connect personal stories to historical context when relevant
4. Find the story that needs to be told

Tone: Literary but not pretentious. Serious but not solemn."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.
CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"
{historical_context}

Tone: Kind, curious, professional"""

# ── Core Functions ────────────────────────────────────────────────────────────
def save_response(session_id, question, answer, images=None, image_description=""):
    """FIXED: Save response with images and combine answers"""
    user_id = st.session_state.user_id
    if not user_id or user_id == "":
        return False
    
    update_streak()
    
    if st.session_state.user_account:
        word_count = len(re.findall(r'\w+', answer))
        if "stats" not in st.session_state.user_account:
            st.session_state.user_account["stats"] = {}
        st.session_state.user_account["stats"]["total_words"] = st.session_state.user_account["stats"].get("total_words", 0) + word_count
        st.session_state.user_account["stats"]["total_sessions"] = len(st.session_state.responses.get(session_id, {}).get("questions", {}))
        st.session_state.user_account["stats"]["last_active"] = datetime.now().isoformat()
        save_account_data(st.session_state.user_account)
    
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
    
    # FIX: Get existing answer
    existing_answer_data = st.session_state.responses[session_id]["questions"].get(question, {})
    existing_answer = existing_answer_data.get("answer", "")
    existing_images = existing_answer_data.get("images", [])
    existing_description = existing_answer_data.get("image_description", "")
    
    # FIX: Combine answers if there's an existing one
    if existing_answer and existing_answer.strip():
        # Clean up the existing answer
        cleaned_existing = existing_answer.strip()
        if not cleaned_existing.endswith(('.', '!', '?')):
            cleaned_existing += '.'
        
        # Clean up the new answer
        cleaned_new = answer.strip()
        
        # Combine them
        combined_answer = f"{cleaned_existing} {cleaned_new}"
    else:
        combined_answer = answer.strip()
    
    # FIX: Combine images
    all_images = list(set(existing_images + (images or [])))
    
    # FIX: Combine descriptions
    if image_description and existing_description:
        combined_description = f"{existing_description}. Also: {image_description}"
    elif image_description:
        combined_description = image_description
    else:
        combined_description = existing_description
    
    st.session_state.responses[session_id]["questions"][question] = {
        "answer": combined_answer,
        "timestamp": datetime.now().isoformat(),
        "images": all_images,  # Store all images
        "image_description": combined_description  # Store description
    }
    
    return save_user_data(user_id, st.session_state.responses)

def calculate_author_word_count(session_id):
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    return total_words

def get_progress_info(session_id):
    current_count = calculate_author_word_count(session_id)
    target = st.session_state.responses[session_id].get("word_target", DEFAULT_WORD_TARGET)
    if target == 0:
        progress_percent = 100
        emoji = "🟢"
        color = "#27ae60"
    else:
        progress_percent = (current_count / target) * 100 if target > 0 else 100
    if progress_percent >= 100:
        emoji = "🟢"
        color = "#27ae60"
    elif progress_percent >= 70:
        emoji = "🟡"
        color = "#f39c12"
    else:
        emoji = "🔴"
        color = "#e74c3c"
    remaining_words = max(0, target - current_count)
    status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"
    return {
        "current_count": current_count,
        "target": target,
        "progress_percent": progress_percent,
        "emoji": emoji,
        "color": color,
        "remaining_words": remaining_words,
        "status_text": status_text
    }
    
def auto_correct_text(text):
    if not text or not st.session_state.spellcheck_enabled:
        return text
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes in the following text. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return text

# ============================================================================
# INTEGRATED PUBLISHER
# ============================================================================
def show_publisher():
    """Show the integrated publisher"""
    st.markdown('<div style="background: white; padding: 2rem; border-radius: 10px; position: relative;">', unsafe_allow_html=True)
    
    if st.button("← Back to Writing", key="back_from_publisher"):
        st.session_state.show_publisher = False
        st.rerun()
    
    st.title("📖 Publish Your Biography")
    
    # Get stories data
    export_data = {}
    story_count = 0
    
    for session in SESSIONS:
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        if session_data.get("questions"):
            export_data[str(session_id)] = {
                "title": session["title"],
                "questions": session_data["questions"]
            }
            story_count += len(session_data["questions"])
    
    if story_count == 0:
        st.info("📝 **No stories to publish yet.** Go back and write some stories first!")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.success(f"✅ You have {story_count} stories ready to publish!")
    
    # Display user info
    user_name = st.session_state.user_id
    user_profile = st.session_state.user_account.get('profile', {}) if st.session_state.user_account else {}
    
    if user_profile and user_profile.get('first_name'):
        display_name = f"{user_profile.get('first_name')} {user_profile.get('last_name', '')}"
    else:
        display_name = user_name
    
    # Export options
    export_format = st.radio(
        "Choose format:",
        ["📚 Biography Format (Just Answers)", "🎤 Interview Format (Questions & Answers)"],
        index=0,
        horizontal=True
    )
    
    include_questions = export_format == "🎤 Interview Format (Questions & Answers)"
    
    # Create biography
    if st.button("✨ Create Biography", type="primary", use_container_width=True):
        with st.spinner("Creating your biography..."):
            # Create text version
            bio_text = "=" * 70 + "\n"
            bio_text += f"{'TELL MY STORY':^70}\n"
            bio_text += f"{'BIOGRAPHY':^70}\n"
            bio_text += "=" * 70 + "\n\n"
            
            bio_text += f"THE LIFE STORY OF\n{display_name.upper()}\n\n"
            bio_text += f"Compiled on {datetime.now().strftime('%B %d, %Y')}\n\n"
            bio_text += "=" * 70 + "\n\n"
            
            # Add stories
            chapter_num = 0
            for session_id, session_data in export_data.items():
                chapter_num += 1
                bio_text += f"CHAPTER {chapter_num}: {session_data['title'].upper()}\n"
                bio_text += "-" * 40 + "\n\n"
                
                story_num = 0
                for question, answer_data in session_data.get("questions", {}).items():
                    story_num += 1
                    answer = answer_data.get("answer", "")
                    image_description = answer_data.get("image_description", "")
                    
                    if include_questions:
                        bio_text += f"Story {story_num}: {question}\n"
                    
                    bio_text += f"{answer}\n\n"
                    
                    # FIX: Show images in published biography
                    if image_description:
                        bio_text += f"📸 Images: {image_description}\n\n"
                    
                    bio_text += "\n"
            
            # Statistics
            total_words = 0
            for session_id, session_data in export_data.items():
                for question, answer_data in session_data.get("questions", {}).items():
                    answer = answer_data.get("answer", "")
                    total_words += len(answer.split())
            
            bio_text += "=" * 70 + "\n\n"
            bio_text += "STATISTICS\n"
            bio_text += "-" * 40 + "\n"
            bio_text += f"Total Stories: {story_count}\n"
            bio_text += f"Total Chapters: {chapter_num}\n"
            bio_text += f"Total Words: {total_words}\n"
            bio_text += f"Created: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
            bio_text += "=" * 70
            
            # Show preview
            st.subheader("📖 Preview")
            with st.expander("Show preview", expanded=True):
                preview = bio_text[:1500] + "..." if len(bio_text) > 1500 else bio_text
                st.text(preview)
            
            # Download button
            safe_name = display_name.replace(" ", "_")
            file_suffix = "_Interview" if include_questions else "_Biography"
            
            st.download_button(
                label="📄 Download Biography",
                data=bio_text,
                file_name=f"{safe_name}{file_suffix}.txt",
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
            
            st.balloons()
            st.success("✅ Biography created successfully!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ── Page Config & State ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Tell My Story - Your Life Timeline",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
default_state = {
    "logged_in": False,
    "user_id": "",
    "user_account": None,
    "show_profile_setup": False,
    "current_session": 0,
    "current_question": 0,
    "responses": {},
    "session_conversations": {},
    "editing": None,
    "edit_text": "",
    "ghostwriter_mode": True,
    "spellcheck_enabled": True,
    "editing_word_target": False,
    "confirming_clear": None,
    "data_loaded": False,
    "current_question_override": None,
    "quick_jots": [],
    "historical_events_loaded": False,
    "streak_days": 1,
    "last_active": date.today().isoformat(),
    "total_writing_days": 1,
    "show_publisher": False,
    "uploaded_images": {},
    "image_descriptions": {}
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

if st.session_state.logged_in and st.session_state.user_id and not st.session_state.data_loaded:
    user_data = load_user_data(st.session_state.user_id)
    if "responses" in user_data:
        st.session_state.responses = user_data["responses"]
    st.session_state.data_loaded = True

# Show publisher if requested
if st.session_state.show_publisher:
    show_publisher()
    st.stop()

# Check if sessions are loaded
if not SESSIONS:
    st.error("❌ No sessions loaded. Please create a sessions/sessions.csv file.")
    st.stop()

# Main header
st.markdown(f"""
<div style="text-align: center; margin-bottom: 1rem;">
    <img src="{LOGO_URL}" style="height: 80px;">
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Remove Streamlit branding with CSS
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📖 Tell My Story")
    
    # Profile
    if st.session_state.user_account:
        profile = st.session_state.user_account['profile']
        st.success(f"👤 **{profile['first_name']} {profile['last_name']}**")
    
    if st.button("🚪 Log Out", use_container_width=True):
        logout_user()
    
    st.divider()
    
    # Sessions
    st.markdown("### 📚 Sessions")
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        responses_count = len(session_data.get("questions", {}))
        total_questions = len(session["questions"])
        
        # Status indicator
        if responses_count == total_questions:
            status = "🔴"
        elif responses_count > 0:
            status = "🟡"
        else:
            status = "🟢"
        
        if i == st.session_state.current_session:
            status = "▶️"
        
        button_text = f"{status} {session_id}: {session['title']}"
        
        if st.button(button_text, key=f"select_session_{i}", use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.current_question_override = None
            st.rerun()
    
    st.divider()
    
    # Publisher button
    total_answers = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    if total_answers > 0:
        if st.button("🖨️ Publish Biography", use_container_width=True, type="primary"):
            st.session_state.show_publisher = True
            st.rerun()
        st.caption(f"{total_answers} stories ready")

# ── Main Content Area ─────────────────────────────────────────────────────────
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]

if st.session_state.current_question_override:
    current_question_text = st.session_state.current_question_override
else:
    if st.session_state.current_question >= len(current_session["questions"]):
        st.session_state.current_question = 0
    current_question_text = current_session["questions"][st.session_state.current_question]

# Session header
st.markdown(f"### Session {current_session_id}: {current_session['title']}")

# Mode indicator
if st.session_state.ghostwriter_mode:
    st.success("✓ Professional mode active • With historical context")

# Question
st.markdown(f"""
<div style="background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 4px solid #3498db; margin: 1rem 0;">
    <h3 style="margin: 0;">{current_question_text}</h3>
</div>
""", unsafe_allow_html=True)

# Guidance
if current_session.get('guidance'):
    st.info(current_session['guidance'])

# FIX: Image upload section
st.markdown("---")
st.subheader("📸 Add Pictures and Descriptions")

# Initialize image storage for this session/question
session_image_key = f"images_{current_session_id}_{st.session_state.current_question}"
if session_image_key not in st.session_state.uploaded_images:
    st.session_state.uploaded_images[session_image_key] = []
if session_image_key not in st.session_state.image_descriptions:
    st.session_state.image_descriptions[session_image_key] = ""

uploaded_files = st.file_uploader(
    "Choose images for this story:",
    type=['jpg', 'jpeg', 'png', 'gif'],
    accept_multiple_files=True,
    key=f"upload_{current_session_id}_{st.session_state.current_question}"
)

# Show existing images from saved response
existing_answer_data = st.session_state.responses.get(current_session_id, {}).get("questions", {}).get(current_question_text, {})
existing_images = existing_answer_data.get("images", [])
existing_description = existing_answer_data.get("image_description", "")

if existing_images:
    st.info(f"📸 {len(existing_images)} image(s) already saved with this story")
    if existing_description:
        st.caption(f"Description: {existing_description}")

image_description = st.session_state.image_descriptions.get(session_image_key, existing_description)
new_images = []

if uploaded_files:
    st.success(f"✅ Uploaded {len(uploaded_files)} new image(s)")
    
    # Show preview of new images
    cols = st.columns(min(4, len(uploaded_files)))
    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx % 4]:
            # Read image
            image_bytes = uploaded_file.read()
            # Store for saving
            new_images.append({
                "name": uploaded_file.name,
                "size": len(image_bytes)
            })
            # Show preview
            st.image(image_bytes, caption=f"New Image {idx+1}", use_column_width=True)
    
    # Image description
    image_description = st.text_area(
        "Describe these images (this will be saved with your story):",
        value=image_description,
        placeholder="What do these images show? When were they taken? Who is in them?",
        height=100,
        key=f"desc_{current_session_id}_{st.session_state.current_question}"
    )
    
    # Store description
    st.session_state.image_descriptions[session_image_key] = image_description

st.markdown("---")

# FIX: Single big answer box with combined content
st.subheader("📝 Your Answer")

# Get existing answer for this question
existing_answer = existing_answer_data.get("answer", "")

# Big answer box - show combined answer
user_input = st.text_area(
    "Write your story here (all your previous answers are already included):",
    value=existing_answer,
    height=400,
    placeholder="Start writing your story here. Each time you save, your new text will be added to what's already here...",
    key=f"answer_{current_session_id}_{st.session_state.current_question}"
)

# Save button
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("💾 Save Answer", type="primary", use_container_width=True):
        if user_input.strip():
            # Get image names from uploaded files
            image_names = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    image_names.append(uploaded_file.name)
            
            # Also include existing images
            all_image_names = list(set(existing_images + image_names))
            
            # Save the response (automatically combines with existing)
            save_response(
                current_session_id, 
                current_question_text, 
                user_input.strip(),
                images=all_image_names,
                image_description=image_description
            )
            
            st.success("✅ Answer saved! Your new text has been added to your existing story.")
            
            # Clear upload state
            if session_image_key in st.session_state.uploaded_images:
                st.session_state.uploaded_images[session_image_key] = []
            
            st.rerun()
        else:
            st.warning("Please write something before saving!")

with col2:
    # Navigation
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.session_state.current_question > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.current_question -= 1
                st.rerun()
    with col_nav2:
        if st.session_state.current_question < len(current_session["questions"]) - 1:
            if st.button("Next →", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()

# Progress
st.markdown("---")
session_data = st.session_state.responses.get(current_session_id, {})
topics_answered = len(session_data.get("questions", {}))
total_topics = len(current_session["questions"])

if total_topics > 0:
    progress = topics_answered / total_topics
    st.progress(min(progress, 1.0))
    st.caption(f"📝 Topics explored: {topics_answered}/{total_topics} ({progress*100:.0f}%)")

# Stats
st.markdown("---")
st.markdown("### 📊 Your Statistics")
col1, col2, col3 = st.columns(3)
with col1:
    total_stories = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    st.metric("Total Stories", total_stories)
with col2:
    completed_sessions = sum(1 for s in SESSIONS if len(st.session_state.responses.get(s["id"], {}).get("questions", {})) > 0)
    st.metric("Sessions Started", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_words = 0
    for session_id, session_data in st.session_state.responses.items():
        for question, answer_data in session_data.get("questions", {}).items():
            answer = answer_data.get("answer", "")
            total_words += len(answer.split())
    st.metric("Total Words", total_words)

# Publisher section at bottom
st.markdown("---")
if total_stories > 0:
    st.success(f"✅ You have {total_stories} stories ready to publish!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📖 Create Beautiful Biography:**
        - Professional formatting
        - Includes all your images and descriptions
        - Preserve your legacy
        """)
        
        if st.button("🚀 Launch Publisher Now", type="primary", use_container_width=True):
            st.session_state.show_publisher = True
            st.rerun()
    
    with col2:
        # Quick stats
        st.metric("Total Images", sum(
            len(answer_data.get("images", [])) 
            for session in st.session_state.responses.values() 
            for answer_data in session.get("questions", {}).values()
        ))
        
        if st.session_state.ghostwriter_mode:
            st.info("✓ Professional mode")
else:
    st.info("📝 **Start by answering some questions above, then come back here to publish your biography!**")

# Footer
st.markdown("---")
st.caption(f"Tell My Story • {datetime.now().strftime('%Y-%m-%d')}")
