import pytest
import numpy as np
import cv2
from backend.services.severity import analyze_leaf_severity

def test_severity_healthy_skip():
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    label, ratio, overlay = analyze_leaf_severity(img, is_healthy=True)
    assert label is None
    assert ratio == 0.0
    assert overlay is None

def test_severity_diseased_calculation():
    # Construct a predominantly green leaf with 20% brown spots
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[:] = (240, 240, 240)
    # Green leaf body
    cv2.circle(img, (100, 100), 70, (34, 139, 34), -1)
    # Lesion
    cv2.circle(img, (100, 100), 25, (25, 95, 175), -1)

    label, ratio, overlay = analyze_leaf_severity(img, is_healthy=False, output_filename="test_sev.jpg")
    assert label in ["Low", "Medium", "High"]
    assert 0.0 <= ratio <= 1.0
    assert overlay is not None

def test_severity_threshold_mapping():
    # Test low vs high
    # Mostly green -> Low severity
    img_low = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(img_low, (100, 100), 80, (34, 139, 34), -1)
    label_low, ratio_low, _ = analyze_leaf_severity(img_low, is_healthy=False)
    assert label_low == "Low"
    assert ratio_low < 0.10
