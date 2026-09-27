import os
import re
import uuid
import gc
import requests
import torch
from diffusers import AutoPipelineForText2Image
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def sanitize_filename(prompt: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", prompt.lower())
    clean = re.sub(r"[-\s]+", "_", clean).strip("_")
    return f"{clean[:30]}_{uuid.uuid4().hex[:8]}.png"

def unload_ollama():
    """Forces Ollama to drop Llama 3.2 from RAM to make room for image generation."""
    try:
        print("🧹 Evicting Llama 3.2 from RAM...")
        requests.post(
            "http://127.0.0.1:11434/api/generate", 
            json={"model": "llama3.2", "keep_alive": 0}, 
            timeout=5
        )
    except:
        pass

def generate_image(prompt: str, filename: str = None) -> str:
    if not filename:
        filename = sanitize_filename(prompt)

    output_dir = os.path.join("static", "panels")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)

    unload_ollama()
    
    try:
        print(f"🎨 Loading SD-Turbo to CPU for: {prompt[:40]}...")
        
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo",
            cache_dir="/home/kaartic/.cache/huggingface/hub",  # Forces root to use your downloaded files
            local_files_only=True,
            safety_checker=None,
            requires_safety_checker=False
        )
        pipe.to("cpu")
        
        # 1. Force a traditional, physical media style
        enhanced_prompt = (
            f"vintage 1990s comic book scan, rough ink lines, heavy crosshatching, "
            f"halftone print dots, traditional hand-drawn media, {prompt}"
        )
        
        # 2. Increase steps to 3 for better texture (Scale must remain at 0.0)
        image = pipe(
            prompt=enhanced_prompt, 
            num_inference_steps=3, 
            guidance_scale=0.0
        ).images[0]
        
        image.save(file_path)
        
        del pipe
        gc.collect()
        
        return f"static/panels/{filename}"
        
    except Exception as e:
        print(f"❌ Local image generation failed: {e}")
        return ""