"""
Image Manager - RESTORED WORKING VERSION
"""

import streamlit as st
import os
import json
import uuid
from datetime import datetime
from PIL import Image
import base64
import time

IMAGE_CONFIG = {
    "max_size_mb": 5,
    "allowed_formats": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
    "max_width": 1920,
    "max_height": 1080,
    "thumbnail_size": (400, 400)
}

def get_user_image_folder(user_id):
    folder_path = f"user_images/{user_id}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def get_session_image_folder(user_id, session_id):
    folder_path = f"user_images/{user_id}/session_{session_id}"
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_image_metadata(user_id, session_id, image_info):
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
    except:
        return False

def get_session_images(user_id, session_id):
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    if not os.path.exists(metadata_file):
        with open(metadata_file, 'w') as f:
            json.dump({}, f)
        return []
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if str(session_id) in metadata:
            return metadata[str(session_id)]
        return []
    except:
        return []

def resize_image_if_needed(image, max_width=1920, max_height=1080):
    width, height = image.size
    if width > max_width or height > max_height:
        ratio = min(max_width/width, max_height/height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

def create_thumbnail(image, size=(400, 400)):
    image.thumbnail(size, Image.Resampling.LANCZOS)
    return image

def save_uploaded_image(uploaded_file, user_id, session_id, description=""):
    try:
        max_size_bytes = IMAGE_CONFIG["max_size_mb"] * 1024 * 1024
        if uploaded_file.size > max_size_bytes:
            return {"success": False, "error": "Image too large"}
        
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext not in IMAGE_CONFIG["allowed_formats"]:
            return {"success": False, "error": "Invalid format"}
        
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
            "description": description,
            "upload_date": datetime.now().isoformat(),
            "session_id": session_id,
            "dimensions": f"{image.width}x{image.height}",
            "paths": {
                "original": original_path,
                "thumbnail": thumbnail_path
            }
        }
        
        save_image_metadata(user_id, session_id, image_info)
        
        return {"success": True, "image_info": image_info}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_image(user_id, session_id, image_id):
    try:
        metadata_file = f"user_images/{user_id}/image_metadata.json"
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if str(session_id) in metadata:
                for i, img in enumerate(metadata[str(session_id)]):
                    if img["id"] == image_id:
                        if os.path.exists(img["paths"]["original"]):
                            os.remove(img["paths"]["original"])
                        if os.path.exists(img["paths"]["thumbnail"]):
                            os.remove(img["paths"]["thumbnail"])
                        
                        metadata[str(session_id)].pop(i)
                        if not metadata[str(session_id)]:
                            del metadata[str(session_id)]
                        
                        with open(metadata_file, 'w') as f:
                            json.dump(metadata, f, indent=2)
                        return {"success": True}
        return {"success": False}
    except:
        return {"success": False}

def get_image_data_url(image_path):
    try:
        with open(image_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            extension = image_path.split('.')[-1].lower()
            mime_type = f"image/{'jpeg' if extension in ['jpg', 'jpeg'] else extension}"
            return f"data:{mime_type};base64,{encoded}"
    except:
        return None

def display_image_gallery(user_id, session_id, columns=3):
    images = get_session_images(user_id, session_id)
    if not images:
        st.info("No images in this session")
        return []
    
    cols = st.columns(columns)
    selected_images = []
    
    for idx, img in enumerate(images):
        col_idx = idx % columns
        with cols[col_idx]:
            if os.path.exists(img["paths"]["thumbnail"]):
                data_url = get_image_data_url(img["paths"]["thumbnail"])
                if data_url:
                    st.markdown(f'<img src="{data_url}" style="max-width:100%;max-height:150px;">', unsafe_allow_html=True)
            
            st.caption(img['original_filename'])
            if img.get('description'):
                st.caption(img['description'][:50])
            
            if st.checkbox("Select", key=f"select_{img['id']}"):
                selected_images.append(img)
    
    return selected_images

def image_upload_interface(user_id, session_id):
    with st.expander("📤 Upload Image"):
        uploaded_file = st.file_uploader(
            "Choose image",
            type=IMAGE_CONFIG["allowed_formats"],
            key=f"uploader_{session_id}"
        )
        
        if uploaded_file:
            description = st.text_area(
                "Write about this image:",
                placeholder="What's the story behind this photo?",
                key=f"desc_{session_id}",
                height=100
            )
            
            if st.button("Upload", key=f"btn_{session_id}"):
                result = save_uploaded_image(uploaded_file, user_id, session_id, description)
                if result["success"]:
                    st.success("Image uploaded!")
                    st.rerun()
                else:
                    st.error(result["error"])

def get_images_for_prompt(user_id, session_id):
    images = get_session_images(user_id, session_id)
    if not images:
        return ""
    
    prompt = "\n📸 User has images:\n"
    for img in images:
        prompt += f"- {img['original_filename']}"
        if img.get('description'):
            prompt += f": {img['description'][:100]}"
        prompt += "\n"
    return prompt

def get_total_user_images(user_id):
    metadata_file = f"user_images/{user_id}/image_metadata.json"
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            total = 0
            for images in metadata.values():
                total += len(images)
            return total
        except:
            pass
    return 0
