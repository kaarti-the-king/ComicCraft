import os
import time
import json
import threading
import traceback
import psutil
import dotenv
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.exporters import save_pdf
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout

# Load existing environment variables
dotenv.load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

CANCEL_FLAG = False
HISTORY_FILE = "prompt_history.json"

class HardwareMonitor:
    def __init__(self):
        self.running = False
        self.max_temps = {}
        self.start_energy = self._get_energy_uj()
        self.end_energy = 0
        self._thread = None

    def _get_energy_uj(self):
        """Reads Intel RAPL energy consumption in microjoules."""
        try:
            with open("/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj", "r") as f:
                return int(f.read().strip())
        except Exception:
            return None

    def _poll_temps(self):
        """Background thread that checks temps every 1 second."""
        while self.running:
            try:
                temps = psutil.sensors_temperatures()
                for name, entries in temps.items():
                    for entry in entries:
                        sensor_name = f"{name} {entry.label}".strip()
                        if sensor_name not in self.max_temps:
                            self.max_temps[sensor_name] = entry.current
                        else:
                            self.max_temps[sensor_name] = max(self.max_temps[sensor_name], entry.current)
            except Exception:
                pass
            time.sleep(1)

    def start(self):
        self.running = True
        self.start_energy = self._get_energy_uj()
        self._thread = threading.Thread(target=self._poll_temps, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.end_energy = self._get_energy_uj()

    def get_report(self):
        report = []
        if self.start_energy is not None and self.end_energy is not None:
            joules = abs(self.end_energy - self.start_energy) / 1_000_000.0
            watt_hours = joules / 3600.0
            report.append(f" ⚡ Total Energy Consumed : {joules:.2f} Joules ({watt_hours:.4f} Wh)")
        else:
            report.append(" ⚡ Total Energy Consumed : [Hidden by OS - Run Uvicorn with 'sudo' to unlock]")

        report.append(" 🌡️  Max Temperatures Reached:")
        if not self.max_temps:
            report.append("     [No temperature sensors detected by OS]")
        else:
            for sensor, temp in self.max_temps.items():
                if temp > 0: 
                    report.append(f"     - {sensor} : {temp}°C")
        
        return "\n".join(report)


class PromptRequest(BaseModel):
    prompt: str
    character_name: str
    setting: str
    tone: str
    style: str

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Check if a key is already saved in the backend
    has_key = bool(os.getenv("GEMINI_API_KEY"))
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"has_gemini_key": has_key}
    )

@router.post("/cancel")
async def cancel_generation():
    global CANCEL_FLAG
    CANCEL_FLAG = True
    return {"message": "Cancellation requested"}

@router.get("/history")
async def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

@router.post("/generate", response_class=HTMLResponse)
async def generate_comic(
    request: Request,
    prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    style: str = Form(...),
    pipeline: str = Form("local"),
    gemini_key: str = Form(""),
):
    global CANCEL_FLAG
    CANCEL_FLAG = False  

    try:
        # --- Handle .env API Key Storage ---
        if gemini_key.strip():
            env_file = ".env"
            if not os.path.exists(env_file):
                open(env_file, 'a').close()
            dotenv.set_key(env_file, "GEMINI_API_KEY", gemini_key.strip())
            os.environ["GEMINI_API_KEY"] = gemini_key.strip()
            print("🔑 New Gemini API Key saved to .env file.")
        
        active_key = os.getenv("GEMINI_API_KEY")

        # --- Save Prompt to History ---
        history_entry = {"prompt": prompt, "character": character_name, "pipeline": pipeline, "time": time.strftime("%Y-%m-%d %H:%M")}
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        history.insert(0, history_entry)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[:10], f)
        # -----------------------------------

        monitor = HardwareMonitor()
        monitor.start()
        overall_start = time.time()
        print(f"\n[{time.strftime('%X')}] 🚀 STARTING COMIC GENERATION ({pipeline.upper()} PIPELINE)...")
        
        full_prompt = (
            f"{prompt}\n"
            f"The main character is {character_name}. "
            f"The setting is a {setting}. "
            f"The tone is {tone}. The art style is {style}."
        )

        if pipeline == "gemini":
            if not active_key:
                raise ValueError("Gemini API Key is required but was not found in the .env file or form input.")
            
            from app.gemini_cloud import run_gemini_pipeline
            outline, full_story, images = run_gemini_pipeline(full_prompt, style, active_key)
            if CANCEL_FLAG: raise InterruptedError("Generation cancelled by user.")
            
        else:
            print("⏳ Generating outline (Local)...")
            outline = generate_outline(full_prompt)
            if isinstance(outline, dict): outline = [outline]
            if not isinstance(outline, list): outline = []
            while len(outline) < 5:
                idx = len(outline) + 1
                outline.append({"panel": idx, "title": f"Scene {idx}", "scene_description": "...", "image_prompt": f"Animal in {setting}"})
            outline = outline[:5] 
            
            if CANCEL_FLAG: raise InterruptedError("Generation cancelled by user.")

            print("⏳ Generating story (Local)...")
            full_story = generate_story(outline)
            
            if CANCEL_FLAG: raise InterruptedError("Generation cancelled by user.")

            print("⏳ Generating images (Local)...")
            images = []
            for i, panel in enumerate(outline, start=1):
                if CANCEL_FLAG: raise InterruptedError("Generation cancelled by user.")
                img_path = generate_image(panel["image_prompt"])
                images.append(img_path)

        layout = build_comic_layout(images, full_story, outline)
        pdf_path = save_pdf(layout)
        web_pdf_path = "/" + pdf_path.replace("\\", "/")

        overall_end = time.time()
        total_duration = overall_end - overall_start
        monitor.stop()

        print("\n" + "="*55)
        print(f" ⏱️  {pipeline.upper()} PERFORMANCE REPORT")
        print("="*55)
        print(f" 🚀 TOTAL TIME          : {total_duration/60:.2f} min ({total_duration:.1f}s)")
        print("-" * 55)
        print(monitor.get_report())
        print("="*55 + "\n")

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={"layout": layout, "pdf_path": web_pdf_path},
        )

    except Exception as e:
        if 'monitor' in locals(): monitor.stop()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-comic/json")
async def generate_comic_json(payload: PromptRequest):
    raise HTTPException(status_code=501, detail="Not implemented with dual pipelines yet.")

@router.get("/export-success", response_class=HTMLResponse)
async def export_success(request: Request, pdf_path: str = ""):
    return templates.TemplateResponse(request=request, name="export_success.html", context={"pdf_path": pdf_path})