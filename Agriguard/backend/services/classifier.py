import os
import json
import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
import onnxruntime as ort

from backend.config import settings

logger = logging.getLogger("agriguard.classifier")


def parse_class_name(class_name: str) -> Tuple[str, str]:
    """
    Parses a raw class name like 'Tomato___Early_blight' or 'Grape___Esca_(Black_Measles)'
    into human-friendly (crop, disease_name).
    """
    if "___" in class_name:
        crop_part, disease_part = class_name.split("___", 1)
    else:
        crop_part, disease_part = "Plant", class_name

    crop = crop_part.replace("_", " ").replace("(", " (").replace("  ", " ").strip()
    disease = disease_part.replace("_", " ").strip()
    if disease.endswith("_"):
        disease = disease[:-1].strip()
    return crop, disease


def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Pure NumPy + Pillow implementation of standard Torchvision MobileNetV2 preprocessing:
    1. Convert to RGB
    2. Resize to (224, 224) using Bilinear interpolation
    3. Scale pixel values to [0.0, 1.0]
    4. Normalize with ImageNet mean and std:
       mean = [0.485, 0.456, 0.406]
       std  = [0.229, 0.224, 0.225]
    5. Transpose (H, W, C) -> (1, C, H, W) with float32 dtype
    """
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    # Resize matching torchvision Resize((224, 224), interpolation=InterpolationMode.BILINEAR)
    resized = image.resize((224, 224), resample=Image.Resampling.BILINEAR)
    
    # Convert to float32 numpy array in [0, 1]
    img_arr = np.asarray(resized, dtype=np.float32) / 255.0
    
    # ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (img_arr - mean) / std
    
    # Shape: (224, 224, 3) -> (3, 224, 224) -> (1, 3, 224, 224)
    tensor = np.transpose(normalized, (2, 0, 1))[np.newaxis, :, :, :].astype(np.float32)
    return tensor


class DiseaseClassifier:
    """Production ONNX Runtime CPU disease classifier (ultra-low memory footprint)."""

    def __init__(self):
        self.session = None
        self.input_name = None
        self.class_names: List[str] = []
        self.load_model()

    @property
    def model(self):
        return self.session

    def _resolve_path(self, target_path: str) -> str:
        candidates = [
            Path(target_path),
            Path(target_path).with_suffix(".onnx"),
            Path.cwd() / target_path,
            Path.cwd() / Path(target_path).with_suffix(".onnx"),
            Path.cwd() / "ml" / "outputs" / Path(target_path).name,
            Path.cwd() / "ml" / "outputs" / Path(target_path).with_suffix(".onnx").name,
            Path.cwd() / Path(target_path).name,
            Path.cwd() / Path(target_path).with_suffix(".onnx").name,
        ]
        for c in candidates:
            if c.exists() and (c.suffix == ".onnx" or "class_names" in str(c)):
                return str(c.resolve())
            elif c.exists() and target_path.endswith(".json"):
                return str(c.resolve())
        # Fallback to any existing candidate
        for c in candidates:
            if c.exists():
                return str(c.resolve())
        raise FileNotFoundError(f"Could not locate model file at {target_path} (checked {candidates})")


    def load_model(self):
        # 1. Load class names
        class_names_path = self._resolve_path(settings.CLASS_NAMES_PATH)
        with open(class_names_path, "r", encoding="utf-8") as f:
            self.class_names = json.load(f)
        num_classes = len(self.class_names)
        logger.info(f"Loaded {num_classes} classes from {class_names_path}")

        # 2. Load ONNX model
        model_path = self._resolve_path(settings.MODEL_PATH)
        logger.info(f"Initializing ONNX Runtime CPU session from: {model_path}")
        
        # Configure single-thread execution for low memory & CPU optimization
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.session = ort.InferenceSession(
            model_path,
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        self.input_name = self.session.get_inputs()[0].name
        logger.info(f"ONNX session ready with input node '{self.input_name}'.")

    def predict(self, image: Image.Image) -> List[Dict[str, Any]]:
        """
        Runs inference on a PIL Image using ONNX Runtime and returns top-3 predictions.
        """
        if self.session is None:
            self.load_model()

        # Preprocess to (1, 3, 224, 224)
        input_tensor = preprocess_image(image)

        # Run ONNX inference
        raw_outputs = self.session.run(None, {self.input_name: input_tensor})
        logits = raw_outputs[0][0]  # Shape (num_classes,)

        # Numerically stable softmax
        exp_logits = np.exp(logits - np.max(logits))
        probabilities = exp_logits / np.sum(exp_logits)

        # Top-3 indices
        k = min(3, len(self.class_names))
        top_indices = np.argsort(probabilities)[::-1][:k]

        results = []
        for idx in top_indices:
            raw_class = self.class_names[idx]
            crop, disease = parse_class_name(raw_class)
            prob = float(probabilities[idx])
            results.append({
                "class_id": raw_class,
                "crop": crop,
                "disease_name": disease,
                "probability": round(prob, 4)
            })

        return results

    def get_supported_crops(self) -> List[str]:
        crops = set()
        for c in self.class_names:
            crop, _ = parse_class_name(c)
            crops.add(crop)
        return sorted(list(crops))


# Global singleton instance
classifier = DiseaseClassifier()
