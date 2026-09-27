import os
import json
import time
import uuid
import re
from PIL import Image
import io
import google.generativeai as genai

def sanitize_filename(prompt: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", prompt.lower())
    clean = re.sub(r"[-\s]+", "_", clean).strip("_")
    return f"{clean[:30]}_{uuid.uuid4().hex[:8]}.jpg"

def run_gemini_pipeline(full_prompt, style, api_key):
    """Executes the entire generation pipeline via Google's Gemini/Imagen APIs."""
    genai.configure(api_key=api_key)
    
    # --- NEW: Auto-detect the correct models for your specific API Key ---
    print("🔍 Locating available Gemini models...")
    
    # Find all models that can generate text
    text_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Pick the first one with 'flash' in the name, or fallback to the first available
    flash_model_name = next((m for m in text_models if 'flash' in m.lower()), None)
    if not flash_model_name:
        flash_model_name = text_models[0] if text_models else 'gemini-1.5-flash'
        
    print(f"✅ Auto-selected text model: {flash_model_name}")
    
    # --- Step 1: Outline Generation ---
    print(f"⚡ Sending outline prompt to {flash_model_name.split('/')[-1]}...")
    text_model = genai.GenerativeModel(flash_model_name)
    
    sys_instruction = "You are a comic planner. Return exactly 5 panels in a JSON array: [{\"panel\": 1, \"title\": \"...\", \"scene_description\": \"...\", \"image_prompt\": \"...\"}]"
    resp_outline = text_model.generate_content(f"{sys_instruction}\n\nSTORY: {full_prompt}")
    
    out_text = resp_outline.text.strip()
    if out_text.startswith("```json"): out_text = out_text[7:-3]
    elif out_text.startswith("```"): out_text = out_text[3:-3]
    
    try:
        outline = json.loads(out_text.strip())
    except:
        raise ValueError("Gemini failed to return valid JSON.")

    # --- Step 2: Story Generation ---
    print(f"⚡ Sending story prompt to {flash_model_name.split('/')[-1]}...")
    story_prompt = f"Write a comic script based on this outline. Use headers like **Panel 1: Title**. Include **CAPTION:**, **NARRATION:**, and **DIALOGUE:**.\n\n{json.dumps(outline)}"
    resp_story = text_model.generate_content(story_prompt)
    full_story = resp_story.text

    # --- Step 3: Image Generation ---
    # Find all models that can generate images
    image_models = [m.name for m in genai.list_models() if 'generateImages' in m.supported_generation_methods]
    imagen_model_name = next((m for m in image_models if 'imagen' in m.lower()), 'imagen-3.0-generate-001')
    
    print(f"🎨 Requesting illustrations from {imagen_model_name.split('/')[-1]}...")
    
    # The Image model expects the name without the "models/" prefix
    clean_imagen_name = imagen_model_name.replace("models/", "")
    image_model = genai.ImageGenerationModel(clean_imagen_name)
    
    output_dir = os.path.join("static", "panels")
    os.makedirs(output_dir, exist_ok=True)
    images = []

    for i, panel in enumerate(outline, start=1):
        t_start = time.time()
        enhanced_prompt = f"{style} style graphic novel comic panel, {panel['image_prompt']}"
        filename = sanitize_filename(enhanced_prompt)
        file_path = os.path.join(output_dir, filename)
        
        try:
            result = image_model.generate_images(
                prompt=enhanced_prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/jpeg"
            )
            
            # Extract bytes and save using Pillow
            image_bytes = result.images[0].image
            img = Image.open(io.BytesIO(image_bytes))
            img.save(file_path)
            
            images.append(f"static/panels/{filename}")
            print(f"   🖼️ Panel {i} drawn in {time.time() - t_start:.1f}s")
        except Exception as e:
            print(f"❌ Gemini Image Gen Failed for Panel {i}: {e}")
            images.append("") # Appends blank to prevent pipeline crash

    return outline, full_story, images