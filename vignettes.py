# vignettes.py - COMPLETE WORKING VERSION WITH IMPORT BUTTON
import streamlit as st
import json
from datetime import datetime
import os
import uuid
import re
import base64
import hashlib
import time
import openai

from streamlit_quill import st_quill

class VignetteManager:
    def __init__(self, user_id):
        self.user_id = user_id
        self.file = f"user_vignettes/{user_id}_vignettes.json"
        os.makedirs("user_vignettes", exist_ok=True)
        os.makedirs(f"user_vignettes/{user_id}_images", exist_ok=True)
        self.standard_themes = [
            "Life Lesson", "Achievement", "Work Experience", "Loss of Life",
            "Illness", "New Child", "Marriage", "Travel", "Relationship",
            "Interests", "Education", "Childhood Memory", "Family Story",
            "Career Moment", "Personal Growth"
        ]
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.file):
                with open(self.file, 'r') as f:
                    self.vignettes = json.load(f)
            else:
                self.vignettes = []
        except:
            self.vignettes = []
    
    def _save(self):
        with open(self.file, 'w') as f:
            json.dump(self.vignettes, f, indent=2)
    
    def save_vignette_image(self, uploaded_file, vignette_id):
        try:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            image_id = hashlib.md5(f"{vignette_id}{uploaded_file.name}{datetime.now()}".encode()).hexdigest()[:12]
            filename = f"{image_id}.{file_ext}"
            filepath = f"user_vignettes/{self.user_id}_images/{filename}"
            
            with open(filepath, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            img_bytes = uploaded_file.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return {
                "id": image_id,
                "filename": filename,
                "base64": img_base64,
                "path": filepath,
                "caption": ""
            }
        except Exception as e:
            st.error(f"Error saving image: {e}")
            return None
    
    def create_vignette(self, title, content, theme, mood="Reflective", is_draft=False, images=None):
        v = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "content": content,
            "theme": theme,
            "mood": mood,
            "word_count": len(re.sub(r'<[^>]+>', '', content).split()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_draft": is_draft,
            "is_published": not is_draft,
            "images": images or []
        }
        self.vignettes.append(v)
        self._save()
        return v
    
    def create_vignette_with_id(self, id, title, content, theme, mood="Reflective", is_draft=False, images=None):
        """Create a vignette with a specific ID (for new vignettes)"""
        v = {
            "id": id,
            "title": title,
            "content": content,
            "theme": theme,
            "mood": mood,
            "word_count": len(re.sub(r'<[^>]+>', '', content).split()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_draft": is_draft,
            "is_published": not is_draft,
            "images": images or []
        }
        self.vignettes.append(v)
        self._save()
        return v
    
    def update_vignette(self, id, title, content, theme, mood=None, images=None):
        for v in self.vignettes:
            if v["id"] == id:
                v.update({
                    "title": title, 
                    "content": content, 
                    "theme": theme, 
                    "mood": mood or v.get("mood", "Reflective"),
                    "word_count": len(re.sub(r'<[^>]+>', '', content).split()), 
                    "updated_at": datetime.now().isoformat(),
                    "images": images or v.get("images", [])
                })
                self._save()
                return True
        return False
    
    def delete_vignette(self, id):
        self.vignettes = [v for v in self.vignettes if v["id"] != id]
        self._save()
        return True
    
    def get_vignette_by_id(self, id):
        for v in self.vignettes:
            if v["id"] == id:
                return v
        return None
    
    def check_spelling(self, text):
        """Check spelling and grammar using OpenAI"""
        if not text: 
            return text
        try:
            client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Fix spelling and grammar. Return only corrected text."},
                    {"role": "user", "content": text}
                ],
                max_tokens=len(text) + 100, 
                temperature=0.1
            )
            return resp.choices[0].message.content
        except Exception as e:
            st.error(f"Spell check failed: {e}")
            return text
    
    def ai_rewrite_vignette(self, original_text, person_option, vignette_title):
        """Rewrite the vignette in 1st, 2nd, or 3rd person using profile context"""
        try:
            client = openai.OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))
            
            clean_text = re.sub(r'<[^>]+>', '', original_text)
            
            if len(clean_text.split()) < 5:
                return {"error": "Text too short to rewrite (minimum 5 words)"}
            
            person_instructions = {
                "1st": {"name": "First Person", "emoji": "👤"},
                "2nd": {"name": "Second Person", "emoji": "💬"},
                "3rd": {"name": "Third Person", "emoji": "📖"}
            }
            
            system_prompt = f"""Rewrite this in {person_instructions[person_option]['name']}.
            Preserve all key facts and emotions. Return only the rewritten text.
            
            ORIGINAL:
            {clean_text}
            
            REWRITTEN:"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}],
                max_tokens=len(clean_text.split()) * 3,
                temperature=0.7
            )
            
            rewritten = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "original": clean_text,
                "rewritten": rewritten,
                "person": person_instructions[person_option]["name"],
                "emoji": person_instructions[person_option]["emoji"]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ============================================================================
    # FILE IMPORT FUNCTION
    # ============================================================================
    def import_text_file(self, uploaded_file):
        """Import text from common document formats"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            file_content = ""
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            
            st.info(f"📄 Importing: {uploaded_file.name} ({file_size_mb:.1f}MB)")
            
            # Supported formats
            if file_extension == 'txt':
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
            
            elif file_extension == 'docx':
                try:
                    import io
                    from docx import Document
                    docx_bytes = io.BytesIO(uploaded_file.getvalue())
                    doc = Document(docx_bytes)
                    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                    file_content = '\n\n'.join(paragraphs)
                except ImportError:
                    st.error("Please install: pip install python-docx")
                    return None
            
            elif file_extension == 'rtf':
                try:
                    from striprtf.striprtf import rtf_to_text
                    rtf_content = uploaded_file.read().decode('utf-8', errors='ignore')
                    file_content = rtf_to_text(rtf_content)
                except ImportError:
                    st.warning("RTF support needs: pip install striprtf")
                    return None
            
            elif file_extension in ['vtt', 'srt']:
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                lines = file_content.split('\n')
                clean_lines = [line.strip() for line in lines if '-->' not in line and not line.strip().isdigit() and line.strip()]
                file_content = ' '.join(clean_lines)
            
            elif file_extension == 'json':
                try:
                    import json
                    data = json.loads(uploaded_file.read().decode('utf-8'))
                    if isinstance(data, dict):
                        file_content = data.get('text', data.get('transcript', str(data)))
                    else:
                        file_content = str(data)
                except Exception as e:
                    st.error(f"Error parsing JSON: {e}")
                    return None
            
            elif file_extension == 'md':
                file_content = uploaded_file.read().decode('utf-8', errors='ignore')
                file_content = re.sub(r'#{1,6}\s*', '', file_content)
                file_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', file_content)
            
            else:
                st.error(f"Unsupported format: .{file_extension}")
                st.info("Supported: .txt, .docx, .rtf, .vtt, .srt, .json, .md")
                return None
            
            if not file_content or not file_content.strip():
                st.warning("File is empty")
                return None
            
            # Clean and format
            file_content = re.sub(r'\s+', ' ', file_content)
            sentences = re.split(r'[.!?]+', file_content)
            paragraphs = []
            current_para = []
            
            for sentence in sentences:
                if sentence.strip():
                    current_para.append(sentence.strip() + '.')
                    if len(current_para) >= 4:
                        paragraphs.append(' '.join(current_para))
                        current_para = []
            
            if current_para:
                paragraphs.append(' '.join(current_para))
            
            if not paragraphs:
                paragraphs = [file_content]
            
            html_content = ''
            for para in paragraphs:
                if para.strip():
                    para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html_content += f'<p>{para.strip()}</p>'
            
            return html_content
            
        except Exception as e:
            st.error(f"Import error: {str(e)}")
            return None
    
    def display_vignette_creator(self, on_publish=None, edit_vignette=None):
        # Now edit_vignette is ALWAYS provided (even for new ones)
        vignette_id = edit_vignette['id']
        base_key = f"vignette_{vignette_id}"
        
        # Editor key and content key
        editor_key = f"quill_vignette_{vignette_id}"
        content_key = f"{editor_key}_content"
        
        # Import state
        import_key = f"import_{editor_key}"
        if import_key not in st.session_state:
            st.session_state[import_key] = False
        
        # Add a version counter for this editor
        version_key = f"{editor_key}_version"
        if version_key not in st.session_state:
            st.session_state[version_key] = 0
        
        # Title input
        title = st.text_input(
            "Title", 
            value=edit_vignette.get("title", ""),
            placeholder="Give your vignette a meaningful title",
            key=f"{base_key}_title"
        )
        
        # Theme and mood in columns
        col1, col2 = st.columns(2)
        with col1:
            theme_options = self.standard_themes + ["Custom"]
            current_theme = edit_vignette.get("theme", self.standard_themes[0])
            if current_theme in self.standard_themes:
                theme_index = self.standard_themes.index(current_theme)
                theme = st.selectbox("Theme", theme_options, index=theme_index, key=f"{base_key}_theme")
            else:
                theme = st.selectbox("Theme", theme_options, index=len(theme_options)-1, key=f"{base_key}_theme")
                if theme == "Custom":
                    theme = st.text_input("Custom Theme", value=current_theme, key=f"{base_key}_custom_theme")
        
        with col2:
            mood_options = ["Reflective", "Joyful", "Bittersweet", "Humorous", "Serious", "Inspiring", "Nostalgic"]
            current_mood = edit_vignette.get("mood", "Reflective")
            mood_index = mood_options.index(current_mood) if current_mood in mood_options else 0
            mood = st.selectbox("Mood/Tone", mood_options, index=mood_index, key=f"{base_key}_mood")
        
        # Initialize content in session state
        if content_key not in st.session_state:
            st.session_state[content_key] = edit_vignette.get("content", "<p>Write your story here...</p>")
        
        st.markdown("### 📝 Your Story")
        st.markdown("""
        <div class="image-drop-info">
            📸 <strong>Drag & drop images</strong> directly into the editor.
        </div>
        """, unsafe_allow_html=True)
        
        # Editor component key with version
        editor_component_key = f"quill_editor_{vignette_id}_v{st.session_state[version_key]}"
        
        # Display Quill editor
        content = st_quill(
            value=st.session_state[content_key],
            key=editor_component_key,
            placeholder="Write your story here...",
            html=True
        )
        
        # Update session state when content changes
        if content is not None and content != st.session_state[content_key]:
            st.session_state[content_key] = content
        
        st.markdown("---")
        
        # ============================================================================
        # BUTTONS ROW
        # ============================================================================
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 2])
        
        # Spellcheck state management
        spellcheck_base = f"spell_{editor_key}"
        spell_result_key = f"{spellcheck_base}_result"
        current_content = st.session_state.get(content_key, "")
        has_content = current_content and current_content != "<p><br></p>" and current_content != "<p>Write your story here...</p>"
        showing_results = spell_result_key in st.session_state and st.session_state[spell_result_key].get("show", False)
        
        with col1:
            if st.button("💾 Save Draft", key=f"{base_key}_save_draft", type="primary", use_container_width=True):
                if not current_content or current_content in ["<p><br></p>", "<p></p>", "<p>Write your story here...</p>"]:
                    st.error("Please write some content")
                else:
                    final_title = title.strip() or "Untitled"
                    self.update_vignette(vignette_id, final_title, current_content, theme, mood)
                    st.success("✅ Draft saved!")
                    
                    if spell_result_key in st.session_state:
                        del st.session_state[spell_result_key]
                    
                    time.sleep(1)
                    st.session_state.show_vignette_modal = False
                    st.session_state.show_vignette_manager = True
                    st.rerun()
        
        with col2:
            if st.button("📢 Publish", key=f"{base_key}_publish", use_container_width=True, type="primary"):
                if not current_content or current_content in ["<p><br></p>", "<p></p>", "<p>Write your story here...</p>"]:
                    st.error("Please write some content")
                else:
                    final_title = title.strip() or "Untitled"
                    edit_vignette["is_draft"] = False
                    edit_vignette["published_at"] = datetime.now().isoformat()
                    self.update_vignette(vignette_id, final_title, current_content, theme, mood)
                    st.success("🎉 Published successfully!")
                    
                    if on_publish:
                        on_publish(edit_vignette)
                    
                    if spell_result_key in st.session_state:
                        del st.session_state[spell_result_key]
                    
                    time.sleep(1)
                    st.session_state.show_vignette_modal = False
                    st.session_state.show_vignette_manager = True
                    st.rerun()
        
        with col3:
            if has_content and not showing_results:
                if st.button("🔍 Spell Check", key=f"{base_key}_spell", use_container_width=True):
                    with st.spinner("Checking spelling and grammar..."):
                        text_only = re.sub(r'<[^>]+>', '', current_content)
                        if len(text_only.split()) >= 3:
                            corrected = self.check_spelling(text_only)
                            if corrected and corrected != text_only:
                                st.session_state[spell_result_key] = {
                                    "original": text_only,
                                    "corrected": corrected,
                                    "show": True
                                }
                            else:
                                st.session_state[spell_result_key] = {
                                    "message": "✅ No spelling or grammar issues found!",
                                    "show": True
                                }
                            st.rerun()
                        else:
                            st.warning("Text too short for spell check (minimum 3 words)")
            else:
                st.button("🔍 Spell Check", key=f"{base_key}_spell_disabled", disabled=True, use_container_width=True)
        
        with col4:
            if has_content:
                if st.button("✨ AI Rewrite", key=f"{base_key}_ai_rewrite", use_container_width=True):
                    st.session_state[f"{base_key}_show_ai_menu"] = True
                    st.rerun()
            else:
                st.button("✨ AI Rewrite", key=f"{base_key}_ai_disabled", disabled=True, use_container_width=True)
        
        with col5:
            # IMPORT BUTTON - Works on all vignettes
            show_import = st.session_state.get(import_key, False)
            button_label = "📂 Close Import" if show_import else "📂 Import File"
            
            if st.button(button_label, key=f"{base_key}_import", use_container_width=True):
                st.session_state[import_key] = not show_import
                st.rerun()
        
        with col6:
            if st.session_state.get(f"{base_key}_show_ai_menu", False):
                person_option = st.selectbox(
                    "Voice:",
                    options=["1st", "2nd", "3rd"],
                    format_func=lambda x: {"1st": "👤 First Person", "2nd": "💬 Second Person", "3rd": "📖 Third Person"}[x],
                    key=f"{base_key}_ai_person",
                    label_visibility="collapsed"
                )
                
                if st.button("Go", key=f"{base_key}_ai_go", type="primary", use_container_width=True):
                    with st.spinner(f"Rewriting in {person_option} person..."):
                        result = self.ai_rewrite_vignette(
                            current_content, 
                            person_option, 
                            title or "Untitled Vignette"
                        )
                        
                        if result.get('success'):
                            st.session_state[f"{base_key}_ai_result"] = result
                            st.session_state[f"{base_key}_show_ai_menu"] = False
                            st.rerun()
                        else:
                            st.error(result.get('error', 'Failed to rewrite'))
            else:
                st.markdown("")
        
        with col7:
            nav1, nav2 = st.columns(2)
            with nav1:
                if st.button("👁️ Preview", key=f"{base_key}_preview", use_container_width=True):
                    st.session_state[f"{base_key}_show_preview"] = True
                    st.rerun()
            with nav2:
                if st.button("❌ Cancel", key=f"{base_key}_cancel", use_container_width=True):
                    # Clear all session state for this vignette
                    keys_to_clear = [content_key, version_key, spell_result_key,
                                    f"{base_key}_ai_result", f"{base_key}_show_ai_menu", 
                                    f"{base_key}_show_preview"]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            try:
                                del st.session_state[key]
                            except:
                                pass
                    st.session_state.show_vignette_modal = False
                    st.session_state.editing_vignette_id = None
                    st.rerun()
        
        # Display import section if toggled
        if st.session_state.get(import_key, False):
            st.markdown("---")
            st.markdown("### 📂 Import Text File")
            
            # Show supported formats table
            with st.expander("📋 Supported File Formats", expanded=True):
                st.markdown("""
                | Format | Description |
                |--------|-------------|
                | **.txt** | Plain text |
                | **.docx** | Microsoft Word |
                | **.rtf** | Rich Text Format |
                | **.vtt/.srt** | Subtitle files |
                | **.json** | Transcription JSON |
                | **.md** | Markdown |
                
                **Maximum file size:** 50MB
                """)
            
            uploaded_file = st.file_uploader(
                "Choose a file to import",
                type=['txt', 'docx', 'rtf', 'vtt', 'srt', 'json', 'md'],
                key=f"{base_key}_file_uploader",
                help="Select a file from your computer to import into this vignette"
            )
            
            if uploaded_file:
                col_imp1, col_imp2 = st.columns(2)
                with col_imp1:
                    if st.button("📥 Import", key=f"{base_key}_do_import", type="primary", use_container_width=True):
                        with st.spinner("Importing file..."):
                            imported_html = self.import_text_file(uploaded_file)
                            if imported_html:
                                # Replace content
                                st.session_state[content_key] = imported_html
                                st.session_state[version_key] += 1
                                st.session_state[import_key] = False
                                st.success("✅ File imported successfully!")
                                st.rerun()
                
                with col_imp2:
                    if st.button("❌ Cancel", key=f"{base_key}_cancel_import", use_container_width=True):
                        st.session_state[import_key] = False
                        st.rerun()
        
        # Display spellcheck results if they exist
        if showing_results:
            result = st.session_state[spell_result_key]
            if "corrected" in result:
                st.markdown("---")
                st.markdown("### ✅ Suggested Corrections:")
                st.markdown(f'<div style="background-color: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">{result["corrected"]}</div>', unsafe_allow_html=True)
                
                col_apply1, col_apply2 = st.columns(2)
                with col_apply1:
                    if st.button("📋 Apply Corrections", key=f"{base_key}_apply", type="primary", use_container_width=True):
                        corrected = result["corrected"]
                        if not corrected.startswith('<p>'):
                            corrected = f'<p>{corrected}</p>'
                        
                        st.session_state[content_key] = corrected
                        st.session_state[version_key] += 1
                        st.session_state[spell_result_key] = {"show": False}
                        st.success("✅ Corrections applied!")
                        st.rerun()
                
                with col_apply2:
                    if st.button("❌ Dismiss", key=f"{base_key}_dismiss", use_container_width=True):
                        st.session_state[spell_result_key] = {"show": False}
                        st.rerun()
            
            elif "message" in result:
                st.success(result["message"])
                if st.button("Dismiss", key=f"{base_key}_dismiss_msg"):
                    st.session_state[spell_result_key] = {"show": False}
                    st.rerun()
        
        # Display AI rewrite result if available
        if st.session_state.get(f"{base_key}_ai_result"):
            result = st.session_state[f"{base_key}_ai_result"]
            
            st.markdown("---")
            st.markdown(f"### {result.get('emoji', '✨')} AI Rewrite Result - {result['person']}")
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown("**📝 Original Version:**")
                with st.container():
                    st.markdown(f'<div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; border-left: 4px solid #ccc;">{result["original"]}</div>', unsafe_allow_html=True)
            
            with col_res2:
                st.markdown(f"**✨ Rewritten Version ({result['person']}):**")
                with st.container():
                    st.markdown(f'<div style="background-color: #e8f4fd; padding: 15px; border-radius: 5px; border-left: 4px solid #4a90e2;">{result["rewritten"]}</div>', unsafe_allow_html=True)
            
            col_apply1, col_apply2 = st.columns(2)
            with col_apply1:
                if st.button("📝 Replace Original", key=f"{base_key}_ai_replace", type="primary", use_container_width=True):
                    new_content = result["rewritten"]
                    if not new_content.startswith('<p>'):
                        new_content = f'<p>{new_content}</p>'
                    
                    st.session_state[content_key] = new_content
                    st.session_state[version_key] += 1
                    del st.session_state[f"{base_key}_ai_result"]
                    st.session_state[f"{base_key}_show_ai_menu"] = False
                    st.rerun()
            
            with col_apply2:
                if st.button("❌ Dismiss", key=f"{base_key}_ai_dismiss", use_container_width=True):
                    del st.session_state[f"{base_key}_ai_result"]
                    st.rerun()
        
        # Preview section
        if st.session_state.get(f"{base_key}_show_preview", False) and st.session_state[content_key]:
            st.markdown("---")
            st.markdown("### 👁️ Preview")
            st.markdown(f"## {title or 'Untitled'}")
            st.markdown(f"**Theme:** {theme}  |  **Mood:** {mood}")
            st.markdown("---")
            st.markdown(st.session_state[content_key], unsafe_allow_html=True)
            
            if st.button("✕ Close Preview", key=f"{base_key}_close_preview"):
                st.session_state[f"{base_key}_show_preview"] = False
                st.rerun()
    
    def display_vignette_gallery(self, filter_by="all", on_select=None, on_edit=None, on_delete=None):
        if filter_by == "published":
            vs = [v for v in self.vignettes if not v.get("is_draft", True)]
        elif filter_by == "drafts":
            vs = [v for v in self.vignettes if v.get("is_draft", False)]
        else:
            vs = self.vignettes
        
        vs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        # Display success messages
        if st.session_state.get("publish_success"):
            st.success("🎉 Published successfully!")
            del st.session_state.publish_success
        if st.session_state.get("draft_success"):
            st.success("💾 Draft saved successfully!")
            del st.session_state.draft_success
        if st.session_state.get("edit_success"):
            st.success("✅ Changes saved successfully!")
            del st.session_state.edit_success
        if st.session_state.get("delete_success"):
            st.success("🗑️ Deleted successfully!")
            del st.session_state.delete_success
        
        if not vs:
            st.info("No vignettes yet. Click 'Create New Vignette' to start writing.")
            return
        
        for v in vs:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    status_emoji = "📢" if not v.get("is_draft") else "📝"
                    status_text = "Published" if not v.get("is_draft") else "Draft"
                    st.markdown(f"### {status_emoji} {v['title']}  `{status_text}`")
                    st.markdown(f"*{v['theme']}*")
                    
                    content_preview = re.sub(r'<[^>]+>', '', v['content'])
                    if len(content_preview) > 100:
                        content_preview = content_preview[:100] + "..."
                    st.markdown(content_preview)
                    
                    date_str = datetime.fromisoformat(v.get('updated_at', v.get('created_at', ''))).strftime('%b %d, %Y')
                    st.caption(f"📝 {v['word_count']} words • Last updated: {date_str}")
                    if v.get('images'):
                        st.caption(f"📸 {len(v['images'])} image(s)")
                
                with col2:
                    if st.button("📖 Read", key=f"read_{v['id']}", use_container_width=True):
                        if on_select:
                            on_select(v['id'])
                
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{v['id']}", use_container_width=True):
                        if on_edit:
                            on_edit(v['id'])
                
                with col4:
                    if st.button("🗑️ Delete", key=f"del_{v['id']}", use_container_width=True):
                        self.delete_vignette(v['id'])
                        st.session_state.delete_success = True
                        st.rerun()
                
                st.divider()
    
    def display_full_vignette(self, id, on_back=None, on_edit=None):
        v = self.get_vignette_by_id(id)
        if not v:
            return
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← Back", use_container_width=True):
                if on_back:
                    on_back()
        
        status_emoji = "📢" if not v.get("is_draft") else "📝"
        status_text = "Published" if not v.get("is_draft") else "Draft"
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"{status_emoji} **{status_text}**")
        with col2:
            st.caption(f"🎭 **{v.get('mood', 'Reflective')}**")
        with col3:
            st.caption(f"📝 **{v['word_count']} words**")
        with col4:
            created = datetime.fromisoformat(v.get('created_at', '')).strftime('%b %d, %Y')
            st.caption(f"📅 **Created: {created}**")
        
        st.markdown("---")
        st.markdown(f"# {v['title']}")
        st.markdown(f"*Theme: {v['theme']}*")
        st.markdown("---")
        st.markdown(v['content'], unsafe_allow_html=True)
        
        if v.get('images'):
            st.markdown("---")
            st.markdown("### 📸 Images")
            cols = st.columns(3)
            for i, img in enumerate(v['images']):
                with cols[i % 3]:
                    if img.get('base64'):
                        st.image(f"data:image/jpeg;base64,{img['base64']}", use_column_width=True)
                    elif img.get('path') and os.path.exists(img['path']):
                        st.image(img['path'], use_column_width=True)
                    if img.get('caption'):
                        st.caption(img['caption'])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✏️ Edit", use_container_width=True, type="primary"):
                if on_edit:
                    on_edit(v['id'])
        
        with col2:
            if v.get("is_draft"):
                if st.button("📢 Publish Now", use_container_width=True):
                    v["is_draft"] = False
                    v["published_at"] = datetime.now().isoformat()
                    self.update_vignette(v["id"], v["title"], v["content"], v["theme"], v.get("mood"), v.get("images"))
                    st.success("🎉 Published!")
                    time.sleep(1)
                    st.rerun()
            else:
                if st.button("📝 Unpublish", use_container_width=True):
                    v["is_draft"] = True
                    self.update_vignette(v["id"], v["title"], v["content"], v["theme"], v.get("mood"), v.get("images"))
                    st.success("📝 Unpublished")
                    time.sleep(1)
                    st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", use_container_width=True):
                self.delete_vignette(v['id'])
                st.session_state.delete_success = True
                if on_back:
                    on_back()
                st.rerun()
