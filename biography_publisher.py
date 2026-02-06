import streamlit as st
import json
import base64
from datetime import datetime
from urllib.parse import unquote

st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Biography Publisher")

def decode_stories_from_url():
    try:
        query_params = st.query_params.to_dict()
        
        if 'data' in query_params:
            encoded_data = query_params['data']
            
            if isinstance(encoded_data, list):
                encoded_data = encoded_data[0]
            
            if encoded_data:
                encoded_data = unquote(encoded_data)
                json_data = base64.b64decode(encoded_data).decode()
                stories_data = json.loads(json_data)
                return stories_data
        
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def create_biography(stories_data):
    user_name = stories_data.get("user", "Unknown")
    stories_dict = stories_data.get("stories", {})
    
    all_stories = []
    for session_id, session_data in stories_dict.items():
        session_title = session_data.get("title", f"Session {session_id}")
        
        for question, answer_data in session_data.get("questions", {}).items():
            if isinstance(answer_data, dict):
                answer = answer_data.get("answer", "")
            else:
                answer = str(answer_data)
            
            if answer.strip():
                all_stories.append({
                    "session": session_title,
                    "question": question,
                    "answer": answer
                })
    
    if not all_stories:
        return "No stories found.", user_name, 0, 0, 0
    
    bio_text = "=" * 70 + "\n"
    bio_text += f"{'LIFE STORY':^70}\n"
    bio_text += f"{user_name.upper():^70}\n"
    bio_text += "=" * 70 + "\n\n"
    
    current_session = None
    chapter_num = 0
    story_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += f"\nCHAPTER {chapter_num}: {story['session'].upper()}\n"
            bio_text += "-" * 70 + "\n\n"
            current_session = story["session"]
        
        story_num += 1
        bio_text += f"Story {story_num}: {story['question']}\n"
        bio_text += "-" * 40 + "\n"
        bio_text += story['answer'] + "\n\n"
    
    bio_text += "=" * 70 + "\n"
    bio_text += f"Total: {story_num} stories in {chapter_num} chapters\n"
    total_words = sum(len(story['answer'].split()) for story in all_stories)
    bio_text += f"Words: {total_words:,}\n"
    bio_text += f"Created: {datetime.now().strftime('%B %d, %Y')}\n"
    bio_text += "=" * 70
    
    return bio_text, user_name, story_num, chapter_num, total_words

# Main app
stories_data = decode_stories_from_url()

if stories_data:
    user_name = stories_data.get("user", "Unknown")
    
    story_count = 0
    for session_data in stories_data.get("stories", {}).values():
        story_count += len(session_data.get("questions", {}))
    
    if story_count > 0:
        st.success(f"✅ Loaded {story_count} stories for {user_name}")
        
        if st.button("Create Biography", type="primary", use_container_width=True):
            bio_text, author_name, story_num, chapter_num, total_words = create_biography(stories_data)
            
            st.balloons()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.text_area("Your Biography:", bio_text, height=400)
            
            with col2:
                st.metric("Stories", story_num)
                st.metric("Chapters", chapter_num)
                st.metric("Words", f"{total_words:,}")
            
            safe_name = author_name.replace(" ", "_")
            st.download_button(
                label="📥 Download Biography",
                data=bio_text,
                file_name=f"{safe_name}_Biography.txt",
                mime="text/plain",
                use_container_width=True
            )
            
            st.success(f"✨ Biography created! {story_num} stories, {chapter_num} chapters")
    else:
        st.warning("No stories found in data")
else:
    st.info("No data loaded. Go to your biographer app and click 'Publish Biography'")

st.markdown("---")
st.caption("Biography Publisher - No login required")

