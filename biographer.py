# biographer.py – Tell My Story App (Simplified Version)
import streamlit as st
import json
from datetime import datetime, date
from openai import OpenAI
import os
import re
import hashlib
import smtplib  # Fixed this line - removed the 'F'
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
import time

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from topic_bank import TopicBank
    from session_manager import SessionManager
    from vignettes import VignetteManager
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Please ensure all .py files are in the same directory")
    TopicBank = None
    SessionManager = None
    VignetteManager = None

DEFAULT_WORD_TARGET = 500

# ============================================================================
# INITIALIZATION
# ============================================================================

client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# Load external CSS
try:
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("styles.css not found – layout may look broken")

LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/02/tms_logo.png"

# ============================================================================
# SESSIONS LOADING
# ============================================================================

def load_sessions_from_csv(csv_path="sessions/sessions.csv"):
    """Load sessions ONLY from CSV file"""
    try:
        import pandas as pd
        
        os.makedirs(os.path.dirname(csv_path) if os.path.dirname(csv_path) else '.', exist_ok=True)
        
        if not os.path.exists(csv_path):
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
        
        required_columns = ['session_id', 'question']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"❌ Missing required columns in CSV: {missing_columns}")
            st.info("CSV must have at least: session_id, question")
            return []
        
        sessions_dict = {}
        
        for session_id, group in df.groupby('session_id'):
            session_id_int = int(session_id)
            group = group.reset_index(drop=True)
            
            title = f"Session {session_id_int}"
            if 'title' in group.columns and not group.empty:
                first_title = group.iloc[0]['title']
                if pd.notna(first_title) and str(first_title).strip():
                    title = str(first_title).strip()
            
            guidance = ""
            if 'guidance' in group.columns and not group.empty:
                first_guidance = group.iloc[0]['guidance']
                if pd.notna(first_guidance) and str(first_guidance).strip():
                    guidance = str(first_guidance).strip()
            
            word_target = DEFAULT_WORD_TARGET
            if 'word_target' in group.columns and not group.empty:
                first_target = group.iloc[0]['word_target']
                if pd.notna(first_target):
                    try:
                        word_target = int(float(first_target))
                    except:
                        word_target = DEFAULT_WORD_TARGET
            
            questions = []
            for _, row in group.iterrows():
                if 'question' in row and pd.notna(row['question']) and str(row['question']).strip():
                    questions.append(str(row['question']).strip())
            
            if questions:
                sessions_dict[session_id_int] = {
                    "id": session_id_int,
                    "title": title,
                    "guidance": guidance,
                    "questions": questions,
                    "completed": False,
                    "word_target": word_target
                }
        
        sessions_list = list(sessions_dict.values())
        sessions_list.sort(key=lambda x: x['id'])
        
        if not sessions_list:
            st.warning("⚠️ No sessions found in CSV file")
            return []
        
        return sessions_list
        
    except Exception as e:
        st.error(f"❌ Error loading sessions from CSV: {e}")
        return []

SESSIONS = load_sessions_from_csv()

# ============================================================================
# EMAIL CONFIG
# ============================================================================

EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
    "sender_email": st.secrets.get("SENDER_EMAIL", ""),
    "sender_password": st.secrets.get("SENDER_PASSWORD", ""),
    "use_tls": True
}

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

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
        msg['Subject'] = "Welcome to Tell My Story"
        
        body = f"""
        <html>
        <body style="font-family: Arial; line-height: 1.6;">
        <h2>Welcome to Tell My Story, {user_data['first_name']}!</h2>
        <p>Thank you for creating your account.</p>
        <div style="background: #f0f8ff; padding: 15px; margin: 15px 0; border-left: 4px solid #3498db;">
            <h3>Your Account Details:</h3>
            <p><strong>Account ID:</strong> {credentials['user_id']}</p>
            <p><strong>Email:</strong> {user_data['email']}</p>
            <p><strong>Password:</strong> {credentials['password']}</p>
        </div>
        <p>Start building your timeline from your birthdate: {user_data.get('birthdate', 'Not specified')}</p>
        <p>If you didn't create this account, please ignore this email.</p>
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
        'session_conversations', 'data_loaded', 'show_vignette_modal',
        'vignette_topic', 'vignette_content', 'selected_vignette_type',
        'current_vignette_list', 'editing_vignette_index', 'show_vignette_manager',
        'custom_topic_input', 'show_custom_topic_modal', 'show_topic_browser',
        'show_session_manager', 'show_session_creator', 'editing_custom_session',
        'show_vignette_detail', 'selected_vignette_id', 'editing_vignette_id',
        'selected_vignette_for_session', 'published_vignette'
    ]
    for key in keys:
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.rerun()

# ============================================================================
# STORAGE FUNCTIONS
# ============================================================================

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

# ============================================================================
# CORE RESPONSE FUNCTIONS
# ============================================================================

def save_response(session_id, question, answer):
    user_id = st.session_state.user_id
    if not user_id or user_id == "":
        return False
    
    formatted_answer = answer
    
    if st.session_state.user_account:
        word_count = len(re.findall(r'\w+', formatted_answer))
        if "stats" not in st.session_state.user_account:
            st.session_state.user_account["stats"] = {}
        st.session_state.user_account["stats"]["total_words"] = st.session_state.user_account["stats"].get("total_words", 0) + word_count
        
        total_answers = 0
        for sid, session_data in st.session_state.responses.items():
            total_answers += len(session_data.get("questions", {}))
        
        st.session_state.user_account["stats"]["total_sessions"] = total_answers
        st.session_state.user_account["stats"]["last_active"] = datetime.now().isoformat()
        save_account_data(st.session_state.user_account)
    
    if session_id not in st.session_state.responses:
        session_data = None
        for s in SESSIONS:
            if s["id"] == session_id:
                session_data = s
                break
        
        if not session_data:
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
    
    st.session_state.responses[session_id]["questions"][question] = {
        "answer": formatted_answer,
        "question": question,
        "timestamp": datetime.now().isoformat(),
        "answer_index": 1
    }
    
    success = save_user_data(user_id, st.session_state.responses)
    
    if success:
        st.session_state.data_loaded = False
        
    return success

def delete_response(session_id, question):
    user_id = st.session_state.user_id
    if not user_id or user_id == "":
        return False
    
    if session_id in st.session_state.responses:
        if question in st.session_state.responses[session_id]["questions"]:
            del st.session_state.responses[session_id]["questions"][question]
            success = save_user_data(user_id, st.session_state.responses)
            if success:
                st.session_state.data_loaded = False
            return success
    
    return False

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
    if not text:
        return text
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return text

# ============================================================================
# BETA READER FUNCTIONS
# ============================================================================

def get_session_full_text(session_id):
    """Get all responses from a session as continuous text for beta reading"""
    if session_id not in st.session_state.responses:
        return ""
    
    session_text = ""
    session_data = st.session_state.responses[session_id]
    
    if "questions" in session_data:
        for question, answer_data in session_data["questions"].items():
            session_text += f"Q: {question}\nA: {answer_data['answer']}\n\n"
    
    return session_text

def generate_beta_reader_feedback(session_title, session_text, feedback_type="comprehensive"):
    """Generate beta reader/editor feedback for a completed session"""
    if not session_text.strip():
        return {"error": "Session has no content to analyze"}
    
    critique_templates = {
        "comprehensive": """You are a professional editor and beta reader. Analyze this life story excerpt and provide:
        1. **Overall Impression** (2-3 sentences)
        2. **Strengths** (3-5 bullet points)
        3. **Areas for Improvement** (3-5 bullet points with specific suggestions)
        4. **Continuity Check** (Note any timeline inconsistencies)
        5. **Emotional Resonance** (How engaging/emotional is it?)
        6. **Specific Edits** (3-5 suggested rewrites with explanations)
        
        Format your response clearly with headings and bullet points.""",
        
        "concise": """You are an experienced beta reader. Provide brief, actionable feedback on:
        - Main strengths
        - 2-3 specific areas to improve
        - 1-2 specific editing suggestions
        
        Keep it under 300 words.""",
        
        "developmental": """You are a developmental editor. Focus on:
        - Narrative structure and flow
        - Character/personality development
        - Pacing and detail balance
        - Theme consistency
        - Suggested structural changes"""
    }
    
    prompt = critique_templates.get(feedback_type, critique_templates["comprehensive"])
    
    full_prompt = f"""{prompt}

    SESSION TITLE: {session_title}
    
    SESSION CONTENT:
    {session_text}
    
    Please provide your analysis:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a thoughtful, constructive editor who balances praise with helpful critique."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        feedback = response.choices[0].message.content
        
        return {
            "session_title": session_title,
            "feedback": feedback,
            "generated_at": datetime.now().isoformat(),
            "feedback_type": feedback_type
        }
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def save_beta_feedback(user_id, session_id, feedback_data):
    """Save beta feedback to user's data file"""
    try:
        filename = get_user_filename(user_id)
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                user_data = json.load(f)
        else:
            user_data = {"responses": {}, "vignettes": [], "beta_feedback": {}}
        
        if "beta_feedback" not in user_data:
            user_data["beta_feedback"] = {}
        
        user_data["beta_feedback"][str(session_id)] = feedback_data
        
        with open(filename, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving beta feedback: {e}")
        return False

def get_previous_beta_feedback(user_id, session_id):
    """Retrieve previous beta feedback for a session"""
    try:
        filename = get_user_filename(user_id)
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                user_data = json.load(f)
            
            if "beta_feedback" in user_data and str(session_id) in user_data["beta_feedback"]:
                return user_data["beta_feedback"][str(session_id)]
    except:
        pass
    return None

def show_beta_reader_modal():
    """Display the beta reader feedback modal"""
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    feedback = st.session_state.current_beta_feedback
    
    if st.button("← Back to Writing", key="beta_reader_back"):
        st.session_state.show_beta_reader = False
        st.rerun()
    
    st.title(f"🦋 Beta Reader: {feedback.get('session_title', 'Session')}")
    st.caption(f"Generated: {datetime.fromisoformat(feedback['generated_at']).strftime('%B %d, %Y at %I:%M %p')}")
    
    st.divider()
    
    # Full feedback
    st.subheader("📝 Editor's Analysis")
    st.markdown(feedback["feedback"])
    
    # Action buttons
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Regenerate Feedback", use_container_width=True):
            st.session_state.show_beta_reader = False
            st.rerun()
    
    with col2:
        if st.button("💾 Save to Profile", use_container_width=True, type="primary"):
            if save_beta_feedback(st.session_state.user_id, current_session["id"], feedback):
                st.success("Feedback saved!")
                time.sleep(1)
                st.session_state.show_beta_reader = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MODULE INTEGRATION FUNCTIONS
# ============================================================================

def switch_to_vignette(vignette_topic, content=""):
    st.session_state.current_question_override = f"Vignette: {vignette_topic}"
    if content:
        current_session = SESSIONS[st.session_state.current_session]
        current_session_id = current_session["id"]
        save_response(current_session_id, f"Vignette: {vignette_topic}", content)
    st.rerun()

def switch_to_custom_topic(topic_text):
    st.session_state.current_question_override = topic_text
    st.rerun()

def show_vignette_modal():
    if not VignetteManager:
        st.error("Vignette module not available")
        st.session_state.show_vignette_modal = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="vignette_modal_back"):
        st.session_state.show_vignette_modal = False
        if 'editing_vignette_id' in st.session_state:
            st.session_state.pop('editing_vignette_id')
        st.rerun()
    
    vignette_manager = VignetteManager(st.session_state.user_id)
    
    if 'published_vignette' not in st.session_state:
        st.session_state.published_vignette = None
    
    def on_publish(vignette):
        st.session_state.published_vignette = vignette
        st.success(f"Vignette '{vignette['title']}' published!")
        st.rerun()
    
    vignette_manager.display_vignette_creator(on_publish=on_publish)
    
    if st.session_state.published_vignette:
        vignette = st.session_state.published_vignette
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📚 Add to Session", key="add_to_session_after", use_container_width=True):
                st.session_state.selected_vignette_for_session = vignette
                st.session_state.show_vignette_modal = False
                st.session_state.published_vignette = None
                st.rerun()
        
        with col2:
            if st.button("📖 View All Vignettes", key="view_all_after", use_container_width=True):
                st.session_state.show_vignette_modal = False
                st.session_state.show_vignette_manager = True
                st.session_state.published_vignette = None
                st.rerun()
        
        with col3:
            if st.button("✏️ Keep Writing", key="keep_writing", use_container_width=True):
                st.session_state.show_vignette_modal = False
                st.session_state.published_vignette = None
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_vignette_manager():
    if not VignetteManager:
        st.error("Vignette module not available")
        st.session_state.show_vignette_manager = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="vignette_manager_back"):
        st.session_state.show_vignette_manager = False
        st.rerun()
    
    st.title("📚 Your Vignettes")
    
    vignette_manager = VignetteManager(st.session_state.user_id)
    
    filter_option = st.radio(
        "Show:",
        ["All Stories", "Published", "Drafts", "Most Popular"],
        horizontal=True,
        key="vignette_filter"
    )
    
    def on_vignette_select(vignette_id):
        st.session_state.show_vignette_detail = True
        st.session_state.selected_vignette_id = vignette_id
        st.rerun()
    
    filter_map = {
        "All Stories": "all",
        "Published": "published",
        "Drafts": "drafts",
        "Most Popular": "popular"
    }
    
    vignette_manager.display_vignette_gallery(
        filter_by=filter_map.get(filter_option, "all"),
        on_select=on_vignette_select
    )
    
    st.divider()
    if st.button("➕ Create New Vignette", type="primary", use_container_width=True):
        st.session_state.show_vignette_manager = False
        st.session_state.show_vignette_modal = True
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_vignette_detail():
    if not VignetteManager or not st.session_state.get('selected_vignette_id'):
        st.session_state.show_vignette_detail = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="vignette_detail_back"):
        st.session_state.show_vignette_detail = False
        st.rerun()
    
    vignette_manager = VignetteManager(st.session_state.user_id)
    vignette = vignette_manager.get_vignette_by_id(st.session_state.selected_vignette_id)
    
    if not vignette:
        st.error("Vignette not found")
        st.session_state.show_vignette_detail = False
        return
    
    st.title(vignette['title'])
    st.caption(f"Theme: {vignette.get('theme', 'Uncategorized')}")
    
    if vignette.get('tags'):
        tags = " ".join([f"`{tag}`" for tag in vignette.get('tags', [])])
        st.caption(f"Tags: {tags}")
    
    st.divider()
    st.write(vignette['content'])
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Words", vignette.get('word_count', 0))
    with col2:
        st.metric("Views", vignette.get('views', 0))
    with col3:
        st.metric("Likes", vignette.get('likes', 0))
    with col4:
        if vignette.get('is_draft'):
            if st.button("🚀 Publish", use_container_width=True, type="primary"):
                if vignette_manager.publish_vignette(vignette['id']):
                    st.success("Published!")
                    st.rerun()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📚 Add to Session", type="primary", use_container_width=True):
            st.session_state.selected_vignette_for_session = vignette
            st.session_state.show_vignette_detail = False
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit", use_container_width=True):
            st.session_state.editing_vignette_id = vignette['id']
            st.session_state.show_vignette_detail = False
            st.session_state.show_vignette_modal = True
            st.rerun()
    
    with col3:
        if st.button("🗑️ Delete", type="secondary", use_container_width=True):
            st.warning("Delete functionality to be implemented")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_topic_browser():
    if not TopicBank:
        st.error("Topic module not available")
        st.session_state.show_topic_browser = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="topic_browser_back"):
        st.session_state.show_topic_browser = False
        st.rerun()
    
    st.title("📚 Topic Browser")
    
    topic_bank = TopicBank(st.session_state.user_id)
    
    def on_topic_select(topic_text):
        switch_to_custom_topic(topic_text)
        st.session_state.show_topic_browser = False
    
    import time
    topic_bank.display_topic_browser(on_topic_select=on_topic_select, unique_key=str(time.time()))
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_session_creator():
    if not SessionManager:
        st.error("Session module not available")
        st.session_state.show_session_creator = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="session_creator_back"):
        st.session_state.show_session_creator = False
        st.rerun()
    
    st.title("📋 Create Custom Session")
    
    session_manager = SessionManager(st.session_state.user_id, "sessions/sessions.csv")
    session_manager.display_session_creator()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_session_manager():
    if not SessionManager:
        st.error("Session module not available")
        st.session_state.show_session_manager = False
        return
    
    st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
    
    if st.button("← Back", key="session_manager_back"):
        st.session_state.show_session_manager = False
        st.rerun()
    
    st.title("📖 Session Manager")
    
    session_manager = SessionManager(st.session_state.user_id, "sessions/sessions.csv")
    
    def on_session_select(session_id):
        all_sessions = session_manager.get_all_sessions()
        for i, session in enumerate(all_sessions):
            if session["id"] == session_id:
                for j, standard_session in enumerate(SESSIONS):
                    if standard_session["id"] == session_id:
                        st.session_state.current_session = j
                        break
                else:
                    custom_sessions = all_sessions[len(SESSIONS):]
                    if session in custom_sessions:
                        custom_index = custom_sessions.index(session)
                        st.session_state.current_session = len(SESSIONS) + custom_index
                
                st.session_state.current_question = 0
                st.session_state.current_question_override = None
                st.rerun()
                break
    
    if st.button("➕ Create New Session", type="primary", use_container_width=True):
        st.session_state.show_session_manager = False
        st.session_state.show_session_creator = True
        st.rerun()
    
    st.divider()
    
    session_manager.display_session_grid(cols=2, on_session_select=on_session_select)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# PAGE CONFIG & STATE INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="Tell My Story - Your Life Timeline",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

