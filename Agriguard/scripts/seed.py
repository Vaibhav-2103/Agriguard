import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

# Add root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.database import SessionLocal, Base, engine
from backend.models import User, Report, Conversation, Message, ExpertReview, ProcessingLog
from backend.auth import hash_password
from backend.services.classifier import classifier
from backend.services.severity import analyze_leaf_severity

def seed_database():
    print("Initializing AgriGuard Database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Demo Farmer
        farmer = db.query(User).filter(User.email == "ramesh@farmer.in").first()
        if not farmer:
            farmer = User(
                name="Ramesh Kumar",
                email="ramesh@farmer.in",
                password_hash=hash_password("farmer123"),
                role="farmer",
                preferred_language="hi"
            )
            db.add(farmer)
            db.commit()
            db.refresh(farmer)
            print("Created Demo Farmer: ramesh@farmer.in")
        else:
            farmer.password_hash = hash_password("farmer123")
            db.commit()
            print("Demo Farmer updated with farmer123 password.")

        # 2. Seed Demo Expert
        expert = db.query(User).filter(User.email == "expert@agriguard.in").first()
        if not expert:
            expert = User(
                name="Dr. M. S. Swaminathan",
                email="expert@agriguard.in",
                password_hash=hash_password("expert123"),
                role="expert",
                preferred_language="en"
            )
            db.add(expert)
            db.commit()
            db.refresh(expert)
            print("Created Demo Expert: expert@agriguard.in")
        else:
            expert.password_hash = hash_password("expert123")
            db.commit()
            print("Demo Expert updated with expert123 password.")

        # 3. Seed Sample Diagnostic Report
        existing_report = db.query(Report).filter(Report.user_id == farmer.id).first()
        if not existing_report:
            # Create synthetic test leaf in uploads
            uploads_dir = Path("uploads")
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            sample_img_name = "seed_tomato_leaf.jpg"
            sample_img_path = uploads_dir / sample_img_name
            
            # Generate green leaf with some brown lesion
            img = np.zeros((300, 300, 3), dtype=np.uint8)
            img[:] = (245, 245, 245)
            cv2.ellipse(img, (150, 150), (110, 80), 20, 0, 360, (34, 139, 34), -1)
            cv2.circle(img, (140, 135), 24, (25, 95, 175), -1)
            cv2.circle(img, (175, 165), 18, (20, 85, 160), -1)
            cv2.imwrite(str(sample_img_path), img)

            # Predict and severity
            pil_img = Image.open(sample_img_path).convert("RGB")
            top3 = classifier.predict(pil_img)
            top_pred = top3[0]

            sev_label, sev_ratio, overlay_path = analyze_leaf_severity(
                bgr_img=img,
                is_healthy=False,
                output_filename=sample_img_name
            )

            # Load KB insight
            kb_path = Path("knowledge/diseases.json")
            kb = {}
            if kb_path.exists():
                with open(kb_path, "r", encoding="utf-8") as f:
                    kb = json.load(f)
            insight = kb.get(top_pred["class_id"])

            report = Report(
                user_id=farmer.id,
                image_path=f"uploads/{sample_img_name}",
                overlay_path=overlay_path,
                crop="Tomato",
                location="Karnal, Haryana Plot 4",
                notes="Observed concentric dark rings on lower canopy leaves.",
                predicted_class=top_pred["class_id"],
                confidence=top_pred["probability"],
                top3_json=json.dumps(top3),
                severity=sev_label,
                severity_ratio=sev_ratio,
                status="completed",
                insight_json=json.dumps(insight) if insight else None
            )
            db.add(report)
            db.commit()
            db.refresh(report)

            # Add demo expert review
            review = ExpertReview(
                report_id=report.id,
                expert_id=expert.id,
                verdict="agree",
                comment="Verified: Early blight symptoms with characteristic bullseye target concentric lesions. Proceed with copper hydroxide contact spray."
            )
            db.add(review)

            # Add demo conversation
            conv = Conversation(
                user_id=farmer.id,
                report_id=report.id,
                title=f"Chat: Tomato ({top_pred['disease_name']})"
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

            m1 = Message(conversation_id=conv.id, role="user", content="How do I treat this?")
            m2 = Message(conversation_id=conv.id, role="assistant", content=f"**Action Plan for {sev_label} Severity:**\n1. Remove lower infected leaves and avoid overhead watering.\n2. Apply preventative copper-based protectants according to label instructions.")
            db.add(m1)
            db.add(m2)

            log = ProcessingLog(report_id=report.id, success=True, duration_ms=45.2)
            db.add(log)

            db.commit()
            print(f"Created Seed Report ID {report.id} with expert review and chat history.")

        print("Seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
