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
    cases_res = client.get("/api/cases")
    if cases_res.json():
        test_cnr = cases_res.json()[0]["cnr"]
        response = client.post("/api/cases/subscribe", json={
            "cnr": test_cnr,
            "email": "test-subscriber@needhi.ai",
            "client_name": "Test User",
            "language": "English"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["success", "already_subscribed"]


def test_spa_catch_all():
    """Verify that visiting a non-API client-side route returns index.html content (SPA router)."""
    response = client.get("/cases")
    assert response.status_code == 200
    assert "html" in response.text.lower() or "root" in response.text.lower()

def test_static_asset_logo():
    """Verify that requesting a static asset file returns the actual file contents (not index.html)."""
    response = client.get("/needhi.png")
    assert response.status_code == 200
    assert "html" not in response.text.lower()

# Stop the mock after tests finish
def teardown_module(module):
    mock_gen.stop()


