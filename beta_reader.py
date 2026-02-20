# beta_reader.py
import streamlit as st
import json
import os
import re
import time
from datetime import datetime
from openai import OpenAI

class BetaReader:
    def __init__(self, openai_client):
        self.client = openai_client
    
    def get_session_full_text(self, session_id, responses_state):
        """Get all responses from a session as continuous text for beta reading"""
        if session_id not in responses_state:
            return ""
        
        session_text = ""
        session_data = responses_state[session_id]
        
        if "questions" in session_data:
            for question, answer_data in session_data["questions"].items():
                session_text += f"Q: {question}\nA: {answer_data['answer']}\n\n"
        
        return session_text
    
    def generate_feedback(self, session_title, session_text, feedback_type="comprehensive", profile_sections=None):
        """Generate beta reader/editor feedback for a completed session"""
        if not session_text.strip():
            return {"error": "Session has no content to analyze"}
        
        critique_templates = {
            "comprehensive": """You are a professional editor and beta reader. You have been given the subject's complete profile information above.

IMPORTANT INSTRUCTIONS:
1. Use the profile information to provide personalized feedback
2. When your feedback is influenced by specific profile details, mark it with [PROFILE: section_name] at the beginning of that comment
3. Check if the writing aligns with the subject's stated purpose, audience, and desired tone
4. Verify that the content accurately reflects the subject's life based on their profile
5. Suggest areas where the profile information could be better incorporated

Provide:
1. **Overall Impression** (2-3 sentences)
2. **Strengths** (3-5 bullet points - mark any profile-influenced comments)
3. **Areas for Improvement** (3-5 bullet points with specific suggestions - mark any profile-influenced comments)
4. **Continuity Check** (Note any timeline inconsistencies - mark any profile-influenced comments)
5. **Emotional Resonance** (How engaging/emotional is it? - mark any profile-influenced comments)
6. **Specific Edits** (3-5 suggested rewrites with explanations - mark any profile-influenced comments)""",
            
            "concise": """You are an experienced beta reader with access to the subject's profile. Provide brief, actionable feedback that references the profile when relevant.

IMPORTANT: Mark any profile-influenced comments with [PROFILE: section_name]

Focus on:
- Main strengths (mark profile-influenced ones)
- 2-3 specific areas to improve (mark profile-influenced ones)
- 1-2 specific editing suggestions""",
            
            "developmental": """You are a developmental editor with full access to the subject's profile. Evaluate how well the writing serves the subject's goals.

IMPORTANT: Mark any profile-influenced comments with [PROFILE: section_name]

Focus on:
- Narrative structure and flow (mark profile-influenced comments)
- Character/personality development (mark profile-influenced comments)
- Pacing and detail balance (mark profile-influenced comments)
- Theme consistency (mark profile-influenced comments)
- Suggested structural changes (mark profile-influenced comments)"""
        }
        
        prompt = critique_templates.get(feedback_type, critique_templates["comprehensive"])
        
        full_prompt = f"""{prompt}

        SESSION TITLE: {session_title}
        
        FULL CONTEXT (INCLUDING PROFILE):
        {session_text}
        
        Please provide your analysis, remembering to mark any profile-influenced comments with [PROFILE: section_name]:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a thoughtful, constructive editor who balances praise with helpful critique. You always reference the subject's profile information when providing feedback and mark those references clearly with [PROFILE: section_name]."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            feedback = response.choices[0].message.content
            
            # Add a summary of what profile information was used
            summary = ""
            if profile_sections:
                summary = "\n\n---\n📋 **PROFILE INFORMATION ACCESSED BY BETA READER:**\n"
                for section in set(profile_sections):
                    summary += f"• {section}\n"
                summary += "\n*Look for [PROFILE: section_name] markers in the feedback above to see where this information influenced the analysis.*\n"
            
            return {
                "session_title": session_title,
                "feedback": feedback + summary,
                "generated_at": datetime.now().isoformat(),
                "feedback_type": feedback_type,
                "profile_sections_used": list(set(profile_sections)) if profile_sections else []
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def save_feedback(self, user_id, session_id, feedback_data, get_user_filename_func, load_user_data_func):
        """Save beta feedback to user's data file"""
        try:
            filename = get_user_filename_func(user_id)
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
    
    def get_previous_feedback(self, user_id, session_id, get_user_filename_func, load_user_data_func):
        """Retrieve previous beta feedback for a session"""
        try:
            filename = get_user_filename_func(user_id)
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    user_data = json.load(f)
                
                if "beta_feedback" in user_data and str(session_id) in user_data["beta_feedback"]:
                    return user_data["beta_feedback"][str(session_id)]
        except:
            pass
        return None
    
    def show_modal(self, feedback, current_session, user_id, save_feedback_func, on_close_callback=None):
        """Display the beta reader feedback modal"""
        st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
        
        if st.button("← Back to Writing", key="beta_reader_back"):
            if on_close_callback:
                on_close_callback()
            st.rerun()
        
        st.title(f"🦋 Beta Reader: {feedback.get('session_title', 'Session')}")
        
        try:
            generated_date = datetime.fromisoformat(feedback['generated_at']).strftime('%B %d, %Y at %I:%M %p')
            st.caption(f"Generated: {generated_date}")
        except:
            st.caption("Generated: Recently")
        
        # Show what profile information was used
        if feedback.get('profile_sections_used'):
            with st.expander("📋 Profile Information Used", expanded=True):
                st.markdown("The Beta Reader accessed these profile sections to provide personalized feedback:")
                for section in feedback['profile_sections_used']:
                    st.markdown(f"✅ **{section}**")
                st.markdown("\n*Look for `[PROFILE: section_name]` markers in the feedback below to see where this information influenced specific comments.*")
        
        st.divider()
        
        st.subheader("📝 Editor's Analysis")
        
        # Process the feedback to highlight profile-influenced sections
        feedback_text = feedback["feedback"]
        
        # Split into sections and highlight profile markers
        parts = re.split(r'(\[PROFILE:.*?\])', feedback_text)
        formatted_feedback = ""
        for i, part in enumerate(parts):
            if part.startswith('[PROFILE:') and part.endswith(']'):
                # This is a profile marker - make it stand out
                formatted_feedback += f'<span style="background-color: #e8f4fd; color: #0366d6; font-weight: bold; padding: 2px 4px; border-radius: 4px;">{part}</span>'
            else:
                formatted_feedback += part
        
        st.markdown(formatted_feedback, unsafe_allow_html=True)
        
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Regenerate Feedback", use_container_width=True):
                if on_close_callback:
                    on_close_callback()
                st.rerun()
        
        with col2:
            if st.button("💾 Save to Profile", use_container_width=True, type="primary"):
                if save_feedback_func(user_id, current_session["id"], feedback):
                    st.success("Feedback saved!")
                    time.sleep(1)
                    if on_close_callback:
                        on_close_callback()
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
