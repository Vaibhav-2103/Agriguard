import json
import pytest
from pathlib import Path

def test_kb_completeness_and_schema():
    class_names_path = Path("ml/outputs/class_names.json")
    if not class_names_path.exists():
        class_names_path = Path("class_names.json")
    with open(class_names_path, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    kb_path = Path("knowledge/diseases.json")
    assert kb_path.exists()
    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    # Every class must have an entry
    for c_id in class_names:
        assert c_id in kb_data, f"Class {c_id} is missing in knowledge base"
        entry = kb_data[c_id]

        assert entry["class_id"] == c_id
        assert entry["crop"]
        assert entry["disease_name"]
        assert entry["scientific_name"]
        assert entry["disease_type"] in ["fungal", "bacterial", "viral", "pest", "healthy"]
        assert len(entry["symptoms"]) > 0
        assert len(entry["causes_and_spread"]) > 0

        # Check IPM severity plans
        t_sev = entry["treatment_by_severity"]
        for s in ["Low", "Medium", "High"]:
            assert s in t_sev
            assert "immediate_actions" in t_sev[s]
            assert "organic_options" in t_sev[s]
            assert "chemical_options" in t_sev[s]

        # Check active ingredients rule: no brand names or dosages
        for s in ["Low", "Medium", "High"]:
            for chem in t_sev[s]["chemical_options"]:
                assert "active_ingredient" in chem
                assert "note" in chem
                assert "caution" in chem
                # Check absence of brand names or specific numeric dosage units like 'ml/L' or 'g/acre'
                assert "ml/l" not in chem["note"].lower()
                assert "g/acre" not in chem["note"].lower()

        # FAQs
        assert len(entry["faq"]) >= 2
        for f_item in entry["faq"]:
            assert f_item["q"]
            assert f_item["a"]
            assert len(f_item["keywords"]) > 0
