"""
Image Manager Module - COMPLETE WORKING VERSION
Upload photos with stories
"""

import streamlit as st
import os
import json
import uuid
from datetime import datetime
from PIL import Image
import base64
import time

# Image configuration
IMAGE_CONFIG = {
    "max_size_mb": 5,
    "allowed_formats": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
    "max_width": 1920,
    "max_height": 1080,
    "thumbnail_size": (400, 400)
}

def get_user_image_folder(user_id):
    """Get or create user's image folder"""
    folder_path = f"user_images/{user_id}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_session_image_folder(user_id, session_id):
    """Get or create session-specific image folder"""
    folder_path = f"user_images/{user_id}/session_{session_id}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_image_metadata(user_id, session_id, image_info):
    """Save image metadata to JSON file"""
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    
    try:
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        if str(session_id) not in metadata:
            metadata[str(session_id)] = []
        
        metadata[str(session_id)].append(image_info)
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving image metadata: {e}")
        return False

def get_session_images(user_id, session_id):
    """Get all images for a specific session"""
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    if not os.path.exists(metadata_file):
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
        return []
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        session_key = str(session_id)
        if session_key in metadata:
            session_images = metadata[session_key]
            if isinstance(session_images, list):
                return session_images
            else:
                metadata[session_key] = []
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                return []
        return []
    except:
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
        return []

