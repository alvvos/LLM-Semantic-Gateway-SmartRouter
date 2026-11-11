from fastapi.testclient import TestClient
from unittest.mock import patch
from src.main import app

client = TestClient(app)

@patch('src.api.router.cache_instance.add')
@patch('src.api.router.cache_instance.search')
def test_chat_endpoint_cache_miss(mock_search, mock_add):
    mock_search.return_value = (None, 0.0)
    
    response = client.post("/chat", json={"prompt": "¿como pido vacaciones?"})
    data = response.json()
    
    assert response.status_code == 200
    assert data["status"] == "CACHE_MISS (LLM Called)"
    assert data["cost_saved"] is False
    mock_add.assert_called_once()

@patch('src.api.router.cache_instance.search')
def test_chat_endpoint_cache_hit(mock_search):
    mock_search.return_value = ("tienes 22 días laborables", 0.95)
    
    response = client.post("/chat", json={"prompt": "¿cuantos días de vacaciones tengo?"})
    data = response.json()
    
    assert response.status_code == 200
    assert data["status"] == "CACHE_HIT"
    assert data["response"] == "tienes 22 días laborables"
    assert data["cost_saved"] is True