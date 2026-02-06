# session_manager.py - MODIFIED (NO HARDCODED SESSIONS)
import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class SessionManager:
    """Manages sessions with grid-based UI and progress tracking - LOADS FROM CSV ONLY"""
    
    def __init__(self, user_id: str, csv_path: str = "sessions/sessions.csv"):
        self.user_id = user_id
        self.csv_path = csv_path
        self.progress_file = f"user_progress/{user_id}_progress.json"
        self.custom_sessions_file = f"user_sessions/{user_id}_custom.json"
        self._ensure_directories()
        self.sessions = self._load_sessions_from_csv()  # Load sessions from CSV
        self._load_progress()
        self._load_custom_sessions()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs("user_progress", exist_ok=True)
        os.makedirs("user_sessions", exist_ok=True)
        os.makedirs("sessions", exist_ok=True)
    
    def _load_sessions_from_csv(self) -> List[Dict]:
        """Load ALL sessions from CSV file - NO HARDCODED FALLBACK"""
        try:
            if not os.path.exists(self.csv_path):
                st.error(f"❌ CSV file not found: {self.csv_path}")
                st.info("Please create a sessions/sessions.csv file with your sessions")
                return []
            
            df = pd.read_csv(self.csv_path)
            
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
                word_target = 500
                if 'word_target' in group.columns and not group.empty:
                    first_target = group.iloc[0]['word_target']
                    if pd.notna(first_target):
                        try:
                            word_target = int(float(first_target))
                        except:
                            word_target = 500
                
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
            
            st.success(f"✅ Loaded {len(sessions_list)} sessions from CSV")
            return sessions_list
            
        except Exception as e:
            st.error(f"❌ Error loading sessions from CSV: {e}")
            return []
    
    def _load_progress(self):
        """Load user progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    self.progress_data = json.load(f)
            else:
                self.progress_data = {}
        except Exception as e:
            print(f"Error loading progress: {e}")
            self.progress_data = {}
    
    def _save_progress(self):
        """Save user progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving progress: {e}")
            return False
    
    def _load_custom_sessions(self):
        """Load custom sessions created by user"""
        try:
            if os.path.exists(self.custom_sessions_file):
                with open(self.custom_sessions_file, 'r') as f:
                    self.custom_sessions = json.load(f)
            else:
                self.custom_sessions = []
        except Exception as e:
            print(f"Error loading custom sessions: {e}")
            self.custom_sessions = []
    
    def _save_custom_sessions(self):
        """Save custom sessions to file"""
        try:
            with open(self.custom_sessions_file, 'w') as f:
                json.dump(self.custom_sessions, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving custom sessions: {e}")
            return False
    
    def get_standard_sessions(self):
        """Get all standard sessions loaded from CSV"""
        return self.sessions
    
    def get_all_sessions(self):
        """Get all sessions (standard from CSV + custom)"""
        return self.sessions + self.custom_sessions
    
    def get_session_by_id(self, session_id):
        """Get a specific session by ID"""
        all_sessions = self.get_all_sessions()
        for session in all_sessions:
            if session["id"] == session_id:
                return session
        return None
    
    def refresh_sessions(self):
        """Reload sessions from CSV (useful if CSV was updated)"""
        self.sessions = self._load_sessions_from_csv()
    
    # KEEP ALL YOUR EXISTING METHODS BELOW (no changes needed)
    # get_session_progress, update_session_progress, get_session_status, etc.
    # ... (all your existing methods remain exactly the same) ...
    
    def get_session_progress(self, session_id: int) -> Dict:
        """Get progress for a specific session"""
        if str(session_id) in self.progress_data:
            return self.progress_data[str(session_id)]
        return {
            "status": "not_started",
            "started_at": None,
            "completed_at": None,
            "current_question": 0,
            "questions_answered": 0,
            "total_questions": 0,
            "word_count": 0
        }
    
    def update_session_progress(self, session_id: int, questions_answered: int, 
                               word_count: int, total_questions: int, is_completed: bool = False):
        """Update progress for a session"""
        session_key = str(session_id)
        
        if session_key not in self.progress_data:
            self.progress_data[session_key] = {
                "status": "in_progress",
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "current_question": questions_answered,
                "questions_answered": questions_answered,
                "total_questions": total_questions,
                "word_count": word_count
            }
        else:
            self.progress_data[session_key]["questions_answered"] = questions_answered
            self.progress_data[session_key]["current_question"] = questions_answered
            self.progress_data[session_key]["word_count"] = word_count
            
            if is_completed:
                self.progress_data[session_key]["status"] = "completed"
                self.progress_data[session_key]["completed_at"] = datetime.now().isoformat()
            elif questions_answered > 0:
                self.progress_data[session_key]["status"] = "in_progress"
        
        self._save_progress()
    
    def get_session_status(self, session_id: int) -> str:
        """Get the status of a session"""
        progress = self.get_session_progress(session_id)
        return progress.get("status", "not_started")
    
    def get_session_color(self, session_id: int) -> str:
        """Get the color for a session button based on status"""
        status = self.get_session_status(session_id)
        
        if status == "completed":
            return "#4CAF50"  # Green
        elif status == "in_progress":
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red
    
    def get_session_progress_percentage(self, session_id: int) -> float:
        """Get progress percentage for a session"""
        progress = self.get_session_progress(session_id)
        questions_answered = progress.get("questions_answered", 0)
        total_questions = progress.get("total_questions", 1)
        
        if total_questions > 0:
            return (questions_answered / total_questions) * 100
        return 0
    
    def create_custom_session(self, title: str, description: str = "", 
                            topics: List[str] = None, word_target: int = 500) -> Dict:
        """Create a custom session"""
        if topics is None:
            topics = []
        
        new_session = {
            "id": len(self.custom_sessions) + len(self.sessions) + 1000,
            "title": title,
            "description": description,
            "questions": topics,
            "guidance": description,
            "word_target": word_target,
            "is_custom": True,
            "created_at": datetime.now().isoformat()
        }
        
        self.custom_sessions.append(new_session)
        self._save_custom_sessions()
        return new_session
    
    def display_session_grid(self, cols: int = 3, on_session_select=None):
        """Display sessions in a grid format"""
        all_sessions = self.get_all_sessions()
        
        if not all_sessions:
            st.warning("No sessions found. Please create a sessions/sessions.csv file.")
            return
        
        # Create columns for the grid
        columns = st.columns(cols)
        
        for i, session in enumerate(all_sessions):
            col_idx = i % cols
            with columns[col_idx]:
                self._display_session_card(session, on_session_select)
    
    def _display_session_card(self, session: Dict, on_session_select=None):
        """Display a single session card"""
        session_id = session["id"]
        progress = self.get_session_progress(session_id)
        status = progress.get("status", "not_started")
        progress_pct = self.get_session_progress_percentage(session_id)
        color = self.get_session_color(session_id)
        
        # Get total questions for this session
        total_questions = len(session.get("questions", []))
        
        # Create card container
        with st.container():
            st.markdown(f"""
            <div style="
                border: 2px solid {color};
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 1rem;
                background-color: rgba(255, 255, 255, 0.05);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #333;">{session['title']}</h4>
                    <span style="
                        background-color: {color};
                        color: white;
                        padding: 0.2rem 0.5rem;
                        border-radius: 12px;
                        font-size: 0.8rem;
                    ">
                        {status.replace('_', ' ').title()}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
            # Show custom badge if custom session
            if session.get("is_custom"):
                st.markdown("""
                <div style="
                    background-color: #E3F2FD;
                    color: #1976D2;
                    padding: 0.2rem 0.5rem;
                    border-radius: 10px;
                    font-size: 0.7rem;
                    display: inline-block;
                    margin: 0.5rem 0;
                ">
                    ✨ Custom Session
                </div>
                """, unsafe_allow_html=True)
            
            # Progress info
            questions_answered = progress.get("questions_answered", 0)
            st.caption(f"📝 {questions_answered}/{total_questions} topics")
            
            # Progress bar
            if total_questions > 0:
                progress_value = questions_answered / total_questions
                st.progress(progress_value)
            
            # Word count
            st.caption(f"📖 {progress.get('word_count', 0)} words")
            
            # Action buttons
            if on_session_select:
                if st.button("Enter Session", key=f"enter_{session_id}", 
                           type="primary", use_container_width=True):
                    on_session_select(session_id)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def display_session_creator(self):
        """Display interface for creating custom sessions"""
        with st.expander("➕ Create Custom Session", expanded=False):
            with st.form("create_session_form"):
                title = st.text_input("Session Title", 
                                    placeholder="e.g., 'My College Years' or 'Career Journey'")
                description = st.text_area("Description/Guidance",
                                         placeholder="Welcome message/guidance for this session...",
                                         height=100)
                
                # Topics input
                st.write("Questions (one per line):")
                topics_text = st.text_area("",
                                         placeholder="e.g., What was your first day like?\nWho were your mentors?\nWhat challenges did you face?",
                                         height=150,
                                         label_visibility="collapsed")
                
                word_target = st.number_input("Word Target", 
                                            min_value=100, 
                                            max_value=5000, 
                                            value=500)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Create Session", type="primary", use_container_width=True):
                        if title.strip():
                            topics = [t.strip() for t in topics_text.split('\n') if t.strip()]
                            new_session = self.create_custom_session(title, description, topics, word_target)
                            st.success(f"Session '{title}' created!")
                            st.rerun()
                        else:
                            st.error("Please enter a session title")
                
                with col2:
                    if st.form_submit_button("Cancel", type="secondary", use_container_width=True):
                        st.rerun()
