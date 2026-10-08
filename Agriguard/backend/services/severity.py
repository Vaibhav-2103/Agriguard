import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from backend.config import settings


def analyze_leaf_severity(
    bgr_img: np.ndarray,
    is_healthy: bool,
    output_filename: str = ""
) -> Tuple[Optional[str], float, Optional[str]]:
    """
    OpenCV-based heuristic severity estimation for crop leaf diseases.

    METHODOLOGY (HEURISTIC):
    1. Segments the total leaf body in HSV color space (capturing both healthy green
       tissue and diseased necrotic/chlorotic lesions).
    2. Identifies healthy green pixels within the leaf mask (Hue ~ 35 to 85).
    3. The diseased fraction is computed as:
       diseased_fraction = (total_leaf_pixels - healthy_green_pixels) / total_leaf_pixels
    4. Categorizes into severity levels:
       - Low:    < 10% (< 0.10)
       - Medium: 10% - 30% (0.10 - 0.30)
       - High:   > 30% (> 0.30)
    5. Generates an annotated visual overlay image highlighting diseased lesions
       in crimson/red and healthy foliage in translucent green, stamped with the metric.

    NOTE: This is an optical heuristic designed for visual field estimation and should
    be corroborated with laboratory tissue testing for critical diagnostic decisions.

    Returns:
        (severity_label, severity_ratio, overlay_relative_path)
    """
    if is_healthy:
        return None, 0.0, None

    h, w = bgr_img.shape[:2]
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)

    # 1. Total Leaf Segmentation (broad range covering green, yellow, brown, orange lesions)
    # Hue 10 to 100 covers chlorosis, blight, brown rot, rust, and green foliage
    lower_leaf = np.array([10, 25, 30])
    upper_leaf = np.array([105, 255, 255])
    leaf_mask = cv2.inRange(hsv, lower_leaf, upper_leaf)

    # Morphological cleaning to remove salt-and-pepper noise and fill small interior gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)

    total_leaf_pixels = np.count_nonzero(leaf_mask)
    if total_leaf_pixels < 100:
        # Fallback if leaf mask segmentation is too sparse
        total_leaf_pixels = max(1, h * w)
        leaf_mask = np.ones((h, w), dtype=np.uint8) * 255

    # 2. Healthy Green Foliage Mask (tight green Hue 35 to 85, moderate saturation & value)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    healthy_leaf_mask = cv2.bitwise_and(green_mask, green_mask, mask=leaf_mask)

    healthy_pixels = np.count_nonzero(healthy_leaf_mask)
    diseased_pixels = max(0, total_leaf_pixels - healthy_pixels)

    severity_ratio = float(diseased_pixels) / float(total_leaf_pixels)
    severity_ratio = min(max(severity_ratio, 0.0), 1.0)

    # 3. Classify Severity
    if severity_ratio < settings.SEVERITY_LOW_THRESHOLD:
        severity_label = "Low"
        badge_color = (0, 180, 0)  # Green
    elif severity_ratio <= settings.SEVERITY_MEDIUM_THRESHOLD:
        severity_label = "Medium"
        badge_color = (0, 140, 255)  # Orange
    else:
        severity_label = "High"
        badge_color = (0, 0, 220)  # Red

    # 4. Generate Annotated Visual Overlay
    diseased_mask = cv2.bitwise_and(leaf_mask, cv2.bitwise_not(healthy_leaf_mask))

    # Base overlay copy
    overlay = bgr_img.copy()

    # Red/Crimson highlight on diseased lesions (BGR: [30, 40, 230])
    red_layer = np.zeros_like(bgr_img)
    red_layer[:] = [30, 40, 230]
    # Blend diseased areas
    cv2.copyTo(
        cv2.addWeighted(bgr_img, 0.45, red_layer, 0.55, 0),
        diseased_mask,
        overlay
    )

    # Contours around diseased lesions
    contours, _ = cv2.findContours(diseased_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 255, 255), 1)  # Thin yellow contour

    # Bottom annotation banner
    banner_height = 42
    banner = np.zeros((banner_height, w, 3), dtype=np.uint8)
    banner[:] = (30, 30, 30)  # Dark slate gray
    cv2.putText(
        banner,
        f"Severity: {severity_label} ({severity_ratio * 100:.1f}% affected area) [Heuristic]",
        (10, 27),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )
    # Circle badge on banner
    cv2.circle(banner, (w - 20, 21), 9, badge_color, -1)

    annotated = np.vstack([overlay, banner])

    # Save overlay file
    overlay_rel_path = None
    if output_filename:
        overlay_filename = f"overlay_{output_filename}"
        overlay_full_path = Path(settings.UPLOAD_DIR) / overlay_filename
        cv2.imwrite(str(overlay_full_path), annotated)
        overlay_rel_path = f"uploads/{overlay_filename}"

    return severity_label, round(severity_ratio, 4), overlay_rel_path
