#!/usr/bin/env python3
"""
AgriGuard Model Exporter: PyTorch MobileNetV2 -> ONNX
Converts `ml/outputs/agriguard_model.pt` to `ml/outputs/agriguard_model.onnx`
with input shape (1, 3, 224, 224), opset 17.
"""

import os
import json
import torch
import torchvision.models as models
from pathlib import Path


def export_to_onnx():
    base_dir = Path(__file__).resolve().parent.parent
    
    # Locate checkpoint
    model_paths = [
        base_dir / "ml" / "outputs" / "agriguard_model.pt",
        base_dir / "agriguard_model.pt",
    ]
    ckpt_path = None
    for p in model_paths:
        if p.exists():
            ckpt_path = p
            break
            
    if not ckpt_path:
        raise FileNotFoundError("Could not find agriguard_model.pt checkpoint.")

    print(f"Loading PyTorch checkpoint from: {ckpt_path}")
    ckpt = torch.load(ckpt_path, map_location="cpu")
    
    # Load class names
    if "class_names" in ckpt:
        class_names = ckpt["class_names"]
    else:
        class_names_path = base_dir / "ml" / "outputs" / "class_names.json"
        if not class_names_path.exists():
            class_names_path = base_dir / "class_names.json"
        with open(class_names_path, "r", encoding="utf-8") as f:
            class_names = json.load(f)

    num_classes = len(class_names)
    print(f"Number of classes: {num_classes}")

    # Build model architecture (MobileNetV2)
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(in_features, num_classes)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    # Output paths
    output_dir = base_dir / "ml" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "agriguard_model.onnx"

    # Dummy input (1, 3, 224, 224)
    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=False)

    print(f"Exporting to ONNX format (opset 17)...")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )

    print(f"ONNX export successful: {onnx_path} (Size: {os.path.getsize(onnx_path) / (1024*1024):.2f} MB)")
    return str(onnx_path)


if __name__ == "__main__":
    export_to_onnx()
