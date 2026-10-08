import pytest
from pathlib import Path

def test_report_upload_flow(client, farmer_token):
    leaf_path = Path("tests/data/leaf_sample.jpg")
    with open(leaf_path, "rb") as f:
        res = client.post(
            "/reports",
            files={"image": ("leaf.jpg", f, "image/jpeg")},
            data={"crop": "Tomato", "location": "Greenhouse A"},
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] in ["completed", "completed_low_certainty"]
    assert data["predicted_class"] is not None
    assert data["confidence"] > 0.0
    assert len(data["top3"]) == 3
    assert data["insight"] is not None
    assert data["image_path"] is not None


def test_reports_access_control(client, farmer_token, farmer2_token):
    # Upload as farmer 1
    leaf_path = Path("tests/data/leaf_sample.jpg")
    with open(leaf_path, "rb") as f:
        res1 = client.post(
            "/reports",
            files={"image": ("leaf.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
    rep_id = res1.json()["id"]

    # Farmer 2 cannot view farmer 1's report
    res2 = client.get(f"/reports/{rep_id}", headers={"Authorization": f"Bearer {farmer2_token}"})
    assert res2.status_code == 403

    # Farmer 2 cannot delete farmer 1's report
    res_del = client.delete(f"/reports/{rep_id}", headers={"Authorization": f"Bearer {farmer2_token}"})
    assert res_del.status_code == 403

    # Farmer 1 can view own report
    res_own = client.get(f"/reports/{rep_id}", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res_own.status_code == 200

def test_expert_review_workflow(client, farmer_token, expert_token):
    # Upload report
    leaf_path = Path("tests/data/leaf_sample.jpg")
    with open(leaf_path, "rb") as f:
        res = client.post(
            "/reports",
            files={"image": ("leaf.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
    rep_id = res.json()["id"]

    # Regular farmer cannot review
    rev_farmer = client.post(
        f"/reports/{rep_id}/review",
        json={"verdict": "agree", "comment": "I agree"},
        headers={"Authorization": f"Bearer {farmer_token}"}
    )
    assert rev_farmer.status_code == 403

    # Expert can review
    rev_expert = client.post(
        f"/reports/{rep_id}/review",
        json={"verdict": "agree", "comment": "Confirmed by certified agronomist review."},
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert rev_expert.status_code == 200
    assert rev_expert.json()["verdict"] == "agree"

    # Expert queue shows the report
    queue_res = client.get("/expert/reports", headers={"Authorization": f"Bearer {expert_token}"})
    assert queue_res.status_code == 200
    assert any(r["id"] == rep_id for r in queue_res.json())

def test_delete_report(client, farmer_token):
    leaf_path = Path("tests/data/leaf_sample.jpg")
    with open(leaf_path, "rb") as f:
        res = client.post(
            "/reports",
            files={"image": ("leaf.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {farmer_token}"}
        )
    rep_id = res.json()["id"]

    del_res = client.delete(f"/reports/{rep_id}", headers={"Authorization": f"Bearer {farmer_token}"})
    assert del_res.status_code == 204

    # Verify not found
    get_res = client.get(f"/reports/{rep_id}", headers={"Authorization": f"Bearer {farmer_token}"})
    assert get_res.status_code == 404
