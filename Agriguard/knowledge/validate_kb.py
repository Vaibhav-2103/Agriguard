#!/usr/bin/env python3
"""
Validator for knowledge/diseases.json
Checks that every class in class_names.json has a valid, non-empty, and schema-compliant entry.
"""

import json
import sys
from pathlib import Path


def validate_kb():
    class_names_path = Path("ml/outputs/class_names.json")
    if not class_names_path.exists():
        class_names_path = Path("class_names.json")
    
    with open(class_names_path, "r", encoding="utf-8") as f:
        class_names = json.load(f)

    kb_path = Path("knowledge/diseases.json")
    if not kb_path.exists():
        print(f"ERROR: {kb_path} does not exist.")
        sys.exit(1)

    with open(kb_path, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    errors = []
    
    # 1. Completeness: every class must exist
    for c_id in class_names:
        if c_id not in kb_data:
            errors.append(f"Missing class in KB: {c_id}")
            continue

        entry = kb_data[c_id]
        # Check required fields
        required_fields = [
            "class_id", "crop", "disease_name", "scientific_name", "disease_type",
            "summary", "symptoms", "causes_and_spread", "treatment_by_severity",
            "fertilizer_and_nutrition", "precautions_and_prevention",
            "recovery_outlook", "when_to_consult_expert", "faq", "source_notes"
        ]
        for field in required_fields:
            if field not in entry or not entry[field]:
                errors.append(f"Class '{c_id}' missing or empty field: {field}")

        # Check severity structure
        treatments = entry.get("treatment_by_severity", {})
        for sev in ["Low", "Medium", "High"]:
            if sev not in treatments:
                errors.append(f"Class '{c_id}' missing severity level '{sev}'")
            else:
                plan = treatments[sev]
                if "immediate_actions" not in plan or not isinstance(plan["immediate_actions"], list):
                    errors.append(f"Class '{c_id}' severity '{sev}' missing immediate_actions list")
                if "organic_options" not in plan or not isinstance(plan["organic_options"], list):
                    errors.append(f"Class '{c_id}' severity '{sev}' missing organic_options list")
                if "chemical_options" not in plan or not isinstance(plan["chemical_options"], list):
                    errors.append(f"Class '{c_id}' severity '{sev}' missing chemical_options list")

        # Check FAQs
        faqs = entry.get("faq", [])
        if not faqs or len(faqs) < 2:
            errors.append(f"Class '{c_id}' has insufficient FAQ entries ({len(faqs)})")

    if errors:
        print(f"Validation FAILED with {len(errors)} errors:")
        for err in errors:
            print(f" - {err}")
        return False

    print(f"SUCCESS: Knowledge base validated successfully! All {len(class_names)} classes comply with schema.")
    return True


if __name__ == "__main__":
    if not validate_kb():
        sys.exit(1)
