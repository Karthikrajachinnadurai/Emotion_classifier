import sys
import os

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend import ml
from fastapi.testclient import TestClient

print("Recreating database...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Initializing ML...")
ml.init_ml()

client = TestClient(app)

def run_tests():
    passed = 0
    failed = 0
    def assert_test(condition, message):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"[PASS] {message}")
        else:
            failed += 1
            print(f"[FAIL] {message}")

    print("\n--- 1. AUTHENTICATION ---")
    # Register
    res = client.post("/register", json={"name": "QA User", "email": "qa@example.com", "password": "password123"})
    assert_test(res.status_code == 200, "User registration")

    # Duplicate Register
    res = client.post("/register", json={"name": "QA User", "email": "qa@example.com", "password": "password123"})
    assert_test(res.status_code == 400, "Duplicate registration rejected")

    # Login
    res = client.post("/login", data={"username": "qa@example.com", "password": "password123"})
    assert_test(res.status_code == 200 and "access_token" in res.json(), "Login successful & JWT generated")
    if "access_token" not in res.json():
        print("Login response:", res.json())
        sys.exit(1)
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- 2. PREDICTION ---")
    sentences = [
        ("I am very happy today.", "joy"),
        ("I feel lonely.", "sadness"),
        ("I am scared.", "fear"),
        ("I hate everyone.", "anger"),
        ("I love my parents.", "love"),
        ("I didn't expect this!", "surprise")
    ]
    for text, expected in sentences:
        res = client.post("/predict", json={"text": text}, headers=headers)
        assert_test(res.status_code == 200, f"Prediction for '{text}'")
        if res.status_code == 200:
            data = res.json()
            assert_test(data.get("emotion") in ["joy", "sadness", "anger", "fear", "surprise", "love"], f"Valid emotion returned: {data.get('emotion')}")
            assert_test("confidence" in data, "Confidence shown")
            assert_test("probability_distribution" in data, "Probability chart generated")

    print("\n--- 3. CRISIS DETECTION ---")
    crisis_text = "I want to kill myself."
    res = client.post("/predict", json={"text": crisis_text}, headers=headers)
    assert_test(res.status_code == 200, "Crisis prediction processed")
    if res.status_code == 200:
        data = res.json()
        assert_test(data.get("is_crisis") is True, "Crisis flag is true")
        assert_test("EMERGENCY SUPPORT NEEDED" in data.get("cbt_response"), "Crisis response displayed")
        assert_test(data.get("emotion") == "crisis", "Emotion set to crisis")

    print("\n--- 4. GAMIFICATION & INSIGHTS ---")
    res = client.get("/dashboard", headers=headers)
    assert_test(res.status_code == 200, "Dashboard data retrieved")
    if res.status_code == 200:
        dash = res.json()
        assert_test(dash.get("total_points") > 0, f"Points awarded (Total: {dash.get('total_points')})")

    res = client.get("/insights", headers=headers)
    assert_test(res.status_code == 200, "Insights retrieved")
    
    res = client.get("/weekly-summary", headers=headers)
    assert_test(res.status_code == 200, "Weekly summary retrieved")

    res = client.get("/analytics", headers=headers)
    assert_test(res.status_code == 200, "Analytics retrieved")
    
    res = client.get("/history", headers=headers)
    assert_test(res.status_code == 200, "History retrieved")
    if res.status_code == 200:
        hist = res.json()
        assert_test(len(hist) > 0, "History is populated")
        
    print(f"\nTotal Passed: {passed}, Total Failed: {failed}")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
