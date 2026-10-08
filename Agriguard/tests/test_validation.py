import pytest
from pathlib import Path
from backend.services.validation import validate_leaf_image, ImageValidationError

def test_validate_valid_leaf():
    leaf_path = Path("tests/data/leaf_sample.jpg")
    assert leaf_path.exists()
    with open(leaf_path, "rb") as f:
        img_bytes = f.read()

    pil_img, bgr_img, meta = validate_leaf_image(img_bytes, "leaf_sample.jpg")
    assert pil_img is not None
    assert bgr_img is not None
    assert meta["vegetation_percent"] >= 5.0

def test_reject_blurry_image():
    blurry_path = Path("tests/data/blurry.jpg")
    assert blurry_path.exists()
    with open(blurry_path, "rb") as f:
        img_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc:
        validate_leaf_image(img_bytes, "blurry.jpg")
    assert exc.value.code == "IMAGE_BLURRY"

def test_reject_dark_image():
    dark_path = Path("tests/data/dark.jpg")
    assert dark_path.exists()
    with open(dark_path, "rb") as f:
        img_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc:
        validate_leaf_image(img_bytes, "dark.jpg")
    assert exc.value.code in ["IMAGE_TOO_DARK", "NO_LEAF_DETECTED"]

def test_reject_non_leaf_image():
    non_leaf_path = Path("tests/data/non_leaf.jpg")
    assert non_leaf_path.exists()
    with open(non_leaf_path, "rb") as f:
        img_bytes = f.read()

    with pytest.raises(ImageValidationError) as exc:
        validate_leaf_image(img_bytes, "non_leaf.jpg")
    assert exc.value.code in ["NO_LEAF_DETECTED", "IMAGE_BLURRY"]

def test_reject_corrupted_image():
    with pytest.raises(ImageValidationError) as exc:
        validate_leaf_image(b"not an image file content", "corrupted.jpg")
    assert exc.value.code == "INVALID_IMAGE_FILE"
