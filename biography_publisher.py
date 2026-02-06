# biography_publisher.py - FIXED VERSION FOR BIOGRAPHER APP
import streamlit as st
import json
import base64
from datetime import datetime
import os
import tempfile

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide", page_icon="📖")

st.title("📖 Beautiful Biography Creator")
st.markdown("### 🎨 Create Your Illustrated Life Story")

def decode_stories_from_url():
    """Extract stories from URL parameter - FIXED FOR BIOGRAPHER FORMAT"""
    try:
        query_params = st.query_params
        encoded_data = query_params.get("data", [None])[0]
        
        if not encoded_data:
            return None
            
        # Decode the data
        json_data = base64.b64decode(encoded_data).decode()
        stories_data = json.loads(json_data)
        
        # TRANSFORM DATA TO MATCH PUBLISHER EXPECTED FORMAT
        transformed_data = {
            "user": stories_data.get("user", "Unknown"),
            "stories": {},
            "summary": stories_data.get("summary", {}),
            "export_date": stories_data.get("export_date", datetime.now().isoformat())
        }
        
        # Convert the stories from biographer format to publisher format
        for session_id, session_data in stories_data.get("stories", {}).items():
            transformed_data["stories"][session_id] = {
                "title": session_data.get("title", f"Session {session_id}"),
                "questions": {},
                "images": []  # Images will be empty since biographer doesn't export them directly
            }
            
            # Copy questions and answers
            for question, answer_info in session_data.get("questions", {}).items():
                if isinstance(answer_info, dict):
                    # Format from biographer: {"answer": "text", "timestamp": "date"}
                    transformed_data["stories"][session_id]["questions"][question] = {
                        "answer": answer_info.get("answer", ""),
                        "timestamp": answer_info.get("timestamp", datetime.now().isoformat())
                    }
                else:
                    # Fallback if it's just a string
                    transformed_data["stories"][session_id]["questions"][question] = {
                        "answer": str(answer_info),
                        "timestamp": datetime.now().isoformat()
                    }
        
        return transformed_data
    except Exception as e:
        st.error(f"Error decoding data: {e}")
        return None

