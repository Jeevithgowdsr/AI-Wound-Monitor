from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import base64
from logic import analyze_wound, get_detailed_report

app = FastAPI()

# Allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, set your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # Read image
    image_bytes = await file.read()
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Process image
    processed_image, wound_area, color_analysis = analyze_wound(pil_image)
    report = get_detailed_report(wound_area, color_analysis)

    # Convert processed image to base64
    buffered = io.BytesIO()
    processed_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return {
        "healing_score": report["healing_score"],
        "wound_area": report["wound_area"],
        "infection_risk": report["infection_risk"],
        "description": report["description"],
        "processed_image": f"data:image/png;base64,{img_str}"
    }
