import json
import requests

def generate_outline(user_prompt: str) -> list:
    prompt = f"""You are a professional AI comic planner.
Your task is to generate a JSON array containing exactly 5 panel descriptions based on the story idea below.

STORY: "{user_prompt}"

You MUST return a JSON list (array) of objects. Use this EXACT format:
[
  {{
    "panel": 1,
    "title": "Title 1",
    "scene_description": "Description 1",
    "image_prompt": "Prompt 1"
  }},
  {{
    "panel": 2,
    "title": "Title 2",
    "scene_description": "Description 2",
    "image_prompt": "Prompt 2"
  }}
]

Respond ONLY with the valid JSON array. Do not include markdown formatting.
"""
    
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }

    try:
        print("⚡ Sending outline prompt to local Ollama (llama3.2)...")
        response = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=600)
        response.raise_for_status()
        
        output_text = response.json().get("response", "").strip()
        panel_data = json.loads(output_text)

        if isinstance(panel_data, dict) and "panel" in panel_data:
            panel_data = [panel_data]
        elif isinstance(panel_data, dict):
            key = list(panel_data.keys())[0]
            panel_data = panel_data[key]
            if isinstance(panel_data, dict) and "panel" in panel_data:
                panel_data = [panel_data]

        if not isinstance(panel_data, list):
            raise ValueError("Ollama response could not be coerced into a list.")

        return panel_data

    except Exception as e:
        print("❌ Unexpected Error in generate_outline:", e)
        raise RuntimeError(f"Outline generation failed: {str(e)}")