# biography_publisher.py - UPDATED WITH CORRECT URL HANDLING
import streamlit as st
import json
import base64
from datetime import datetime
from urllib.parse import unquote

# Page setup
st.set_page_config(
    page_title="Tell My Story - Biography Publisher", 
    layout="wide", 
    page_icon="📖",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -1rem;
        margin-bottom: 2rem;
        border-radius: 0 0 20px 20px;
    }
    .story-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .download-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        margin-top: 1rem;
        text-align: center;
        text-decoration: none;
        display: inline-block;
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #48bb78;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
<h1>📖 Tell My Story - Biography Publisher</h1>
<p>Transform your memories into a beautiful book</p>
</div>
""", unsafe_allow_html=True)

def decode_stories_from_url():
    """Extract stories from URL parameter"""
    try:
        # Check query parameters
        query_params = st.query_params.to_dict()
        
        if 'data' in query_params:
            encoded_data = query_params['data']
            
            # If it's a list, take the first item
            if isinstance(encoded_data, list):
                encoded_data = encoded_data[0]
            
            if encoded_data:
                # URL decode
                encoded_data = unquote(encoded_data)
                
                # Decode base64
                json_data = base64.b64decode(encoded_data).decode('utf-8')
                stories_data = json.loads(json_data)
                
                st.success(f"✅ Successfully loaded stories for: {stories_data.get('user', 'Unknown User')}")
                return stories_data
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("Please go back to the main app and click 'Publish Biography' to send your stories here.")
        return None

def create_biography_text(stories_data):
    """Create a text version of the biography"""
    user_name = stories_data.get("user", "Unknown")
    user_profile = stories_data.get("user_profile", {})
    stories_dict = stories_data.get("stories", {})
    
    # Get user's name
    if user_profile and 'first_name' in user_profile:
        display_name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        if not display_name:
            display_name = user_name
    else:
        display_name = user_name
    
    bio_text = "=" * 70 + "\n"
    bio_text += f"{'TELL MY STORY':^70}\n"
    bio_text += f"{'A PERSONAL BIOGRAPHY':^70}\n"
    bio_text += "=" * 70 + "\n\n"
    
    bio_text += f"THE LIFE STORY OF\n{display_name.upper()}\n\n"
    bio_text += "-" * 70 + "\n\n"
    
    # Personal Information
    if user_profile:
        bio_text += "PERSONAL INFORMATION\n"
        bio_text += "-" * 40 + "\n"
        if user_profile.get('birthdate'):
            bio_text += f"Date of Birth: {user_profile.get('birthdate')}\n"
        if user_profile.get('gender'):
            bio_text += f"Gender: {user_profile.get('gender')}\n"
        bio_text += "\n"
    
    # Table of Contents
    bio_text += "TABLE OF CONTENTS\n"
    bio_text += "-" * 40 + "\n\n"
    
    session_count = 0
    story_count = 0
    
    # Sort sessions by ID
    try:
        sorted_sessions = sorted(stories_dict.items(), key=lambda x: int(x[0]))
    except:
        sorted_sessions = stories_dict.items()
    
    for session_id, session_data in sorted_sessions:
        session_count += 1
        session_title = session_data.get("title", f"Session {session_id}")
        questions = session_data.get("questions", {})
        
        if questions:
            bio_text += f"CHAPTER {session_count}: {session_title.upper()}\n"
            bio_text += f"  Contains {len(questions)} stories\n\n"
    
    bio_text += "\n" + "=" * 70 + "\n\n"
    
    # Stories by Chapter
    session_count = 0
    total_words = 0
    
    for session_id, session_data in sorted_sessions:
        session_title = session_data.get("title", f"Session {session_id}")
        questions = session_data.get("questions", {})
        
        if not questions:
            continue
            
        session_count += 1
        bio_text += f"CHAPTER {session_count}\n"
        bio_text += f"{session_title.upper()}\n"
        bio_text += "-" * 70 + "\n\n"
        
        story_num = 0
        for question, answer_data in questions.items():
            story_num += 1
            
            if isinstance(answer_data, dict):
                answer = answer_data.get("answer", "")
                timestamp = answer_data.get("timestamp", "")
            else:
                answer = str(answer_data)
                timestamp = ""
            
            if answer.strip():
                bio_text += f"STORY {story_num}\n"
                bio_text += f"Topic: {question}\n"
                
                if timestamp:
                    try:
                        date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y')
                        bio_text += f"Recorded: {date_str}\n"
                    except:
                        bio_text += f"Recorded: {timestamp[:10]}\n"
                
                bio_text += "-" * 40 + "\n"
                bio_text += answer.strip() + "\n\n"
                
                # Word count
                words = len(answer.split())
                total_words += words
                bio_text += f"[{words} words]\n\n"
    
    # Summary
    bio_text += "=" * 70 + "\n"
    bio_text += "SUMMARY\n"
    bio_text += "-" * 40 + "\n"
    bio_text += f"Total Chapters: {session_count}\n"
    bio_text += f"Total Stories: {sum(len(s['questions']) for s in stories_dict.values())}\n"
    bio_text += f"Total Words: {total_words:,}\n"
    bio_text += f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    bio_text += "\nCreated with Tell My Story Biographer\n"
    bio_text += "=" * 70
    
    return bio_text, display_name, session_count, total_words

def create_html_biography(stories_data):
    """Create an HTML version of the biography"""
    bio_text, display_name, chapter_count, word_count = create_biography_text(stories_data)
    
    # Count total stories
    stories_dict = stories_data.get("stories", {})
    total_stories = sum(len(session.get("questions", {})) for session in stories_dict.values())
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name}'s Biography</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fefefe;
        }}
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 3px double #2c5282;
            margin-bottom: 40px;
        }}
        h1 {{
            color: #2c5282;
            font-size: 2.8em;
            margin-bottom: 10px;
        }}
        .chapter {{
            margin: 40px 0;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .story {{
            margin: 25px 0;
            padding: 20px;
            background: #f8fafc;
            border-left: 4px solid #4299e1;
            border-radius: 5px;
        }}
        .stats {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 40px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
        }}
        @media print {{
            .no-print {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{display_name}'s Life Story</h1>
        <p>A Personal Biography • {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    <div class="stats">
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div style="margin: 10px;">
                <div style="font-size: 2.5em; font-weight: bold;">{chapter_count}</div>
                <div>Chapters</div>
            </div>
            <div style="margin: 10px;">
                <div style="font-size: 2.5em; font-weight: bold;">{total_stories}</div>
                <div>Stories</div>
            </div>
            <div style="margin: 10px;">
                <div style="font-size: 2.5em; font-weight: bold;">{word_count:,}</div>
                <div>Words</div>
            </div>
        </div>
    </div>
    
    <div style="background: #edf2f7; padding: 20px; border-radius: 10px; margin: 30px 0;">
        <h3 style="color: #2d3748; margin-top: 0;">Table of Contents</h3>
'''

    # Add Table of Contents
    try:
        sorted_sessions = sorted(stories_dict.items(), key=lambda x: int(x[0]))
    except:
        sorted_sessions = stories_dict.items()
    
    for i, (session_id, session_data) in enumerate(sorted_sessions, 1):
        session_title = session_data.get("title", f"Session {session_id}")
        story_count = len(session_data.get("questions", {}))
        html += f'<p style="margin: 8px 0;"><strong>Chapter {i}:</strong> {session_title} <span style="color: #4a5568;">({story_count} stories)</span></p>'

    html += '''
    </div>
    
    <div id="content">
'''

    # Add Chapters
    for i, (session_id, session_data) in enumerate(sorted_sessions, 1):
        session_title = session_data.get("title", f"Session {session_id}")
        questions = session_data.get("questions", {})
        
        if questions:
            html += f'''
            <div class="chapter">
                <h2 style="color: #2c5282; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
                    Chapter {i}: {session_title}
                </h2>
            '''
            
            for j, (question, answer_data) in enumerate(questions.items(), 1):
                if isinstance(answer_data, dict):
                    answer = answer_data.get("answer", "")
                else:
                    answer = str(answer_data)
                
                if answer.strip():
                    html += f'''
                    <div class="story">
                        <h3 style="color: #4a5568; margin-top: 0;">Story {j}: {question}</h3>
                        <div style="white-space: pre-line; font-size: 1.1em;">{answer}</div>
                    </div>
                    '''
            
            html += '</div>'

    html += f'''
    </div>
    
    <div class="footer">
        <p>Created with Tell My Story Biographer</p>
        <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        <p style="margin-top: 20px; font-size: 0.9em;">
            This biography contains {total_stories} stories across {chapter_count} chapters, 
            comprising {word_count:,} words in total.
        </p>
    </div>
    
    <div class="no-print" style="text-align: center; margin-top: 40px;">
        <button onclick="window.print()" style="
            background: #48bb78;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            margin: 20px;
        ">
            🖨️ Print This Biography
        </button>
    </div>
</body>
</html>'''
    
    return html, display_name

# ============================================================================
# MAIN APP
# ============================================================================

# Try to load data from URL
stories_data = decode_stories_from_url()

if stories_data:
    # Data loaded successfully
    user_name = stories_data.get("user", "Unknown")
    user_profile = stories_data.get("user_profile", {})
    
    # Count statistics
    stories_dict = stories_data.get("stories", {})
    total_stories = sum(len(session.get("questions", {})) for session in stories_dict.values())
    total_sessions = len(stories_dict)
    
    # Display user info
    col1, col2 = st.columns([3, 1])
    with col1:
        if user_profile and user_profile.get('first_name'):
            st.success(f"✅ Welcome, **{user_profile.get('first_name')} {user_profile.get('last_name', '')}**!")
        else:
            st.success(f"✅ Welcome, **{user_name}**!")
        
        if user_profile and user_profile.get('birthdate'):
            st.caption(f"🎂 Born: {user_profile.get('birthdate')}")
    
    with col2:
        st.metric("Total Sessions", total_sessions)
        st.metric("Total Stories", total_stories)
    
    # Create biography
    if st.button("✨ Create Beautiful Biography", type="primary", use_container_width=True):
        with st.spinner("Crafting your biography..."):
            # Create text version
            bio_text, display_name, chapter_count, word_count = create_biography_text(stories_data)
            
            # Create HTML version
            html_bio, html_name = create_html_biography(stories_data)
            
            # Display preview
            st.subheader("📖 Biography Preview")
            
            col_preview1, col_preview2 = st.columns(2)
            
            with col_preview1:
                st.text_area("Text Version Preview", bio_text[:1500] + "..." if len(bio_text) > 1500 else bio_text, height=300)
            
            with col_preview2:
                st.markdown("""
                ### 📊 Statistics
                """)
                st.metric("Chapters", chapter_count)
                st.metric("Total Stories", total_stories)
                st.metric("Total Words", f"{word_count:,}")
                st.metric("Biography Size", f"{len(bio_text):,} characters")
            
            # Download options
            st.subheader("📥 Download Your Biography")
            
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                safe_name = display_name.replace(" ", "_")
                st.download_button(
                    label="📄 Download Text Version",
                    data=bio_text,
                    file_name=f"{safe_name}_Biography.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
                st.caption("Plain text format - compatible with all devices")
            
            with col_dl2:
                st.download_button(
                    label="🌐 Download HTML Version",
                    data=html_bio,
                    file_name=f"{safe_name}_Biography.html",
                    mime="text/html",
                    use_container_width=True,
                    type="secondary"
                )
                st.caption("Beautiful web format - ready to print or share")
            
            # Preview stories
            with st.expander("📋 Preview Your Stories", expanded=False):
                try:
                    sorted_sessions = sorted(stories_dict.items(), key=lambda x: int(x[0]))
                except:
                    sorted_sessions = stories_dict.items()
                
                for session_id, session_data in sorted_sessions[:3]:  # Show first 3 sessions
                    session_title = session_data.get("title", f"Session {session_id}")
                    st.markdown(f"### {session_title}")
                    
                    for question, answer_data in list(session_data.get("questions", {}).items())[:2]:  # First 2 stories
                        if isinstance(answer_data, dict):
                            answer = answer_data.get("answer", "")
                        else:
                            answer = str(answer_data)
                        
                        if answer.strip():
                            st.markdown(f"**{question}**")
                            st.write(answer[:200] + "..." if len(answer) > 200 else answer)
                            st.divider()
            
            st.balloons()
            st.success(f"✨ Biography created! **{total_stories} stories** across **{chapter_count} chapters** ({word_count:,} words)")
    
else:
    # No data from URL - show manual upload
    st.info("📋 **Welcome to the Biography Publisher**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 **Automatic Method**
        1. Go to your Tell My Story app
        2. Answer questions and save your responses
        3. Click the **Publish Biography** button
        4. Your stories will automatically appear here
        """)
        
        st.markdown(f"""
        <a href="https://menuhunterai.com/wp-content/uploads/2026/02/tms_logo.png" target="_blank">
        <button style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 1rem;
        ">
        📖 Go to Tell My Story App
        </button>
        </a>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### 📤 **Manual Upload**
        If you have exported your stories as JSON:
        1. Download the JSON file from the main app
        2. Upload it here:
        """)
        
        uploaded_file = st.file_uploader("Choose a JSON file", type=['json'])
        if uploaded_file:
            try:
                uploaded_data = json.load(uploaded_file)
                st.success(f"✅ Loaded {len(uploaded_data.get('stories', {}))} sessions")
                
                if st.button("Create Biography from File", type="primary", use_container_width=True):
                    bio_text, display_name, chapter_count, word_count = create_biography_text(uploaded_data)
                    
                    safe_name = display_name.replace(" ", "_")
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Text Version",
                            data=bio_text,
                            file_name=f"{safe_name}_Biography.txt",
                            mime="text/plain"
                        )
                    with col_dl2:
                        html_bio, _ = create_html_biography(uploaded_data)
                        st.download_button(
                            label="🌐 Download HTML Version",
                            data=html_bio,
                            file_name=f"{safe_name}_Biography.html",
                            mime="text/html"
                        )
                        
                    st.success(f"Biography created for {display_name}!")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")

# Footer
st.markdown("---")
st.caption("✨ **Tell My Story Biography Publisher** • Create beautiful books from your life stories • Professional formatting • Multiple export options")
