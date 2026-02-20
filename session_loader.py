# session_loader.py
import pandas as pd
import os
import streamlit as st

DEFAULT_WORD_TARGET = 500

class SessionLoader:
    def __init__(self, csv_path="sessions/sessions.csv"):
        self.csv_path = csv_path
    
    def load_sessions_from_csv(self):
        """Load sessions ONLY from CSV file"""
        try:
            os.makedirs(os.path.dirname(self.csv_path) if os.path.dirname(self.csv_path) else '.', exist_ok=True)
            
            if not os.path.exists(self.csv_path):
                st.error(f"❌ Sessions CSV file not found: {self.csv_path}")
                st.info("""
                Please create a `sessions/sessions.csv` file with this format:
                
                session_id,title,guidance,question,word_target
                1,Childhood,"Welcome to Session 1...","What is your earliest memory?",500
                1,Childhood,,"Can you describe your family home?",500
                
                Guidance only needs to be in the first row of each session.
                """)
                return []
            
            df = pd.read_csv(self.csv_path)
            
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
