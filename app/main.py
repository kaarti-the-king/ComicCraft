import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import router

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    description="Automated panel-by-panel comic story and illustration generator powered by Gemini and Stable Diffusion.",
    version="1.0.0",
)

# Cross-Origin configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required runtime folders exist
os.makedirs(os.path.join("static", "panels"), exist_ok=True)
os.makedirs(os.path.join("static", "exports"), exist_ok=True)
os.makedirs(os.path.join("static", "fonts"), exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount route handlers
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)