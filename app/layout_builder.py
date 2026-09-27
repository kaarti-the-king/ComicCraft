import re

def build_comic_layout(image_paths: list, full_story: str, outline: list) -> list:
    blocks = re.split(r'(?i)(?:\n|^)\s*#*\s*\**\s*Panel\s*\d+.*?(?:\n|$)', full_story)
    story_panels = [b.strip() for b in blocks if b.strip()]

    layout = []
    for idx, (image, panel_info) in enumerate(zip(image_paths, outline), start=1):
        if (idx - 1) < len(story_panels):
            text_content = story_panels[idx - 1]
        else:
            text_content = panel_info.get("scene_description", "The adventure continues...")
            
        # Strip headers
        text_content = text_content.replace("**CAPTION:**", "").replace("**NARRATION:**", "\n").replace("**DIALOGUE:**", "\n")
        
        # NEW: Forcefully remove all remaining asterisks used for bold/italic markdown
        text_content = re.sub(r'\*+', '', text_content)

        layout.append({
            "panel": idx,
            "title": panel_info.get("title", f"Panel {idx}").replace("**", ""),
            "image_path": image,
            "text": text_content.strip(),
            "scene_description": panel_info.get("scene_description", "")
        })

    return layout