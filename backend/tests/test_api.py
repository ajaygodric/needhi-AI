import os
import sys
from unittest import mock
import pytest

# Ensure the backend directory is in the search path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock chunk class for stream iteration
class MockGeminiChunk:
    def __init__(self, text):
        self.text = text
        # Mock structure: chunk.candidates[0].content.parts
        part = mock.Mock()
        part.text = text
        candidate = mock.Mock()
        candidate.content.parts = [part]
        self.candidates = [candidate]

# Mock response class
class MockGeminiResponse:
    def __init__(self, text):
        self.text = text
        self.candidates = [mock.Mock()]
    
    def __iter__(self):
        return iter([MockGeminiChunk(self.text)])

# Apply mock to generate_gemini_content BEFORE importing main and registering routers
mock_gen = mock.patch("core.gemini.generate_gemini_content")
mocked_func = mock_gen.start()
mocked_func.return_value = (MockGeminiResponse("Mocked legal analysis from Needhi AI"), "models/gemini-2.5-flash-lite")

# Now import the FastAPI app and dependencies
from main import app
from core.db import init_db
from fastapi.testclient import TestClient

@pytest.fixture(scope="module", autouse=True)
def init_test_db():
    # Setup/Migrate the SQLite DB
    init_db()
    
    # Clean the rate_limits table so test executions never hit rate limit 429
    import sqlite3
    from core.config import DATABASE_FILE
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rate_limits")
    conn.commit()
    conn.close()
    yield

client = TestClient(app)

def test_get_cases_all():
    """Verify all case logs are retrieved without filter parameters."""
    response = client.get("/api/cases")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "cnr" in data[0]

def test_get_cases_search_cnr():
    """Verify case is filterable by CNR."""
    all_res = client.get("/api/cases")
    if all_res.json():
        test_cnr = all_res.json()[0]["cnr"]
        response = client.get(f"/api/cases?search={test_cnr}&search_type=CNR+Number")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["cnr"] == test_cnr

