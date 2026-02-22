# question_bank_manager.py - PRODUCTION VERSION WITH ALL FIXES
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import uuid
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class QuestionBankManager:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.base_path = Path("question_banks")
        self.default_banks_path = self.base_path / "default"
        self.user_banks_path = self.base_path / "users"
        
        # Create directories with error handling
        try:
            self.default_banks_path.mkdir(parents=True, exist_ok=True)
            self.user_banks_path.mkdir(parents=True, exist_ok=True)
            if self.user_id:
                (self.user_banks_path / self.user_id).mkdir(parents=True, exist_ok=True)
            logger.info(f"QuestionBankManager initialized for user: {user_id}")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            st.error(f"System error: Could not create required directories")
    
    def load_sessions_from_csv(self, csv_path):
        """Load sessions from a CSV file with error handling"""
        try:
            csv_path = Path(csv_path)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_path}")
                return []
            
            df = pd.read_csv(csv_path)
            sessions = []
            
            # Validate required columns
            required_cols = ['session_id', 'question']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"CSV missing required columns: {required_cols}")
                st.error(f"CSV file must contain columns: {required_cols}")
                return []
            
            for _, row in df.iterrows():
                try:
                    session_id = int(row['session_id'])
                    
                    session = next((s for s in sessions if s['id'] == session_id), None)
                    if not session:
                        session = {
                            'id': session_id,
                            'title': str(row.get('title', f'Session {session_id}')),
                            'guidance': str(row.get('guidance', '')) if pd.notna(row.get('guidance', '')) else '',
                            'questions': [],
                            'word_target': int(row.get('word_target', 500)) if pd.notna(row.get('word_target', 500)) else 500
                        }
                        sessions.append(session)
                    
                    if pd.notna(row['question']):
                        session['questions'].append(str(row['question']).strip())
                except Exception as e:
                    logger.warning(f"Error processing row {_}: {e}")
                    continue
            
            logger.info(f"Loaded {len(sessions)} sessions from {csv_path}")
            return sorted(sessions, key=lambda x: x['id'])
            
        except Exception as e:
            logger.error(f"Error loading CSV {csv_path}: {e}")
            st.error(f"Error loading CSV file: {e}")
            return []
    
    def get_default_banks(self):
        """Get list of default banks from CSV files"""
        banks = []
        
        try:
            if self.default_banks_path.exists():
                for filename in self.default_banks_path.glob("*.csv"):
                    try:
                        bank_id = filename.stem
                        name_parts = bank_id.replace('_', ' ').title()
                        
                        df = pd.read_csv(filename)
                        sessions = df['session_id'].nunique()
                        topics = len(df)
                        
                        banks.append({
                            "id": bank_id,
                            "name": f"📖 {name_parts}",
                            "description": f"{sessions} sessions • {topics} topics",
                            "sessions": sessions,
                            "topics": topics,
                            "filename": filename.name,
                            "type": "default"
                        })
                        logger.debug(f"Found default bank: {bank_id}")
                    except Exception as e:
                        logger.error(f"Error reading {filename}: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error scanning default banks: {e}")
        
        return banks
    
    def load_default_bank(self, bank_id):
        """Load a default bank by ID"""
        filename = self.default_banks_path / f"{bank_id}.csv"
        
        if filename.exists():
            return self.load_sessions_from_csv(filename)
        logger.warning(f"Default bank not found: {bank_id}")
        return []
    
    # ============ CUSTOM BANK METHODS ============
    
    def get_user_banks(self):
        """Get all custom banks for the current user"""
        if not self.user_id:
            return []
        
        try:
            catalog_file = self.user_banks_path / self.user_id / "catalog.json"
            if catalog_file.exists():
                with open(catalog_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading user banks catalog: {e}")
        
        return []
    
    def _save_user_banks(self, banks):
        """Save user banks catalog with error handling"""
        if not self.user_id:
            return False
        
        try:
            catalog_file = self.user_banks_path / self.user_id / "catalog.json"
            catalog_file.parent.mkdir(parents=True, exist_ok=True)
            with open(catalog_file, 'w') as f:
                json.dump(banks, f, indent=2)
            logger.info(f"Saved user banks catalog for {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving user banks catalog: {e}")
            return False
    
    def create_custom_bank(self, name, description="", copy_from=None, bank_type="standard"):
        """Create a new custom bank with validation"""
        if not self.user_id:
            st.error("You must be logged in")
            return None
        
        if not name or not name.strip():
            st.error("Bank name cannot be empty")
            return None
        
        try:
            user_dir = self.user_banks_path / self.user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            bank_id = str(uuid.uuid4())[:8]
            now = datetime.now().isoformat()
            
            sessions = []
            if copy_from:
                sessions = self.load_default_bank(copy_from)
                logger.info(f"Copied {len(sessions)} sessions from {copy_from}")
            
            # For chapters-only banks, ensure all sessions have empty questions lists
            if bank_type == "chapters":
                for session in sessions:
                    session['questions'] = []
            
            # Save bank file
            bank_file = user_dir / f"{bank_id}.json"
            with open(bank_file, 'w') as f:
                json.dump({
                    'id': bank_id,
                    'name': name.strip(),
                    'description': description.strip(),
                    'created_at': now,
                    'updated_at': now,
                    'bank_type': bank_type,
                    'sessions': sessions
                }, f, indent=2)
            
            # Update catalog
            banks = self.get_user_banks()
            banks.append({
                'id': bank_id,
                'name': name.strip(),
                'description': description.strip(),
                'created_at': now,
                'updated_at': now,
                'session_count': len(sessions),
                'topic_count': sum(len(s.get('questions', [])) for s in sessions),
                'bank_type': bank_type
            })
            self._save_user_banks(banks)
            
            logger.info(f"Created {bank_type} bank: {bank_id} - {name}")
            st.success(f"✅ {bank_type.title()} Bank '{name}' created successfully!")
            return bank_id
            
        except Exception as e:
            logger.error(f"Error creating custom bank: {e}")
            st.error(f"Failed to create bank: {e}")
            return None
    
    def load_user_bank(self, bank_id):
        """Load a custom bank with validation"""
        if not self.user_id:
            return []
        
        try:
            bank_file = self.user_banks_path / self.user_id / f"{bank_id}.json"
            if bank_file.exists():
                with open(bank_file, 'r') as f:
                    data = json.load(f)
                    return data.get('sessions', [])
            else:
                logger.warning(f"Bank file not found: {bank_file}")
        except Exception as e:
            logger.error(f"Error loading user bank {bank_id}: {e}")
        
        return []
    
    def delete_user_bank(self, bank_id):
        """Delete a custom bank with validation"""
        if not self.user_id:
            return False
        
        try:
            bank_file = self.user_banks_path / self.user_id / f"{bank_id}.json"
            if bank_file.exists():
                bank_file.unlink()
                logger.info(f"Deleted bank file: {bank_file}")
            
            banks = self.get_user_banks()
            banks = [b for b in banks if b['id'] != bank_id]
            self._save_user_banks(banks)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting bank {bank_id}: {e}")
            return False
    
    def export_user_bank_to_csv(self, bank_id):
        """Export custom bank to CSV for download"""
        try:
            sessions = self.load_user_bank(bank_id)
            
            rows = []
            for session in sessions:
                questions = session.get('questions', [])
                if not questions:
                    # Add a placeholder for chapters-only banks
                    rows.append({
                        'session_id': session['id'],
                        'title': session['title'],
                        'guidance': session.get('guidance', ''),
                        'question': '',
                        'word_target': session.get('word_target', 500)
                    })
                else:
                    for i, q in enumerate(questions):
                        rows.append({
                            'session_id': session['id'],
                            'title': session['title'],
                            'guidance': session.get('guidance', '') if i == 0 else '',
                            'question': q,
                            'word_target': session.get('word_target', 500)
                        })
            
            if rows:
                df = pd.DataFrame(rows)
                return df.to_csv(index=False)
            
            logger.warning(f"No data to export for bank {bank_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error exporting bank {bank_id}: {e}")
            return None
    
    def save_user_bank(self, bank_id, sessions):
        """Save changes to a custom bank with validation"""
        if not self.user_id:
            return False
        
        try:
            bank_file = self.user_banks_path / self.user_id / f"{bank_id}.json"
            
            if bank_file.exists():
                with open(bank_file, 'r') as f:
                    data = json.load(f)
                
                data['sessions'] = sessions
                data['updated_at'] = datetime.now().isoformat()
                
                with open(bank_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                # Update catalog
                banks = self.get_user_banks()
                for bank in banks:
                    if bank['id'] == bank_id:
                        bank['updated_at'] = datetime.now().isoformat()
                        bank['session_count'] = len(sessions)
                        bank['topic_count'] = sum(len(s.get('questions', [])) for s in sessions)
                        break
                self._save_user_banks(banks)
                
                logger.info(f"Saved bank {bank_id} with {len(sessions)} sessions")
                return True
            
            logger.warning(f"Bank file not found for save: {bank_file}")
            return False
            
        except Exception as e:
            logger.error(f"Error saving bank {bank_id}: {e}")
            return False
    
    # ============ UI METHODS ============
    
    def display_bank_selector(self):
        """Main UI for bank selection"""
        st.title("📚 Question Bank Manager")
        
        tab1, tab2, tab3 = st.tabs(["📖 Default Banks", "✨ My Custom Banks", "➕ Create New"])
        
        with tab1:
            self._display_default_banks()
        
        with tab2:
            if self.user_id:
                self._display_my_banks()
            else:
                st.info("🔐 Please log in to manage custom question banks")
        
        with tab3:
            if self.user_id:
                self._display_create_bank_form()
            else:
                st.info("🔐 Please log in to create custom question banks")
    
    def _display_default_banks(self):
        """Display default banks with load buttons"""
        
        banks = self.get_default_banks()
        
        if not banks:
            st.info("📁 No question banks found. Please add CSV files to the question_banks/default/ folder.")
            return
        
        # 2-COLUMN GRID
        cols = st.columns(2)
        for i, bank in enumerate(banks):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="border:1px solid #ddd; border-radius:10px; padding:1rem; margin-bottom:1rem;">
                        <h4>{bank['name']}</h4>
                        <p>{bank['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load Question Bank"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_default_{bank['id']}_btn", 
                               use_container_width=True, type=button_type):
                        if not is_loaded:
                            sessions = self.load_default_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "default"
                                st.session_state.current_bank_id = bank['id']
                                
                                st.success(f"✅ Question Bank Loaded: '{bank['name']}'")
                                
                                for session in sessions:
                                    session_id = session["id"]
                                    if session_id not in st.session_state.responses:
                                        st.session_state.responses[session_id] = {
                                            "title": session["title"],
                                            "questions": {},
                                            "summary": "",
                                            "completed": False,
                                            "word_target": session.get("word_target", 500)
                                        }
                                st.rerun()
    
    def _display_my_banks(self):
        """Display user's custom banks - FIXED DUPLICATE KEYS"""
        banks = self.get_user_banks()
        
        if not banks:
            st.info("✨ You haven't created any custom question banks yet. Go to the 'Create New' tab to get started!")
            return
        
        # Create a unique status container for each bank using a session state key
        if 'bank_status_messages' not in st.session_state:
            st.session_state.bank_status_messages = {}
        
        for bank in banks:
            # Add emoji based on bank type
            bank_type_emoji = "📚" if bank.get('bank_type', 'standard') == 'standard' else "📖"
            bank_type_label = "Standard Bank" if bank.get('bank_type', 'standard') == 'standard' else "Chapters-Only Bank"
            
            with st.expander(f"{bank_type_emoji} {bank['name']} - {bank_type_label}", expanded=False):
                st.write(f"**Description:** {bank.get('description', 'No description')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Chapters/Sessions", bank.get('session_count', 0))
                with col2:
                    if bank.get('bank_type', 'standard') == 'standard':
                        st.metric("Topics", bank.get('topic_count', 0))
                    else:
                        st.metric("Type", "Chapters Only")
                
                st.caption(f"Created: {bank['created_at'][:10]}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    is_loaded = st.session_state.get('current_bank_id') == bank['id']
                    button_label = "✅ Loaded" if is_loaded else "📂 Load"
                    button_type = "secondary" if is_loaded else "primary"
                    
                    if st.button(button_label, key=f"load_user_{bank['id']}_btn", 
                               use_container_width=True, type=button_type):
                        if not is_loaded:
                            sessions = self.load_user_bank(bank['id'])
                            if sessions:
                                st.session_state.current_question_bank = sessions
                                st.session_state.current_bank_name = bank['name']
                                st.session_state.current_bank_type = "custom"
                                st.session_state.current_bank_id = bank['id']
                                
                                st.session_state.bank_status_messages[bank['id']] = {
                                    "type": "success",
                                    "message": f"✅ Bank Loaded: '{bank['name']}'"
                                }
                                
                                for session in sessions:
                                    session_id = session["id"]
                                    if session_id not in st.session_state.responses:
                                        st.session_state.responses[session_id] = {
                                            "title": session["title"],
                                            "questions": {},
                                            "summary": "",
                                            "completed": False,
                                            "word_target": session.get("word_target", 500)
                                        }
                                st.rerun()
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_user_{bank['id']}_btn", 
                               use_container_width=True):
                        st.session_state.bank_status_messages[bank['id']] = {
                            "type": "info",
                            "message": f"Opening editor for bank {bank['id']}"
                        }
                        st.session_state.editing_bank_id = bank['id']
                        st.session_state.editing_bank_name = bank['name']
                        st.session_state.show_bank_editor = True
                        st.rerun()
                
                with col3:
                    csv_data = self.export_user_bank_to_csv(bank['id'])
                    if csv_data:
                        st.download_button(
                            label="📥 Save as CSV",
                            data=csv_data,
                            file_name=f"{bank['name'].replace(' ', '_')}.csv",
                            mime="text/csv",
                            key=f"download_{bank['id']}_btn",
                            use_container_width=True
                        )
                    else:
                        st.button(
                            "📥 No Data", 
                            disabled=True, 
                            use_container_width=True,
                            key=f"no_data_{bank['id']}_btn"
                        )
                
                with col4:
                    if st.button("🗑️ Delete", key=f"delete_user_{bank['id']}_btn", 
                               use_container_width=True):
                        if self.delete_user_bank(bank['id']):
                            st.session_state.bank_status_messages[bank['id']] = {
                                "type": "success",
                                "message": f"✅ Deleted '{bank['name']}'"
                            }
                            st.rerun()
                
                # Show status message if exists
                if bank['id'] in st.session_state.bank_status_messages:
                    msg = st.session_state.bank_status_messages[bank['id']]
                    if msg["type"] == "success":
                        st.success(msg["message"])
                    elif msg["type"] == "error":
                        st.error(msg["message"])
                    else:
                        st.info(msg["message"])
                    # Clear after showing
                    del st.session_state.bank_status_messages[bank['id']]
    
    def _display_create_bank_form(self):
        """Display form to create new bank"""
        st.markdown("### Create New Question Bank")
        
        bank_type = st.radio(
            "Select Bank Type:",
            options=["standard", "chapters"],
            format_func=lambda x: "📚 Standard Bank (with topics/questions)" if x == "standard" else "📖 Chapters-Only Bank (just chapter titles, no topics)",
            horizontal=True,
            key="create_bank_type_radio",
            help="Chapters-Only banks are perfect for organizing your life into chapters without specific questions"
        )
        
        with st.form("create_bank_form"):
            name = st.text_input("Bank Name *", placeholder="e.g., 'My Life Chapters' or 'Family History'", 
                               key="create_bank_name_input")
            description = st.text_area("Description", placeholder="What kind of stories will this bank contain?", 
                                     key="create_bank_desc_input")
            
            st.markdown("#### Start from template (optional)")
            default_banks = self.get_default_banks()
            options = ["-- Start from scratch --"] + [b['name'] for b in default_banks]
            selected = st.selectbox("Copy questions from:", options, key="create_bank_template_select")
            
            submitted = st.form_submit_button("✅ Create Bank", type="primary", use_container_width=True)
            
            if submitted:
                if name and name.strip():
                    copy_from = None
                    if selected != "-- Start from scratch --":
                        for bank in default_banks:
                            if bank['name'] == selected:
                                copy_from = bank['id']
                                break
                    
                    self.create_custom_bank(name.strip(), description.strip(), copy_from, bank_type)
                    st.rerun()
                else:
                    st.error("❌ Please enter a bank name")
    
    def display_bank_editor(self, bank_id):
        """Display the bank editor interface with validation"""
        # Validate bank exists
        banks = self.get_user_banks()
        bank_info = next((b for b in banks if b['id'] == bank_id), None)
        
        if not bank_info:
            st.error(f"Bank with ID {bank_id} not found")
            if st.button("← Back to Bank Manager", key="back_from_error_btn"):
                st.session_state.show_bank_editor = False
                st.rerun()
            return
        
        bank_type = bank_info.get('bank_type', 'standard')
        
        # Add visible banner at the top
        bank_type_label = "📖 CHAPTERS-ONLY BANK" if bank_type == "chapters" else "📚 STANDARD BANK"
        banner_color = "#2196F3" if bank_type == "chapters" else "#4CAF50"
        
        st.markdown(f"""
        <div style="background-color: {banner_color}; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="color: white; margin: 0;">✏️ EDITOR MODE - {bank_type_label}: {bank_info.get('name', '')}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.title(f"Edit Bank")
        
        sessions = self.load_user_bank(bank_id)
        
        with st.expander("Bank Settings", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_name = st.text_input("Bank Name", value=bank_info.get('name', ''), 
                                       key="editor_bank_name_input")
                new_desc = st.text_area("Description", value=bank_info.get('description', ''), 
                                      key="editor_bank_desc_input")
            with col2:
                if st.button("💾 Save Settings", key="editor_save_settings_btn", 
                           use_container_width=True, type="primary"):
                    for bank in banks:
                        if bank['id'] == bank_id:
                            bank['name'] = new_name.strip()
                            bank['description'] = new_desc.strip()
                            bank['updated_at'] = datetime.now().isoformat()
                    if self._save_user_banks(banks):
                        st.success("✅ Settings saved")
                        st.rerun()
                    else:
                        st.error("Failed to save settings")
        
        st.divider()
        
        # Different header based on bank type
        if bank_type == "chapters":
            st.subheader("📖 Chapters")
            st.info("This is a Chapters-Only bank. Each chapter has a title and guidance, but no topic questions.")
        else:
            st.subheader("📋 Sessions")
        
        if st.button("➕ Add New " + ("Chapter" if bank_type == "chapters" else "Session"), 
                    key="editor_add_session_btn", use_container_width=True, type="primary"):
            max_id = max([s['id'] for s in sessions], default=0)
            sessions.append({
                'id': max_id + 1,
                'title': 'New ' + ("Chapter" if bank_type == "chapters" else "Session"),
                'guidance': '',
                'questions': [],
                'word_target': 500
            })
            if self.save_user_bank(bank_id, sessions):
                st.rerun()
            else:
                st.error("Failed to add new session")
        
        for i, session in enumerate(sessions):
            expander_title = f"📁 Chapter {session['id']}: {session['title']}" if bank_type == "chapters" else f"📁 Session {session['id']}: {session['title']}"
            
            with st.expander(expander_title, expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_title = st.text_input("Title", session['title'], 
                                            key=f"title_{session['id']}_input")
                    new_guidance = st.text_area("Guidance", session.get('guidance', ''), 
                                               key=f"guidance_{session['id']}_input", height=100)
                    new_target = st.number_input("Word Target", 
                                               value=session.get('word_target', 500),
                                               min_value=100, max_value=5000, step=100,
                                               key=f"target_{session['id']}_input")
                
                with col2:
                    st.write("**Actions**")
                    if i > 0:
                        if st.button("⬆️ Move Up", key=f"up_{session['id']}_btn", 
                                   use_container_width=True):
                            sessions[i], sessions[i-1] = sessions[i-1], sessions[i]
                            for idx, s in enumerate(sessions):
                                s['id'] = idx + 1
                            if self.save_user_bank(bank_id, sessions):
                                st.rerun()
                    
                    if i < len(sessions) - 1:
                        if st.button("⬇️ Move Down", key=f"down_{session['id']}_btn", 
                                   use_container_width=True):
                            sessions[i], sessions[i+1] = sessions[i+1], sessions[i]
                            for idx, s in enumerate(sessions):
                                s['id'] = idx + 1
                            if self.save_user_bank(bank_id, sessions):
                                st.rerun()
                    
                    if st.button("💾 Save", key=f"save_{session['id']}_btn", 
                               use_container_width=True, type="primary"):
                        session['title'] = new_title
                        session['guidance'] = new_guidance
                        session['word_target'] = new_target
                        if self.save_user_bank(bank_id, sessions):
                            st.success("✅ Saved")
                            st.rerun()
                        else:
                            st.error("Failed to save")
                    
                    if st.button("🗑️ Delete", key=f"delete_{session['id']}_btn", 
                               use_container_width=True):
                        sessions.pop(i)
                        for idx, s in enumerate(sessions):
                            s['id'] = idx + 1
                        if self.save_user_bank(bank_id, sessions):
                            st.rerun()
                
                # Only show topics/questions section for standard banks
                if bank_type == "standard":
                    st.divider()
                    st.write("**Topics/Questions:**")
                    
                    new_topic = st.text_input("Add new topic", key=f"new_topic_{session['id']}_input")
                    if new_topic and st.button("➕ Add", key=f"add_topic_{session['id']}_btn", 
                                             use_container_width=True):
                        session['questions'].append(new_topic)
                        if self.save_user_bank(bank_id, sessions):
                            st.rerun()
                    
                    for j, topic in enumerate(session.get('questions', [])):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            edited = st.text_area(f"Topic {j+1}", topic, 
                                                key=f"topic_{session['id']}_{j}_input", height=60)
                        
                        with col2:
                            if j > 0:
                                if st.button("⬆️", key=f"topic_up_{session['id']}_{j}_btn"):
                                    session['questions'][j], session['questions'][j-1] = session['questions'][j-1], session['questions'][j]
                                    if self.save_user_bank(bank_id, sessions):
                                        st.rerun()
                            if j < len(session['questions']) - 1:
                                if st.button("⬇️", key=f"topic_down_{session['id']}_{j}_btn"):
                                    session['questions'][j], session['questions'][j+1] = session['questions'][j+1], session['questions'][j]
                                    if self.save_user_bank(bank_id, sessions):
                                        st.rerun()
                        
                        with col3:
                            if st.button("💾", key=f"topic_save_{session['id']}_{j}_btn"):
                                session['questions'][j] = edited
                                if self.save_user_bank(bank_id, sessions):
                                    st.rerun()
                            
                            if st.button("🗑️", key=f"topic_del_{session['id']}_{j}_btn"):
                                session['questions'].pop(j)
                                if self.save_user_bank(bank_id, sessions):
                                    st.rerun()
                        
                        st.divider()
                else:
                    st.caption("✨ This is a chapters-only bank. No topics/questions needed.")
        
        if st.button("🔙 Back to Bank Manager", key="editor_back_btn", use_container_width=True):
            st.session_state.show_bank_editor = False
            st.rerun()
