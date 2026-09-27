# 🦸‍♂️ ComicCraft

> **Note:** Conceptualized and developed as part of the ALGORHYTHM '26 technical event.

**ComicCraft** is an intelligent, dual-pipeline web application that transforms simple text prompts into fully illustrated, 5-panel comic books in minutes. Built with a responsive FastAPI backend, ComicCraft allows users to seamlessly toggle between a fully offline local hardware engine and a lightning-fast Google Cloud API pipeline.

---

## ✨ Key Features

* 🔀 **Dual-Pipeline Architecture:** Switch effortlessly between **Local Hardware** (Llama 3.2 + SD-Turbo) for offline privacy, or **Google Cloud** (Gemini 1.5 Flash + Imagen 3) for state-of-the-art speed and quality.
* 🎨 **Dynamic Customization:** Control the setting, tone, and art style (Anime, Pixel Art, Comic Book, etc.) via an intuitive web UI.
* 🔒 **Smart API Management:** Google AI Studio API keys are entered directly through the web interface and securely saved to a local `.env` file—never exposed or hardcoded.
* 📊 **Hardware Monitoring:** Tracks real-time CPU temperatures and Intel RAPL energy consumption (in Joules/Wh) during local generation runs.
* ⏳ **Asynchronous Processing:** Bypasses standard browser timeouts for heavy ML workloads using background fetch rendering.
* 📖 **Instant PDF Export:** Automatically stitches the generated script, captions, and panel illustrations into a downloadable PDF graphic novel.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, FastAPI, Uvicorn |
| **Frontend** | HTML5, CSS3, Vanilla JS, Jinja2 Templates |
| **Cloud AI Engine** | Google Generative AI SDK (Gemini 1.5 Flash / Imagen 3) |
| **Local AI Engine** | HuggingFace Diffusers, Transformers, Ollama |
| **Utilities** | Pillow (Image Processing), psutil (Hardware Monitoring), python-dotenv |

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/kaarti-the-king/ComicCraft.git](https://github.com/kaarti-the-king/ComicCraft.git)
cd ComicCraft
```

### 2. Set Up a Virtual Environment
It is highly recommended to isolate the dependencies.
```bash
python3 -m venv comiccraft-env
source comiccraft-env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Application
To enable the Intel RAPL energy consumption monitor during local generation, the server requires root privileges. Run the app using `sudo` and explicitly point to your virtual environment's Python executable:
```bash
sudo $(which python) -m uvicorn app.main:app --reload
```
*The app will now be live at `http://127.0.0.1:8000`.*

---

## 🎮 How to Use

1. **Open the Web Interface:** Navigate to `http://127.0.0.1:8000` in your browser.
2. **Select Your Engine:**
   * **Google Cloud:** Requires a free Gemini API key (from Google AI Studio). Paste it into the UI once, and it will be permanently saved to your local `.env` file.
   * **Local Hardware:** Requires Ollama to be running locally with the necessary models downloaded.
3. **Craft Your Story:** Enter a prompt, name your main character, and use the **Advanced Settings** dropdown to fine-tune the artistic style and tone.
4. **Generate:** Click "Generate Comic". You can monitor the live hardware and pipeline progress directly in your terminal.
5. **Read:** Once complete, the browser will seamlessly transition to the preview page where you can read and download your newly minted PDF comic!

---

## 🧠 Pipeline Architecture

### The Cloud Pipeline (Gemini)
ComicCraft utilizes a custom auto-detect function via the Google Generative AI SDK to ensure API routing stability (preventing `404 NOT_FOUND` errors). It queries the `v1beta` endpoint for the most recent compatible Flash and Imagen models assigned to the user's API key. 
1. **Gemini 1.5 Flash** structures a JSON 5-panel outline.
2. **Gemini 1.5 Flash** expands the JSON into a full narrative script with dialogue.
3. **Imagen 3** generates text-accurate, 1:1 aspect ratio comic illustrations.

### The Local Pipeline (Ollama / HuggingFace)
Designed for offline capability and data privacy. 
1. **Llama 3.2** (via Ollama API) generates the story and scene directions.
2. **SD-Turbo** (Stable Diffusion) synthesizes the illustrations using local CPU/GPU compute, heavily monitored by `psutil` to track thermal limits and energy usage.