def create_beautiful_biography(stories_data, include_images=True):
    """Create a professionally formatted biography with optional images"""
    user_name = stories_data.get("user", "Unknown")
    user_profile = stories_data.get("user_profile", {})
    stories_dict = stories_data.get("stories", {})
    
    # Collect all stories
    all_stories = []
    all_images = []
    
    for session_id, session_data in sorted(stories_dict.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        session_title = session_data.get("title", f"Chapter {session_id}")
        
        # Get session images (empty in biographer export)
        session_images = session_data.get("images", [])
        
        for question, answer_data in session_data.get("questions", {}).items():
            answer = answer_data.get("answer", "")
            if answer.strip():  # Only include non-empty answers
                story_entry = {
                    "session_id": session_id,
                    "session": session_title,
                    "question": question,
                    "answer": answer,
                    "date": answer_data.get("timestamp", datetime.now().isoformat())[:10],
                    "images": []
                }
                
                # Find images related to this session (empty in biographer)
                if session_images:
                    story_entry["images"] = session_images
                
                all_stories.append(story_entry)
        
        # Collect all images (empty in biographer)
        all_images.extend(session_images)
    
    if not all_stories:
        return "No stories found to publish.", [], user_name, 0, 0, 0, 0, {}
    
    # ========== CREATE BEAUTIFUL BIOGRAPHY ==========
    bio_text = "=" * 60 + "\n"
    bio_text += f"{'THE LIFE STORY OF':^60}\n"
    bio_text += f"{user_name.upper():^60}\n"
    bio_text += "=" * 60 + "\n\n"
    
    # Table of Contents
    bio_text += "TABLE OF CONTENTS\n"
    bio_text += "-" * 40 + "\n"
    
    current_session = None
    chapter_num = 0
    for i, story in enumerate(all_stories):
        if story["session"] != current_session:
            chapter_num += 1
            image_count = len(story["images"])
            photo_note = f" 📸 {image_count} photo(s)" if image_count > 0 else ""
            bio_text += f"\nChapter {chapter_num}: {story['session']}{photo_note}\n"
            current_session = story["session"]
    
    if all_images and include_images:
        bio_text += f"\n📸 Photo Gallery: {len(all_images)} images included\n"
    
    bio_text += "\n" + "=" * 60 + "\n\n"
    
    # Introduction
    bio_text += "FOREWORD\n\n"
    bio_text += f"This biography captures the unique life journey of {user_name}, "
    bio_text += f"compiled from personal reflections shared on {datetime.now().strftime('%B %d, %Y')}. "
    bio_text += "Each chapter represents a different phase of life, preserved here for future generations.\n\n"
    
    bio_text += "=" * 60 + "\n\n"
    
    # Chapters with stories
    current_session = None
    chapter_num = 0
    story_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += "\n" + "-" * 60 + "\n"
            bio_text += f"CHAPTER {chapter_num}\n"
            bio_text += f"{story['session'].upper()}\n"
            bio_text += "-" * 60 + "\n\n"
            current_session = story["session"]
        
        story_num += 1
        bio_text += f"STORY {story_num}\n"
        bio_text += f"Topic: {story['question']}\n"
        
        if story['date']:
            bio_text += f"Date Recorded: {story['date']}\n"
        
        bio_text += "-" * 40 + "\n"
        
        # Format the answer with proper paragraphs
        answer = story['answer'].strip()
        paragraphs = answer.split('\n')
        
        for para in paragraphs:
            if para.strip():
                # Add proper indentation for paragraphs
                bio_text += f"  {para.strip()}\n\n"
        
        bio_text += "\n"
    
    # Conclusion
    bio_text += "=" * 60 + "\n\n"
    bio_text += "EPILOGUE\n\n"
    bio_text += f"This collection contains {story_num} stories across {chapter_num} chapters, "
    bio_text += f"each one a piece of {user_name}'s unique mosaic of memories. "
    bio_text += "These reflections will continue to resonate long into the future.\n\n"
    
    # Statistics
    bio_text += "-" * 60 + "\n"
    bio_text += "BIOGRAPHY STATISTICS\n"
    bio_text += f"• Total Stories: {story_num}\n"
    bio_text += f"• Chapters: {chapter_num}\n"
    
    # Calculate word count
    total_words = sum(len(story['answer'].split()) for story in all_stories)
    bio_text += f"• Total Words: {total_words:,}\n"
    
    # Find longest story
    if all_stories:
        longest = max(all_stories, key=lambda x: len(x['answer'].split()))
        bio_text += f"• Longest Story: \"{longest['question'][:50]}...\" ({len(longest['answer'].split())} words)\n"
    
    bio_text += f"• Compiled: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    bio_text += "-" * 60 + "\n\n"
    
    # Final note
    bio_text += "This digital legacy was created with the Tell My Story Biographer, "
    bio_text += "preserving personal history for generations to come.\n\n"
    bio_text += "=" * 60
    
    return bio_text, all_stories, user_name, story_num, chapter_num, total_words, len(all_images), {}

def create_html_biography(stories_data, include_images=True):
    """Create an HTML version of the biography"""
    bio_text, all_stories, author_name, story_num, chapter_num, total_words, image_count, _ = create_beautiful_biography(stories_data, include_images)
    
    # Start HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{author_name}'s Biography</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:wght@400;600;700&family=Open+Sans:wght@300;400;600&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Crimson Text', serif;
            line-height: 1.8;
            color: #333;
            background: #fefefe;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            border-left: 1px solid #e0e0e0;
            border-right: 1px solid #e0e0e0;
            box-shadow: 0 0 30px rgba(0,0,0,0.1);
        }}
        
        .container {{
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 3px double #2c5282;
            margin-bottom: 40px;
        }}
        
        h1 {{
            font-size: 2.8em;
            color: #2c5282;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        
        .subtitle {{
            font-family: 'Open Sans', sans-serif;
            font-size: 1.2em;
            color: #666;
            font-weight: 300;
            margin-bottom: 30px;
        }}
        
        .chapter {{
            margin: 50px 0;
            padding: 30px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .chapter-title {{
            color: #2c5282;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .story {{
            margin: 25px 0;
            padding: 20px;
            background: #f8f9fa;
            border-left: 4px solid #4299e1;
            border-radius: 4px;
        }}
        
        .question {{
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        
        .answer {{
            font-size: 1.1em;
            line-height: 1.7;
            white-space: pre-line;
        }}
        
        .stats {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin: 40px 0;
            text-align: center;
        }}
        
        .stat-item {{
            display: inline-block;
            margin: 0 20px;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: 700;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 20px 10px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            .stat-item {{
                display: block;
                margin: 15px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{author_name}'s Life Story</h1>
            <div class="subtitle">
                A personal biography • {datetime.now().strftime('%B %d, %Y')}
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">{story_num}</span>
                <span class="stat-label">Stories</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{chapter_num}</span>
                <span class="stat-label">Chapters</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{total_words:,}</span>
                <span class="stat-label">Words</span>
            </div>
        </div>
        
        <div class="content">
            <h2 style="color: #2c5282; margin: 40px 0 20px 0;">Table of Contents</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
"""
    
    # Generate TOC
    current_session = None
    chapter_num = 0
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            html += f"<p style='margin: 10px 0;'><strong>Chapter {chapter_num}:</strong> {story['session']}</p>"
            current_session = story["session"]
    
    html += """
            </div>
    """
    
    # Add chapters
    current_session = None
    chapter_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            current_session = story["session"]
            
            html += f"""
            <div class="chapter">
                <h2 class="chapter-title">Chapter {chapter_num}: {story['session']}</h2>
            """
        
        # Add story
        html += f"""
        <div class="story">
            <div class="question">✏️ {story['question']}</div>
            <div class="answer">{story['answer']}</div>
        """
        
        # Add date if available
        if story['date']:
            html += f"""<div style="margin-top: 15px; font-size: 0.9em; color: #718096;">
                Recorded: {story['date']}
            </div>"""
        
        html += "</div>"  # Close story div
        
        # If this is the last story of the chapter
        next_idx = all_stories.index(story) + 1
        if next_idx >= len(all_stories) or all_stories[next_idx]["session"] != current_session:
            html += "</div>"  # Close chapter div
    
    # Close HTML
    html += f"""
        </div>
        
        <div class="footer">
            <p>Created with Tell My Story Biographer</p>
            <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p style="margin-top: 20px; font-size: 0.8em;">
                This biography contains {story_num} stories, {chapter_num} chapters, 
                and {total_words:,} words.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

# ============================================================================
# MAIN APP INTERFACE
# ============================================================================

# Try to get data from URL first
stories_data = decode_stories_from_url()

if stories_data:
    # Auto-process data from URL
    user_name = stories_data.get("user", "Unknown")
    summary = stories_data.get("summary", {})
    
    # Count stories
    story_count = 0
    for session_id, session_data in stories_data.get("stories", {}).items():
        story_count += len(session_data.get("questions", {}))
    
    if story_count > 0:
        # Display welcome message
        st.success(f"✅ Welcome, **{user_name}**!")
        st.info(f"📚 You have **{story_count} stories** ready to publish")
        
        if summary:
            st.caption(f"Total sessions: {summary.get('total_sessions', 0)} • Total stories: {summary.get('total_stories', 0)}")
        
        # Generate biography button
        if st.button("✨ Create Beautiful Biography", type="primary", use_container_width=True):
            with st.spinner("Crafting your beautiful biography..."):
                biography, all_stories, author_name, story_num, chapter_num, total_words, img_count, _ = create_beautiful_biography(
                    stories_data, 
                    include_images=False
                )
            
            # Show preview
            st.subheader("📖 Your Biography Preview")
            
            # Display in columns
            col_preview1, col_preview2 = st.columns([2, 1])
            
            with col_preview1:
                # Show first 1000 characters as preview
                preview_text = biography[:1000] + "..." if len(biography) > 1000 else biography
                st.text_area("Preview:", preview_text, height=300)
            
            with col_preview2:
                st.metric("Total Stories", story_num)
                st.metric("Chapters", chapter_num)
                st.metric("Total Words", f"{total_words:,}")
                st.metric("Biography Size", f"{len(biography):,} chars")
            
            # Download options
            st.subheader("📥 Download Your Biography")
            
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                # Plain text version
                safe_name = author_name.replace(" ", "_")
                st.download_button(
                    label="📄 Download Text Version",
                    data=biography,
                    file_name=f"{safe_name}_Biography.txt",
                    mime="text/plain",
                    type="primary",
                    use_container_width=True,
                    help="Standard text format"
                )
            
            with col_dl2:
                # HTML version
                html_biography = create_html_biography(stories_data, include_images=False)
                st.download_button(
                    label="🌐 Download HTML Version",
                    data=html_biography,
                    file_name=f"{safe_name}_Biography.html",
                    mime="text/html",
                    use_container_width=True,
                    help="Beautiful web format"
                )
            
            # Story preview
            with st.expander("📋 Preview Your Stories", expanded=True):
                for session_id, session_data in stories_data.get("stories", {}).items():
                    session_title = session_data.get('title', f'Chapter {session_id}')
                    
                    st.markdown(f"### {session_title}")
                    
                    for question, answer_data in session_data.get("questions", {}).items():
                        answer = answer_data.get("answer", "")
                        if answer.strip():
                            word_count = len(answer.split())
                            st.markdown(f"**{question}**")
                            st.write(f"{answer[:200]}..." if len(answer) > 200 else answer)
                            st.caption(f"{word_count} words")
                            st.divider()
            
            st.balloons()
            st.success(f"✨ Biography created! **{story_num} stories** across **{chapter_num} chapters** ({total_words:,} words)")
            
    else:
        st.warning(f"Found your profile (**{user_name}**) but no stories yet.")
        st.info("Go back to the main app and save some stories first!")
        
else:
    # Manual upload option
    st.info("📋 **How to create your biography:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 **Automatic Method**
        1. Go to your Tell My Story app
        2. Answer questions and save your responses
        3. Click the **Publish Biography** link at the bottom
        4. Your beautiful biography will be created automatically!
        """)
    
    with col2:
        st.markdown("""
        ### 📤 **Manual Upload**
        1. In the main app, use **Export Current Progress**
        2. Download the JSON file
        3. Upload it here:
        """)
        
        uploaded_file = st.file_uploader("Upload stories JSON", type=['json'])
        if uploaded_file:
            try:
                uploaded_data = json.load(uploaded_file)
                user_name = uploaded_data.get('user', 'Unknown')
                
                # Transform to match expected format
                transformed_data = {
                    "user": user_name,
                    "stories": uploaded_data.get("stories", {}),
                    "summary": uploaded_data.get("summary", {}),
                    "export_date": uploaded_data.get("export_date", datetime.now().isoformat())
                }
                
                story_count = 0
                for session_id, session_data in transformed_data.get("stories", {}).items():
                    story_count += len(session_data.get("questions", {}))
                
                st.success(f"✅ Loaded stories for **{user_name}**")
                st.info(f"📚 Found {story_count} stories")
                
                if story_count > 0 and st.button("Create Biography from File", type="primary"):
                    biography, all_stories, author_name, story_num, chapter_num, total_words, _, _ = create_beautiful_biography(transformed_data, include_images=False)
                    
                    safe_name = author_name.replace(" ", "_")
                    
                    # Offer download options
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Text Version",
                            data=biography,
                            file_name=f"{safe_name}_Biography.txt",
                            mime="text/plain"
                        )
                    with col_dl2:
                        html_version = create_html_biography(transformed_data, include_images=False)
                        st.download_button(
                            label="🌐 Download HTML Version",
                            data=html_version,
                            file_name=f"{safe_name}_Biography.html",
                            mime="text/html"
                        )
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("✨ **Professional formatting** • **Multiple export formats** • **Beautiful layout** • Your life story, beautifully preserved")
