import requests

def generate_story(outline: list) -> str:
    formatted_outline = "\n".join(
        [
            f"Panel {item.get('panel', idx + 1)}: {item.get('title', '')} - "
            f"Scene: {item.get('scene_description', '')} - "
            f"Visual Prompt: {item.get('image_prompt', '')}"
            for idx, item in enumerate(outline)
        ]
    )

    prompt = f"""You are an expert comic book writer.

Given the following panel breakdown, write a comic-style story with engaging narration, scene context, and character dialogues for each panel.

Panel Outline:
{formatted_outline}

Guidelines:
- Structure each panel strictly beginning with the exact header format: **Panel X: Panel Title**
- Under each panel, format the contents into:
  **CAPTION:** (A brief, atmospheric description of the environment or setting)
  **NARRATION:** (Detailed narration describing character movements, feelings, and actions)
  **DIALOGUE:** (Character spoken lines formatted clearly, e.g., Hero: "Dialogue goes here")
- Maintain a cohesive narrative flow from Panel 1 to Panel 5.
"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }

    try:
        print("⚡ Sending story prompt to local Ollama (llama3.2)...")
        response = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=900)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        print("❌ Error generating story:", e)
        raise RuntimeError(f"Error generating story: {str(e)}")