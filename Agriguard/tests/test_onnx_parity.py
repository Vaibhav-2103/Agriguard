import json
import pytest
import numpy as np
from PIL import Image
from pathlib import Path
import torch
import torchvision.transforms as transforms
import torchvision.models as models
import onnxruntime as ort

from backend.services.classifier import preprocess_image, parse_class_name


def test_pytorch_vs_onnx_parity():
    """
    Asserts exact prediction and probability parity between PyTorch MobileNetV2
    and ONNX Runtime inference on identical sample images within 1e-3 tolerance.
    """
    base_dir = Path(__file__).resolve().parent.parent
    pt_path = base_dir / "ml" / "outputs" / "agriguard_model.pt"
    if not pt_path.exists():
        pt_path = base_dir / "agriguard_model.pt"
    onnx_path = base_dir / "ml" / "outputs" / "agriguard_model.onnx"
    class_names_path = base_dir / "ml" / "outputs" / "class_names.json"

    assert pt_path.exists(), f"PyTorch checkpoint not found at {pt_path}"
    assert onnx_path.exists(), f"ONNX model not found at {onnx_path}"

    with open(class_names_path, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    # 1. Load PyTorch model
    ckpt = torch.load(pt_path, map_location="cpu")
    pt_model = models.mobilenet_v2(weights=None)
    in_features = pt_model.classifier[1].in_features
    pt_model.classifier[1] = torch.nn.Linear(in_features, len(class_names))
    pt_model.load_state_dict(ckpt["state_dict"])
    pt_model.eval()

    torch_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    # 2. Load ONNX Runtime model
    ort_session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = ort_session.get_inputs()[0].name

    # Test images list
    test_images = []
    
    # Real test leaf fixture
    leaf_file = base_dir / "tests" / "data" / "leaf_sample.jpg"
    if leaf_file.exists():
        test_images.append(Image.open(leaf_file).convert("RGB"))
        
    # Synthetic variation images
    test_images.append(Image.new("RGB", (300, 300), color=(45, 140, 50)))
    test_images.append(Image.new("RGB", (224, 224), color=(120, 80, 40)))
    test_images.append(Image.new("RGB", (512, 384), color=(200, 180, 60)))

    for i, img in enumerate(test_images):
        # A. PyTorch Inference
        pt_tensor = torch_transform(img).unsqueeze(0)
        with torch.no_grad():
            pt_logits = pt_model(pt_tensor)
            pt_probs = torch.softmax(pt_logits, dim=1).squeeze(0).numpy()

        # B. ONNX Inference
        onnx_tensor = preprocess_image(img)
        onnx_outputs = ort_session.run(None, {input_name: onnx_tensor})
        onnx_logits = onnx_outputs[0][0]
        exp_logits = np.exp(onnx_logits - np.max(onnx_logits))
        onnx_probs = exp_logits / np.sum(exp_logits)

        # Top-1 comparison
        pt_top1_idx = int(np.argmax(pt_probs))
        onnx_top1_idx = int(np.argmax(onnx_probs))

        assert pt_top1_idx == onnx_top1_idx, (
            f"Image {i}: Class mismatch: PyTorch={class_names[pt_top1_idx]} vs ONNX={class_names[onnx_top1_idx]}"
        )

        # Probability difference assertion
        prob_diff = np.abs(pt_probs - onnx_probs)
        max_diff = float(np.max(prob_diff))
        
        print(f"Image {i}: Top-1={class_names[pt_top1_idx]}, Max probability diff={max_diff:.6f}")
        assert max_diff < 1e-3, f"Image {i}: Probability diff {max_diff} exceeds tolerance 1e-3"
