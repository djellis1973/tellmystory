"""
Image Manager Module for TellMyStory Biographer
Handles image uploads, storage, and integration with stories
"""

import streamlit as st
import os
import json
import shutil
from datetime import datetime
import uuid
from PIL import Image
import io
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
        # Load existing metadata
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # Initialize session entry if not exists
        if str(session_id) not in metadata:
            metadata[str(session_id)] = []
        
        # Add new image info
        metadata[str(session_id)].append(image_info)
        
        # Save back to file
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving image metadata: {e}")
        return False

def get_session_images(user_id, session_id):
    """Get all images for a specific session - FIXED FOR CORRUPTED FILE"""
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    
    # FIX: Ensure the directory and file exist
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    if not os.path.exists(metadata_file):
        # Create a valid empty JSON file
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
        return []
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        session_key = str(session_id)
        if session_key in metadata:
            # FIX: Ensure we return a list even if data is malformed
            session_images = metadata[session_key]
            if isinstance(session_images, list):
                return session_images
            else:
                # If data is not a list, reset it for this session
                metadata[session_key] = []
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                return []
        return []
    except (json.JSONDecodeError, IOError):
        # FIX: If file is corrupted, reset it
        print(f"Error loading metadata from {metadata_file}. Resetting file.")
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
        return []

def resize_image_if_needed(image, max_width=1920, max_height=1080):
    """Resize image if it's too large"""
    width, height = image.size
    
    if width > max_width or height > max_height:
        # Calculate new dimensions while maintaining aspect ratio
        ratio = min(max_width/width, max_height/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    return image

def create_thumbnail(image, size=(400, 400)):
    """Create thumbnail from image"""
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image

def save_uploaded_image(uploaded_file, user_id, session_id, description=""):
    """Process and save an uploaded image"""
    try:
        # Validate file size
        max_size_bytes = IMAGE_CONFIG["max_size_mb"] * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            return {"success": False, "error": f"Image too large. Max size: {IMAGE_CONFIG['max_size_mb']}MB"}
        
        # Validate file format
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext not in IMAGE_CONFIG["allowed_formats"]:
            return {"success": False, "error": f"Invalid format. Allowed: {', '.join(IMAGE_CONFIG['allowed_formats'])}"}
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = uploaded_file.name
        safe_filename = f"{timestamp}_{unique_id}.{file_ext}"
        
        # Get session folder
        session_folder = get_session_image_folder(user_id, session_id)
        
        # Open and process image
        image = Image.open(uploaded_file)
        
        # Resize if needed
        image = resize_image_if_needed(image, IMAGE_CONFIG["max_width"], IMAGE_CONFIG["max_height"])
        
        # Save original (resized if necessary)
        original_path = os.path.join(session_folder, f"original_{safe_filename}")
        image.save(original_path, quality=95)
        
        # Create and save thumbnail
        thumbnail = create_thumbnail(image.copy(), IMAGE_CONFIG["thumbnail_size"])
        thumbnail_path = os.path.join(session_folder, f"thumb_{safe_filename}")
        thumbnail.save(thumbnail_path, quality=85)
        
        # Create image info
        image_info = {
            "id": unique_id,
            "original_filename": original_filename,
            "saved_filename": safe_filename,
            "description": description,
            "upload_date": datetime.now().isoformat(),
            "session_id": session_id,
            "file_size_kb": uploaded_file.size / 1024,
            "dimensions": f"{image.width}x{image.height}",
            "paths": {
                "original": original_path,
                "thumbnail": thumbnail_path
            }
        }
        
        # Save metadata
        save_image_metadata(user_id, session_id, image_info)
        
        return {
            "success": True,
            "image_info": image_info,
            "message": f"Image uploaded successfully!"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error processing image: {str(e)}"}

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
    """Display images in a gallery layout - FIXED SIZE AND ERRORS"""
    images = get_session_images(user_id, session_id)
    
    if not images:
        st.info("No images uploaded for this session yet.")
        return []
    
    st.subheader(f"📸 Session Images ({len(images)})")
    
    # Create columns for gallery
    cols = st.columns(columns)
    
    selected_images = []
    
    for idx, img_info in enumerate(images):
        col_idx = idx % columns
        
        with cols[col_idx]:
            # Display thumbnail with FIXED MAXIMUM SIZE
            if os.path.exists(img_info["paths"]["thumbnail"]):
                data_url = get_image_data_url(img_info["paths"]["thumbnail"])
                if data_url:
                    # FIX: Properly sized images with centered alignment
                    st.markdown(
                        f'<div style="text-align: center;">'
                        f'<img src="{data_url}" style="max-width: 100%; max-height: 200px; width: auto; height: auto; border-radius:8px; margin: 0 auto;">'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            
            # Image info
            st.caption(f"📁 {img_info['original_filename']}")
            if img_info.get('description'):
                st.caption(f"💬 {img_info['description'][:50]}")
            
            # Select checkbox
            selected = st.checkbox(f"Select", key=f"select_img_{session_id}_{img_info['id']}")
            if selected:
                selected_images.append(img_info)
            
            # Delete button
            if st.button("🗑️", key=f"delete_{session_id}_{img_info['id']}", help="Delete this image"):
                result = delete_image(user_id, session_id, img_info["id"])
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["error"])
            
            st.divider()
    
    return selected_images

def image_upload_interface(user_id, session_id):
    """Streamlit interface for uploading images - ONE AT A TIME WITH DESCRIPTION"""
    with st.expander("📤 Upload Images to This Session", expanded=False):
        st.write("Add photos one at a time. Write about each photo as you upload it.")
        
        # SINGLE file uploader - ONE AT A TIME
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=IMAGE_CONFIG["allowed_formats"],
            accept_multiple_files=False,
            key=f"image_uploader_{session_id}_{int(time.time())}"  # Unique key
        )
        
        if uploaded_file:
            # Individual description for this ONE image
            description = st.text_area(
                "✍️ Write about this image:",
                placeholder="Tell the story behind this photo. Who's in it? When was it taken? What memories does it bring back?",
                key=f"img_desc_{session_id}_{uploaded_file.name}",
                height=100
            )
            
            # Upload button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📤 Upload This Image", key=f"upload_btn_{session_id}", type="primary"):
                    result = save_uploaded_image(uploaded_file, user_id, session_id, description)
                    if result["success"]:
                        st.success("✅ Image uploaded successfully!")
                        st.info("📝 Your story about this image has been saved.")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result['error']}")
            
            with col2:
                if st.button("🔄 Upload Another", key=f"another_btn_{session_id}"):
                    st.rerun()

def get_images_for_prompt(user_id, session_id):
    """Get images formatted for AI prompt - SIMPLIFIED"""
    images = get_session_images(user_id, session_id)
    
    if not images:
        return ""
    
    prompt_text = "\n\n📸 **USER HAS UPLOADED THESE PHOTOS:**\n"
    
    for img in images:
        prompt_text += f"- {img['original_filename']}"
        if img.get('description'):
            prompt_text += f" - {img['description']}"
        prompt_text += "\n"
    
    return prompt_text

def export_images_data(user_id, session_id):
    """Export image data for book generation"""
    images = get_session_images(user_id, session_id)
    
    if not images:
        return None
    
    export_data = []
    for img in images:
        # Create export-friendly version
        export_img = {
            "id": img["id"],
            "original_filename": img["original_filename"],
            "description": img.get("description", ""),
            "upload_date": img["upload_date"],
            "dimensions": img["dimensions"],
            "session_id": session_id
        }
        export_data.append(export_img)
    
    return export_data

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