def test_get_lawyers():
    """Verify lawyers lists are queryable and filterable."""
    response = client.get("/api/lawyers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "specialization" in data[0]

def test_get_lawyers_filtered():
    """Verify lawyers are filterable by specialization."""
    response = client.get("/api/lawyers?specialization=Criminal")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for lawyer in data:
        assert "Criminal" in lawyer["specialization"] or "criminal" in lawyer["specialization"].lower()

def test_bns_lookup_static():
    """Verify the offline ipc_bns static mappings search operates correctly."""
    response = client.post("/api/bns-lookup", json={"term": "theft", "category": ""})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "theft" in item["title"].lower() or "theft" in item["description"].lower() or "theft" in item["ipc"].lower() or "theft" in item["bns"].lower()

def test_chat_endpoint_greeting_bypass():
    """Verify simple greeting responses bypass RAG and return conversational greetings."""
    response = client.post("/api/chat", json={
        "query": "hi",
        "language": "English",
        "history": []
    })
    assert response.status_code == 200
    assert response.text != ""

def test_chat_endpoint_rag():
    """Verify legal queries trigger the mocked Gemini model pipeline."""
    response = client.post("/api/chat", json={
        "query": "What is the punishment for house breaking by night under BNS?",
        "language": "English",
        "history": []
    })
    assert response.status_code == 200
    assert "Mocked" in response.text

def test_generate_fir():
    """Verify complaint generation builds draft reports via mocked Gemini."""
    response = client.post("/api/generate-fir", json={
        "issue": "My neighbor stole my bicycle last night from the driveway",
        "state": "Tamil Nadu",
        "ps": "Maduravoyal Police Station",
        "name": "Jane Doe",
        "category": "Property Dispute",
        "category_fields": {
            "propertyLocation": "123 Street",
            "damageDetails": "Stolen bicycle"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert "draft" in data
    assert "Mocked" in data["draft"]

def test_cases_subscribe():
    """Verify case subscription register saves details to SQLite."""
    import time
    dynamic_sub_email = f"sub-test-{time.time()}@needhi.ai"
    reg = client.post("/api/auth/register", json={
        "name": "Sub User",
        "email": dynamic_sub_email,
        "password": "SecurePassword"
    })
    assert reg.status_code == 200
    token = reg.json()["token"]
    
    cases_res = client.get("/api/cases")
    if cases_res.json():
        test_cnr = cases_res.json()[0]["cnr"]
        response = client.post("/api/cases/subscribe", json={
            "cnr": test_cnr,
            "email": dynamic_sub_email,
            "client_name": "Sub User",
            "language": "English"
        }, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "already_subscribed"]




def test_spa_catch_all():
    """Verify that visiting a non-API client-side route returns index.html content (SPA router)."""
    response = client.get("/cases")
    assert response.status_code == 200
    assert "html" in response.text.lower() or "root" in response.text.lower()

def test_static_asset_logo():
    """Verify that requesting static asset files returns the actual file contents (not index.html)."""
    # Test PNG logo
    response = client.get("/needhi.png")
    assert response.status_code == 200
    assert "html" not in response.text.lower()
    
    # Test new SVG favicon
    response2 = client.get("/needhi_favicon.svg")
    assert response2.status_code == 200
    assert "svg" in response2.text.lower()


# Stop the mock after tests finish
def teardown_module(module):
    mock_gen.stop()


def test_auth_and_search_history_flow():
    """Verify complete registration, login, history logging, data isolation, and logout flow."""
    import time
    dynamic_email = f"auth-test-{time.time()}@needhi.ai"

    # 1. Register a new user
    reg_response = client.post("/api/auth/register", json={
        "name": "Test Auth User",
        "email": dynamic_email,
        "password": "SecurePassword123"
    })
    assert reg_response.status_code == 200
    reg_data = reg_response.json()
    assert "token" in reg_data
    assert reg_data["email"] == dynamic_email

    token = reg_data["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register again with same email should fail (400)
    reg_fail = client.post("/api/auth/register", json={
        "name": "Test Auth User 2",
        "email": dynamic_email,
        "password": "AnotherPassword"
    })
    assert reg_fail.status_code == 400

    # 3. Check /api/auth/me profile retrieve
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == dynamic_email

    # 4. Login user
    login_response = client.post("/api/auth/login", json={
        "email": dynamic_email,
        "password": "SecurePassword123"
    })
    assert login_response.status_code == 200
    assert "token" in login_response.json()

    # 5. RAG query with authorization header logs search history
    chat_response = client.post("/api/chat", json={
        "query": "Is trespass an offense under BNS?",
        "language": "English",
        "history": []
    }, headers=headers)
    assert chat_response.status_code == 200

    # 6. Retrieve history list
    hist_response = client.get("/api/chat/history", headers=headers)
    assert hist_response.status_code == 200
    hist_data = hist_response.json()
    assert len(hist_data) >= 1
    assert hist_data[0]["query"] == "Is trespass an offense under BNS?"

    # 7. Book a lawyer with authorization header
    lawyers_list = client.get("/api/lawyers").json()
    if lawyers_list:
        lawyer_id = lawyers_list[0]["id"]
        book_res = client.post("/api/book-lawyer", json={
            "lawyer_id": lawyer_id,
            "client_name": "Test Auth User",
            "client_email": dynamic_email,
            "client_phone": "9876543210",
            "date": "2026-10-10",
            "slot": "10:00 AM - 11:00 AM",
            "details": "Property encroachment issue"
        }, headers=headers)
        assert book_res.status_code == 200
        assert "receipt" in book_res.json()

        # 8. Retrieve my-bookings list
        my_bookings_res = client.get("/api/bookings/my-bookings", headers=headers)
        assert my_bookings_res.status_code == 200
        my_bookings = my_bookings_res.json()
        assert len(my_bookings) >= 1
        assert str(my_bookings[0]["lawyer_id"]) == str(lawyer_id)

    # 9. Case Subscribe with authorization header
    cases_list = client.get("/api/cases").json()
    if cases_list:
        cnr = cases_list[0]["cnr"]
        sub_res = client.post("/api/cases/subscribe", json={
            "cnr": cnr,
            "email": dynamic_email,
            "client_name": "Test Auth User",
            "language": "English"
        }, headers=headers)
        assert sub_res.status_code == 200

        # 10. Retrieve my-subscriptions list
        my_subs_res = client.get("/api/cases/my-subscriptions", headers=headers)
        assert my_subs_res.status_code == 200
        my_subs = my_subs_res.json()
        assert len(my_subs) >= 1
        assert my_subs[0]["cnr"] == cnr

    # 10.5 Clear history and verify it is empty
    clear_res = client.delete("/api/chat/history", headers=headers)
    assert clear_res.status_code == 200
    hist_empty_res = client.get("/api/chat/history", headers=headers)
    assert len(hist_empty_res.json()) == 0

    # 11. Logout user
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # 12. Retrieve profile again after logout should fail (401)
    me_fail = client.get("/api/auth/me", headers=headers)
    assert me_fail.status_code == 401