def resize_image_if_needed(image, max_width=1920, max_height=1080):
    """Resize image if it's too large"""
    width, height = image.size
    
    if width > max_width or height > max_height:
        ratio = min(max_width/width, max_height/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image

def create_thumbnail(image, size=(400, 400)):
    """Create thumbnail from image"""
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image

def save_uploaded_image(uploaded_file, user_id, session_id, story_text=""):
    """Process and save an uploaded image WITH STORY"""
    try:
        max_size_bytes = IMAGE_CONFIG["max_size_mb"] * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            return {"success": False, "error": f"Image too large. Max size: {IMAGE_CONFIG['max_size_mb']}MB"}
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext not in IMAGE_CONFIG["allowed_formats"]:
            return {"success": False, "error": f"Invalid format. Allowed: {', '.join(IMAGE_CONFIG['allowed_formats'])}"}
        
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = uploaded_file.name
        safe_filename = f"{timestamp}_{unique_id}.{file_ext}"
        
        session_folder = get_session_image_folder(user_id, session_id)
        
        image = Image.open(uploaded_file)
        image = resize_image_if_needed(image, IMAGE_CONFIG["max_width"], IMAGE_CONFIG["max_height"])
        
        original_path = os.path.join(session_folder, f"original_{safe_filename}")
        image.save(original_path, quality=95)
        
        thumbnail = create_thumbnail(image.copy(), IMAGE_CONFIG["thumbnail_size"])
        thumbnail_path = os.path.join(session_folder, f"thumb_{safe_filename}")
        thumbnail.save(thumbnail_path, quality=85)
        
        image_info = {
            "id": unique_id,
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "story": story_text,
            "upload_date": datetime.now().isoformat(),
            "session_id": session_id,
            "file_size_kb": uploaded_file.size / 1024,
            "dimensions": f"{image.width}x{image.height}",
            "paths": {
                "original": original_path,
                "thumbnail": thumbnail_path
            }
        }
        
        save_image_metadata(user_id, session_id, image_info)
        
        return {
            "success": True,
            "image_info": image_info,
            "message": f"Photo + story saved!"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error: {str(e)}"}

def delete_image(user_id, session_id, image_id):
    """Delete an image and its metadata"""
    try:
        metadata_file = f"user_images/{user_id}/image_metadata.json"
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            session_key = str(session_id)
            if session_key in metadata:
                # Find and remove image
                for i, img in enumerate(metadata[session_key]):
                    if img["id"] == image_id:
                        # Delete image files
                        if os.path.exists(img["paths"]["original"]):
                            os.remove(img["paths"]["original"])
                        if os.path.exists(img["paths"]["thumbnail"]):
                            os.remove(img["paths"]["thumbnail"])
                        
                        # Remove from metadata
                        metadata[session_key].pop(i)
                        
                        # If session has no more images, remove session entry
                        if not metadata[session_key]:
                            del metadata[session_key]
                        
                        # Save updated metadata
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        
                        return {"success": True, "message": "Image deleted successfully"}
        
        return {"success": False, "error": "Image not found"}
    except Exception as e:
        return {"success": False, "error": f"Error deleting image: {str(e)}"}

def get_image_data_url(image_path):
    """Convert image to data URL for HTML display"""
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            extension = image_path.split('.')[-1].lower()
            mime_type = f"image/{'jpeg' if extension in ['jpg', 'jpeg'] else extension}"
            return f"data:{mime_type};base64,{encoded}"
    except:
        return None

def display_image_gallery(user_id, session_id, columns=3):
    """Display images in a gallery layout - SHOWS STORIES"""
    images = get_session_images(user_id, session_id)
    
    if not images:
        st.info("No photos in this session yet.")
        return []
    
    st.subheader(f"📸 Photos in This Session ({len(images)})")
    
    cols = st.columns(columns)
    
    for idx, img_info in enumerate(images):
        col_idx = idx % columns
        
        with cols[col_idx]:
            if os.path.exists(img_info["paths"]["thumbnail"]):
                data_url = get_image_data_url(img_info["paths"]["thumbnail"])
                if data_url:
                    st.markdown(
                        f'<div style="text-align: center;">'
                        f'<img src="{data_url}" style="max-width: 100%; max-height: 200px; border-radius:8px; margin: 0 auto;">'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            
            st.caption(f"📁 {img_info['original_filename']}")
            
            # SHOW THE STORY
            if img_info.get('story'):
                with st.expander(f"📖 Story about this photo", expanded=False):
                    st.write(img_info['story'])
            else:
                st.caption("No story added yet")
            
            # Delete button
            if st.button("🗑️ Delete", key=f"delete_{session_id}_{img_info['id']}", use_container_width=True):
                result = delete_image(user_id, session_id, img_info["id"])
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["error"])
            
            st.divider()
    
    return images

def image_upload_interface(user_id, session_id):
    """Upload interface - ONE PHOTO + STORY"""
    st.markdown("### 📤 Add Photo + Story to This Session")
    
    uploaded_file = st.file_uploader(
        "Choose a photo",
        type=IMAGE_CONFIG["allowed_formats"],
        accept_multiple_files=False,
        key=f"image_upload_{session_id}_{int(time.time())}"
    )
    
    if uploaded_file:
        # THIS IS THE TEXT BOX THAT SAYS "Write a story about this image"
        story_text = st.text_area(
            "📝 **Write a story about this image:**",
            placeholder="Tell the story behind this photo. Who's in it? When was it taken? What memories does it bring back?",
            key=f"story_{session_id}_{uploaded_file.name}",
            height=150
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Upload Photo + Story", key=f"upload_{session_id}", type="primary", use_container_width=True):
                if not story_text.strip():
                    st.error("Please write a story about this photo!")
                    return
                
                result = save_uploaded_image(uploaded_file, user_id, session_id, story_text)
                if result["success"]:
                    st.success("✅ Photo + story saved to this session!")
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
        
        with col2:
            if st.button("🔄 Cancel", key=f"cancel_{session_id}", use_container_width=True):
                st.rerun()

def get_images_for_prompt(user_id, session_id):
    """Get images formatted for AI prompt"""
    images = get_session_images(user_id, session_id)
    
    if not images:
        return ""
    
    prompt_text = "\n\n📸 **USER HAS PHOTOS IN THIS SESSION:**\n"
    
    for img in images:
        prompt_text += f"- {img['original_filename']}"
        if img.get('story'):
            prompt_text += f" - {img['story'][:100]}"
        prompt_text += "\n"
    
    return prompt_text

def get_images_for_session(user_id, session_id):
    """Get images + stories for a session"""
    return get_session_images(user_id, session_id)

def get_total_user_images(user_id):
    """Get total number of images across all sessions"""
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            total = 0
            for session_id, images in metadata.items():
                total += len(images)
            return total
        except:
            pass
    
    return 0