default_state = {
    "logged_in": False,
    "user_id": "",
    "user_account": None,
    "show_profile_setup": False,
    "current_session": 0,
    "current_question": 0,
    "responses": {},
    "editing": False,
    "editing_word_target": False,
    "confirming_clear": None,
    "data_loaded": False,
    "current_question_override": None,
    "show_vignette_modal": False,
    "vignette_topic": "",
    "vignette_content": "",
    "selected_vignette_type": "Standard Topic",
    "current_vignette_list": [],
    "editing_vignette_index": None,
    "show_vignette_manager": False,
    "custom_topic_input": "",
    "show_custom_topic_modal": False,
    "show_topic_browser": False,
    "show_session_manager": False,
    "show_session_creator": False,
    "editing_custom_session": None,
    "show_vignette_detail": False,
    "selected_vignette_id": None,
    "editing_vignette_id": None,
    "selected_vignette_for_session": None,
    "published_vignette": None,
    "show_beta_reader": False,  # NEW: Beta reader modal state
    "current_beta_feedback": None,  # NEW: Store current feedback
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

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
        for session_id_str, session_data in user_data["responses"].items():
            try:
                session_id = int(session_id_str)
                if session_id in st.session_state.responses:
                    if "questions" in session_data:
                        if session_data["questions"]:
                            st.session_state.responses[session_id]["questions"] = session_data["questions"]
            except ValueError:
                continue
    st.session_state.data_loaded = True

# ============================================================================
# SESSIONS CHECK
# ============================================================================

if not SESSIONS:
    st.error("❌ No sessions loaded. Please create a sessions/sessions.csv file.")
    st.info("""
    Create a CSV file with this format:
    
    session_id,title,guidance,question,word_target
    1,Childhood,"Welcome to Session 1...","What is your earliest memory?",500
    1,Childhood,,"Can you describe your family home?",500
    2,Family,"Welcome to Session 2...","How would you describe your relationship?",500
    
    Save it as: sessions/sessions.csv
    """)
    st.stop()

# ============================================================================
# PROFILE SETUP MODAL
# ============================================================================

if st.session_state.get('show_profile_setup', False):
    st.markdown('<div class="profile-setup-modal">', unsafe_allow_html=True)
    st.title("👤 Complete Your Profile")
    st.write("Please complete your profile to start building your timeline:")
    with st.form("profile_setup_form"):
        st.write("**Gender**")
        gender = st.radio(
            "Gender",
            ["Male", "Female", "Other", "Prefer not to say"],
            horizontal=True,
            key="modal_gender",
            label_visibility="collapsed"
        )
        st.write("**Birthdate**")
        col1, col2, col3 = st.columns(3)
        with col1:
            months = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            birth_month = st.selectbox("Month", months, key="modal_month", label_visibility="collapsed")
        with col2:
            days = list(range(1, 32))
            birth_day = st.selectbox("Day", days, key="modal_day", label_visibility="collapsed")
        with col3:
            current_year = datetime.now().year
            years = list(range(current_year, current_year - 120, -1))
            birth_year = st.selectbox("Year", years, key="modal_year", label_visibility="collapsed")
        st.write("**Is this account for you or someone else?**")
        account_for = st.radio(
            "Account Type",
            ["For me", "For someone else"],
            key="modal_account_type",
            horizontal=True,
            label_visibility="collapsed"
        )
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Complete Profile", type="primary", use_container_width=True)
        with col2:
            skip_button = st.form_submit_button("Skip for Now", type="secondary", use_container_width=True)
        
        if submit_button:
            if not birth_month or not birth_day or not birth_year:
                st.error("Please complete your birthdate or click 'Skip for Now'")
            else:
                birthdate = f"{birth_month} {birth_day}, {birth_year}"
                account_for_value = "self" if account_for == "For me" else "other"
                if st.session_state.user_account:
                    st.session_state.user_account['profile']['gender'] = gender
                    st.session_state.user_account['profile']['birthdate'] = birthdate
                    st.session_state.user_account['profile']['timeline_start'] = birthdate
                    st.session_state.user_account['account_type'] = account_for_value
                    save_account_data(st.session_state.user_account)
                    st.success("Profile updated!")
                st.session_state.show_profile_setup = False
                st.rerun()
        
        if skip_button:
            if st.session_state.user_account:
                st.session_state.user_account['profile']['gender'] = ""
                st.session_state.user_account['profile']['birthdate'] = ""
                st.session_state.user_account['profile']['timeline_start'] = ""
                st.session_state.user_account['account_type'] = "self"
                save_account_data(st.session_state.user_account)
            st.session_state.show_profile_setup = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# AUTHENTICATION COMPONENTS
# ============================================================================

if not st.session_state.logged_in:
    st.markdown("""
    <div class="auth-container">
    <h1 class="auth-title">Tell My Story</h1>
    <p class="auth-subtitle">Your Life Timeline • Preserve Your Legacy</p>
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
        with st.form("login_form"):
            st.subheader("Welcome Back")
            email = st.text_input("Email Address", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            col1, col2 = st.columns([2, 1])
            with col1:
                remember_me = st.checkbox("Remember me", value=True)
            with col2:
                st.markdown('<div class="forgot-password"><a href="#">Forgot password?</a></div>', unsafe_allow_html=True)
            login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
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
                            if remember_me:
                                st.query_params['user'] = result['user_id']
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(f"Login failed: {result.get('error', 'Unknown error')}")
    else:
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
            accept_terms = st.checkbox("I agree to the Terms*", key="signup_terms")
            signup_button = st.form_submit_button("Create Account", type="primary", use_container_width=True)
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
                if not accept_terms:
                    errors.append("You must accept the terms")
                if email and "@" in email:
                    existing_account = get_account_data(email=email)
                    if existing_account:
                        errors.append("An account with this email already exists")
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    user_data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "account_for": "self"
                    }
                    with st.spinner("Creating your account..."):
                        result = create_user_account(user_data, password)
                        if result["success"]:
                            email_sent = send_welcome_email(user_data, {
                                "user_id": result["user_id"],
                                "password": password
                            })
                            st.session_state.user_id = result["user_id"]
                            st.session_state.user_account = result["user_record"]
                            st.session_state.logged_in = True
                            st.session_state.data_loaded = False
                            st.session_state.show_profile_setup = True
                            st.success("Account created!")
                            if email_sent:
                                st.info(f"Welcome email sent to {email}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"Error: {result.get('error', 'Unknown error')}")
    st.stop()

# ============================================================================
# MODAL HANDLING (PRIORITY ORDER)
# ============================================================================

# NEW: Beta Reader Modal (added to priority order)
if st.session_state.show_beta_reader and st.session_state.current_beta_feedback:
    show_beta_reader_modal()
    st.stop()

if st.session_state.show_vignette_detail:
    show_vignette_detail()
    st.stop()

if st.session_state.show_vignette_manager:
    show_vignette_manager()
    st.stop()

if st.session_state.show_vignette_modal:
    show_vignette_modal()
    st.stop()

if st.session_state.show_topic_browser:
    show_topic_browser()
    st.stop()

if st.session_state.show_session_manager:
    show_session_manager()
    st.stop()

if st.session_state.show_session_creator:
    show_session_creator()
    st.stop()

# ============================================================================
# MAIN HEADER
# ============================================================================

st.markdown(f"""
<div class="main-header">
<img src="{LOGO_URL}" class="logo-img" alt="Tell My Story Logo">
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem; border-bottom: 2px solid #b5f5ec;">
        <h2 style="color: #0066cc; margin: 0;">Tell My Story</h2>
        <p style="color: #36cfc9; font-size: 0.9rem; margin: 0.25rem 0 0 0;">Your Life Timeline</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("👤 Your Profile")
    if st.session_state.user_account:
        profile = st.session_state.user_account['profile']
        st.success(f"✓ **{profile['first_name']} {profile['last_name']}**")
    
    if st.button("📝 Edit Profile", use_container_width=True):
        st.session_state.show_profile_setup = True
        st.rerun()
    
    if st.button("🚪 Log Out", use_container_width=True):
        logout_user()
    
    st.divider()
    
    st.header("📖 Sessions")
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        responses_count = len(session_data.get("questions", {}))
        total_questions = len(session["questions"])
        
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
            st.session_state.editing = False
            st.session_state.current_question_override = None
            st.rerun()
    
    st.divider()
    
    st.header("✨ Vignettes")
    if st.button("📝 New Vignette", use_container_width=True):
        st.session_state.show_vignette_modal = True
        st.rerun()
    
    if st.button("📖 View All", use_container_width=True):
        st.session_state.show_vignette_manager = True
        st.rerun()
    
    st.divider()
    
    st.header("📖 Session Management")
    if st.button("📋 All Sessions", use_container_width=True):
        st.session_state.show_session_manager = True
        st.rerun()
    
    if st.button("➕ Custom Session", use_container_width=True):
        st.session_state.show_session_creator = True
        st.rerun()
    
    st.divider()
    
    st.subheader("📤 Export Options")
    
    total_answers = 0
    for session_id, session_data in st.session_state.responses.items():
        total_answers += len(session_data.get("questions", {}))
    st.caption(f"Total answers: {total_answers}")
    
    if st.session_state.logged_in and st.session_state.user_id:
        export_data = []
        
        for session in SESSIONS:
            session_id = session["id"]
            session_data = st.session_state.responses.get(session_id, {})
            if session_data.get("questions"):
                for question_text, answer_data in session_data["questions"].items():
                    export_data.append({
                        "question": question_text,
                        "answer": answer_data["answer"],
                        "timestamp": answer_data["timestamp"],
                        "answer_index": 1,
                        "session_id": session_id,
                        "session_title": session["title"]
                    })
        
        if export_data:
            complete_data = {
                "user": st.session_state.user_id,
                "user_profile": st.session_state.user_account.get('profile', {}) if st.session_state.user_account else {},
                "stories": export_data,
                "export_date": datetime.now().isoformat(),
                "summary": {
                    "total_stories": len(export_data),
                    "total_sessions": len(set(s['session_id'] for s in export_data))
                }
            }
            
            json_data = json.dumps(complete_data, indent=2)
            
            stories_only = {
                "user": st.session_state.user_id,
                "stories": export_data,
                "export_date": datetime.now().isoformat()
            }
            stories_json = json.dumps(stories_only, indent=2)
            
            if st.download_button(
                label="📥 Stories Only",
                data=stories_json,
                file_name=f"Tell_My_Story_Stories_{st.session_state.user_id}.json",
                mime="application/json",
                use_container_width=True,
                key="download_stories_btn"
            ):
                pass
            
            if st.download_button(
                label="📊 Complete Data",
                data=json_data,
                file_name=f"Tell_My_Story_Complete_{st.session_state.user_id}.json",
                mime="application/json",
                use_container_width=True,
                key="download_complete_btn"
            ):
                pass
        else:
            st.warning("No data to export yet!")
    else:
        st.warning("Please log in to export your data.")
    
    st.divider()
    
    st.subheader("⚠️ Clear Data")
    st.caption("**WARNING: This action cannot be undone!**")
    
    if st.session_state.confirming_clear == "session":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: Delete ALL answers in current session?**")
        
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
            
        st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.confirming_clear == "all":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: Delete ALL answers for ALL sessions?**")
        
        if st.button("✅ Confirm Delete All", type="primary", use_container_width=True, key="confirm_delete_all"):
            try:
                for session in SESSIONS:
                    session_id = session["id"]
                    st.session_state.responses[session_id]["questions"] = {}
                save_user_data(st.session_state.user_id, st.session_state.responses)
                st.session_state.confirming_clear = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_delete_all"):
            st.session_state.confirming_clear = None
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        if st.button("🗑️ Clear Session", type="secondary", use_container_width=True, key="clear_session_btn"):
            st.session_state.confirming_clear = "session"
            st.rerun()
        
        if st.button("🔥 Clear All", type="secondary", use_container_width=True, key="clear_all_btn"):
            st.session_state.confirming_clear = "all"
            st.rerun()

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

if st.session_state.current_session >= len(SESSIONS):
    st.session_state.current_session = 0

current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]

if st.session_state.current_question_override:
    current_question_text = st.session_state.current_question_override
    question_source = "custom"
else:
    if st.session_state.current_question >= len(current_session["questions"]):
        st.session_state.current_question = 0
    current_question_text = current_session["questions"][st.session_state.current_question]
    question_source = "regular"

st.markdown("---")

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    session_data = st.session_state.responses.get(current_session_id, {})
    topics_answered = len(session_data.get("questions", {}))
    total_topics = len(current_session["questions"])
    
    if total_topics > 0:
        topic_progress = topics_answered / total_topics
        st.progress(min(topic_progress, 1.0))
        st.caption(f"📝 Topics explored: {topics_answered}/{total_topics} ({topic_progress*100:.0f}%)")

with col2:
    if question_source == "custom":
        if st.session_state.current_question_override.startswith("Vignette:"):
            st.markdown(f'<div class="question-counter" style="margin-top: 1rem; color: #9b59b6;">📝 Vignette</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="question-counter" style="margin-top: 1rem; color: #ff6b00;">✨ Custom Topic</div>', unsafe_allow_html=True)
    else:
        current_topic = st.session_state.current_question + 1
        total_topics = len(current_session["questions"])
        st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Topic {current_topic} of {total_topics}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="question-box">
{current_question_text}
</div>
""", unsafe_allow_html=True)

if question_source == "regular":
    st.markdown(f"""
    <div class="chapter-guidance">
    {current_session.get('guidance', '')}
    </div>
    """, unsafe_allow_html=True)
else:
    if st.session_state.current_question_override.startswith("Vignette:"):
        st.info("📝 **Vignette Mode** - Write a short, focused story about a specific moment or memory.")
    else:
        st.info("✨ **Custom Topic** - Write about whatever comes to mind!")

st.write("")
st.write("")

existing_answer = ""
if current_session_id in st.session_state.responses:
    if current_question_text in st.session_state.responses[current_session_id]["questions"]:
        existing_answer = st.session_state.responses[current_session_id]["questions"][current_question_text]["answer"]

user_input = st.text_area(
    "Type your answer here...",
    value=existing_answer,
    key=f"answer_box_{current_session_id}_{hash(current_question_text)}",
    height=600,
    placeholder="Write your detailed response here...",
    label_visibility="visible"
)

st.write("")
st.write("")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("💾 Save", key="save_answer", type="primary", use_container_width=True):
        if user_input:
            saving_placeholder = st.empty()
            saving_placeholder.info("Saving...")
            corrected_text = auto_correct_text(user_input)
            if save_response(current_session_id, current_question_text, corrected_text):
                saving_placeholder.success("Answer saved!")
                time.sleep(0.5)
                st.rerun()
            else:
                saving_placeholder.error("Failed to save")
        else:
            st.warning("Please write something before saving!")

with col2:
    if existing_answer:
        if st.button("🗑️ Delete", key="delete_answer", type="secondary", use_container_width=True):
            if delete_response(current_session_id, current_question_text):
                st.success("Answer deleted!")
                st.rerun()
    else:
        st.button("🗑️ Delete", key="delete_disabled", disabled=True, use_container_width=True)

with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        prev_disabled = st.session_state.current_question == 0
        if st.button("← Previous Topic", 
                    disabled=prev_disabled,
                    key="bottom_prev_btn",
                    use_container_width=True):
            if not prev_disabled:
                st.session_state.current_question -= 1
                st.session_state.editing = False
                st.session_state.current_question_override = None
                st.rerun()
    
    with nav_col2:
        next_disabled = st.session_state.current_question >= len(current_session["questions"]) - 1
        if st.button("Next Topic →", 
                    disabled=next_disabled,
                    key="bottom_next_btn",
                    use_container_width=True):
            if not next_disabled:
                st.session_state.current_question += 1
                st.session_state.editing = False
                st.session_state.current_question_override = None
                st.rerun()

st.divider()

# ============================================================================
# BETA READER SECTION (NEW)
# ============================================================================

st.subheader("🦋 Beta Reader Feedback")

# Check if session is complete
session_data = st.session_state.responses.get(current_session_id, {})
responses_count = len(session_data.get("questions", {}))
total_questions = len(current_session["questions"])

if responses_count == total_questions and total_questions > 0:
    st.success("✅ Session complete - ready for beta reading!")
    
    # Check for previous feedback
    previous_feedback = get_previous_beta_feedback(st.session_state.user_id, current_session_id)
    
    if previous_feedback:
        st.info(f"📖 Previous feedback available from {datetime.fromisoformat(previous_feedback['generated_at']).strftime('%B %d')}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        feedback_type = st.selectbox(
            "Feedback Type",
            ["comprehensive", "concise", "developmental"],
            key="beta_reader_type",
            help="Comprehensive: Detailed analysis | Concise: Quick feedback | Developmental: Structural focus"
        )
    
    with col2:
        if st.button("🦋 Get Beta Reader Feedback", use_container_width=True, type="primary"):
            with st.spinner("Analyzing your session with professional editor eyes..."):
                # Get all session text
                session_text = get_session_full_text(current_session_id)
                
                if not session_text.strip():
                    st.error("Session has no content to analyze")
                else:
                    # Generate feedback
                    feedback = generate_beta_reader_feedback(
                        current_session["title"], 
                        session_text, 
                        feedback_type
                    )
                    
                    if "error" not in feedback:
                        st.session_state.current_beta_feedback = feedback
                        st.session_state.show_beta_reader = True
                        st.rerun()
                    else:
                        st.error(f"Failed to generate feedback: {feedback['error']}")
    
    # Show previous feedback button
    if previous_feedback:
        if st.button("📖 View Previous Feedback", use_container_width=True):
            st.session_state.current_beta_feedback = previous_feedback
            st.session_state.show_beta_reader = True
            st.rerun()
else:
    st.info(f"Complete all {total_questions} topics in this session to get beta reader feedback.")

st.divider()

# ============================================================================
# SESSION PROGRESS (Original continues here)
# ============================================================================

progress_info = get_progress_info(current_session_id)
st.markdown(f"""
<div class="progress-container">
<div class="progress-header">📊 Session Progress</div>
<div class="progress-status">{progress_info['emoji']} {progress_info['progress_percent']:.0f}% complete • {progress_info['remaining_words']} words remaining</div>
<div class="progress-bar-container">
<div class="progress-bar-fill" style="width: {min(progress_info['progress_percent'], 100)}%; background-color: {progress_info['color']};"></div>
</div>
<div style="text-align: center; font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
{progress_info['current_count']} / {progress_info['target']} words
</div>
</div>
""", unsafe_allow_html=True)

if st.button("✏️ Change Word Target", key="edit_word_target_bottom", use_container_width=True):
    st.session_state.editing_word_target = not st.session_state.editing_word_target
    st.rerun()

if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    st.write("**Change Word Target**")
    new_target = st.number_input(
        "Target words for this session:",
        min_value=100,
        max_value=5000,
        value=progress_info['target'],
        key="target_edit_input_bottom",
        label_visibility="collapsed"
    )
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Save", key="save_word_target_bottom", type="primary", use_container_width=True):
            st.session_state.responses[current_session_id]["word_target"] = new_target
            save_user_data(st.session_state.user_id, st.session_state.responses)
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", key="cancel_word_target_bottom", use_container_width=True):
            st.session_state.editing_word_target = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_words_all_sessions = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    st.metric("Total Words", f"{total_words_all_sessions}")
with col2:
    unique_questions_all = set()
    for session in SESSIONS:
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        for question_text, answer_data in session_data.get("questions", {}).items():
            unique_questions_all.add((session_id, question_text))
    
    completed_sessions = sum(1 for s in SESSIONS if len([q for (sid, q) in unique_questions_all if sid == s["id"]]) == len(s["questions"]))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_topics_answered = len(unique_questions_all)
    total_all_topics = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Topics Explored", f"{total_topics_answered}/{total_all_topics}")
with col4:
    total_answers_all = 0
    for session in SESSIONS:
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        total_answers_all += len(session_data.get("questions", {}))
    st.metric("Total Answers", f"{total_answers_all}")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
if st.session_state.user_account:
    profile = st.session_state.user_account['profile']
    account_age = (datetime.now() - datetime.fromisoformat(st.session_state.user_account['created_at'])).days
    
    footer_info = f"""
Tell My Story Timeline • 👤 {profile['first_name']} {profile['last_name']} • 📅 Account Age: {account_age} days
"""
    st.caption(footer_info)
else:
    st.caption(f"Tell My Story Timeline • User: {st.session_state.user_id}")



