import pytest
from PIL import Image
from backend.services.classifier import classifier, parse_class_name

def test_parse_class_name():
    crop, disease = parse_class_name("Tomato___Early_blight")
    assert crop == "Tomato"
    assert disease == "Early blight"

    crop, disease = parse_class_name("Apple___healthy")
    assert crop == "Apple"
    assert disease == "healthy"

    crop, disease = parse_class_name("Corn_(maize)___Common_rust_")
    assert "Corn" in crop
    assert "rust" in disease.lower()

def test_classifier_predict_shape_and_classes():
    assert classifier.model is not None
    assert len(classifier.class_names) == 38

    # Dummy image
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    top3 = classifier.predict(img)

    assert len(top3) == 3
    for pred in top3:
        assert "class_id" in pred
        assert "crop" in pred
        assert "disease_name" in pred
        assert 0.0 <= pred["probability"] <= 1.0

    # Ensure probabilities are sorted descending
    assert top3[0]["probability"] >= top3[1]["probability"] >= top3[2]["probability"]

def test_get_supported_crops():
    crops = classifier.get_supported_crops()
    assert len(crops) >= 10
    assert "Tomato" in crops
    assert "Apple" in crops
    assert "Potato" in crops
