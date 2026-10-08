import io
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Dict, Any, Tuple, List
from backend.config import settings


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str, tips: List[str]):
        super().__init__(message)
        self.code = code
        self.message = message
        self.tips = tips


def validate_leaf_image(image_bytes: bytes, filename: str = "") -> Tuple[Image.Image, np.ndarray, Dict[str, Any]]:
    """
    Validates uploaded leaf image according to strict image quality criteria:
    - Real image format (JPEG, PNG, WEBP)
    - File size <= 8 MB
    - Minimum dimensions (64x64)
    - Blur detection via Laplacian variance
    - Exposure / brightness boundaries
    - Leaf vegetative color check in HSV color space

    Returns:
        (PIL.Image, cv2_bgr_image, metadata_dict)
    Raises:
        ImageValidationError if criteria are violated.
    """
    # 1. Size check
    if len(image_bytes) > settings.MAX_FILE_SIZE_BYTES:
        raise ImageValidationError(
            code="FILE_TOO_LARGE",
            message=f"File size exceeds {settings.MAX_FILE_SIZE_BYTES // (1024*1024)}MB limit.",
            tips=["Please compress your photo or capture it at standard resolution."]
        )

    # 2. Content integrity & format check
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        pil_img.verify()
        # Reopen because verify() consumes the stream
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ImageValidationError(
            code="INVALID_IMAGE_FILE",
            message="The uploaded file is corrupted or not a valid image.",
            tips=["Please upload a valid JPG, PNG, or WEBP image of a crop leaf."]
        )

    valid_formats = {"JPEG", "JPG", "PNG", "WEBP"}
    if (pil_img.format or "").upper() not in valid_formats:
        # Check filename extension as fallback
        ext = filename.split(".")[-1].upper() if "." in filename else ""
        if ext not in valid_formats:
            raise ImageValidationError(
                code="UNSUPPORTED_FORMAT",
                message=f"Image format {pil_img.format or ext} is not supported.",
                tips=["Please use JPG, PNG, or WEBP formats."]
            )

    # Convert to RGB
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    width, height = pil_img.size
    if width < settings.MIN_IMAGE_DIM or height < settings.MIN_IMAGE_DIM:
        raise ImageValidationError(
            code="IMAGE_TOO_SMALL",
            message=f"Image resolution {width}x{height} is too small for accurate disease diagnosis.",
            tips=["Capture the photo closer to the leaf with at least 224x224 pixels."]
        )

    # Downscale high-resolution photos to max 1024px for RAM optimization
    if max(width, height) > settings.MAX_IMAGE_DIM:
        pil_img.thumbnail((settings.MAX_IMAGE_DIM, settings.MAX_IMAGE_DIM), Image.Resampling.BILINEAR)
        width, height = pil_img.size

    # Convert to OpenCV BGR format for CV operations
    rgb_arr = np.array(pil_img)
    bgr_img = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)


    # 3. Brightness check (in grayscale)
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
    avg_brightness = float(np.mean(gray))

    if avg_brightness < settings.BRIGHTNESS_MIN:
        raise ImageValidationError(
            code="IMAGE_TOO_DARK",
            message=f"The photo is too dark (brightness index: {avg_brightness:.1f}/255).",
            tips=[
                "Take the photo in clear daylight or turn on your camera flash.",
                "Ensure shadows are not completely covering the leaf."
            ]
        )

    if avg_brightness > settings.BRIGHTNESS_MAX:
        raise ImageValidationError(
            code="IMAGE_TOO_BRIGHT",
            message=f"The photo is overexposed or has severe glare (brightness index: {avg_brightness:.1f}/255).",
            tips=[
                "Avoid harsh direct sunlight reflection or flashlight glare directly bouncing into the lens.",
                "Angle your phone slightly to reduce white specular highlights."
            ]
        )

    # 4. Blur check using Laplacian variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if laplacian_var < settings.BLUR_LAPLACIAN_VAR_THRESHOLD:
        raise ImageValidationError(
            code="IMAGE_BLURRY",
            message=f"The photo appears blurry or out of focus (sharpness score: {laplacian_var:.1f}).",
            tips=[
                "Hold your phone steady or rest your hands on a stable surface.",
                "Tap the camera screen directly on the leaf lesion to focus before taking the shot.",
                "Wipe your camera lens clean of dust or moisture."
            ]
        )

    # 5. Leaf / Plant color presence check in HSV space
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
    # Green and yellow/brown vegetation bounds in HSV:
    # Hue: [20, 95] covers yellow-green, green, dark green; [10, 25] covers yellow/brown necrotic leaf tissue
    plant_mask = cv2.inRange(hsv, np.array([10, 25, 25]), np.array([100, 255, 255]))
    plant_pixel_ratio = (np.count_nonzero(plant_mask) / (width * height)) * 100.0

    if plant_pixel_ratio < settings.MIN_LEAF_COLOR_PERCENT:
        raise ImageValidationError(
            code="NO_LEAF_DETECTED",
            message=f"No crop leaf or foliage detected in the photo ({plant_pixel_ratio:.1f}% vegetative pixels found).",
            tips=[
                "Make sure a crop leaf covers the majority of the camera frame.",
                "Avoid photographing plain walls, soil, hands, or distant fields without a close-up leaf."
            ]
        )

    metadata = {
        "width": width,
        "height": height,
        "brightness": round(avg_brightness, 2),
        "sharpness": round(laplacian_var, 2),
        "vegetation_percent": round(plant_pixel_ratio, 2)
    }

    return pil_img, bgr_img, metadata
