from fastapi import FastAPI, UploadFile, File
from PIL import Image
import io
import sys
import os
import importlib.util
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load the pipeline
def load_module(name, path):
    module_dir = os.path.dirname(os.path.abspath(path))
    if module_dir in sys.path:
        sys.path.remove(module_dir)
    sys.path.insert(0, module_dir)
    for key in list(sys.modules.keys()):
        if key in ("myunet", "dataset", "loader"):
            del sys.modules[key]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def convert_to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    return obj


BASE = os.path.dirname(os.path.abspath(__file__))
pipeline = load_module("pipeline", os.path.join(BASE, "../main-model/main.py"))


@app.get("/")
def home():
    return {"status": "running"}

@app.post("/analyse")
async def analyse(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")
    
    cord_instances, polygons = pipeline.run_pipeline(img)
    output = pipeline.calculate_outputs(cord_instances, polygons)
    
    return {
        "diagnostic": str(output["diagnostic"]),
        "number_of_cords": int(output["number_of_cords"]),
        "sua": bool(output["sua"]),
        "confidence": float(output["confidence"]),
        "polygons": convert_to_serializable(output["polygons"])
    }

