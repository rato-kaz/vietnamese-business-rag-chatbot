import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "timestamp" in data
    assert "version" in data


def test_create_session():
    """Test session creation."""
    response = client.post("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "created_at" in data
    assert data["status"] == "active"
    return data["session_id"]


def test_chat_message():
    """Test sending chat message."""
    # First create a session
    session_response = client.post("/sessions")
    session_id = session_response.json()["session_id"]
    
    # Send a message
    message_data = {
        "message": "Xin chào",
        "session_id": session_id
    }
    
    response = client.post("/chat/message", json=message_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "intent" in data
    assert data["session_id"] == session_id


def test_intent_classification():
    """Test intent classification endpoint."""
    request_data = {
        "text": "Tôi muốn tạo hồ sơ đăng ký công ty"
    }
    
    response = client.post("/classify-intent", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert data["intent"] in ["legal", "business", "general"]
    assert "description" in data
    assert "confidence" in data


def test_get_templates():
    """Test getting available templates."""
    response = client.get("/templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_document_stats():
    """Test getting document statistics."""
    response = client.get("/documents/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "embedding_model" in data


def test_system_stats():
    """Test getting system statistics."""
    response = client.get("/system/stats")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data
    assert "total_documents" in data


def test_session_management():
    """Test session management operations."""
    # Create session
    create_response = client.post("/sessions")
    assert create_response.status_code == 200
    session_id = create_response.json()["session_id"]
    
    # Get session info
    info_response = client.get(f"/sessions/{session_id}")
    assert info_response.status_code == 200
    info_data = info_response.json()
    assert info_data["session_id"] == session_id
    
    # Get conversation history
    history_response = client.get(f"/sessions/{session_id}/history")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert isinstance(history_data, list)
    
    # Clear session
    clear_response = client.post(f"/sessions/{session_id}/clear")
    assert clear_response.status_code == 200
    
    # Delete session
    delete_response = client.delete(f"/sessions/{session_id}")
    assert delete_response.status_code == 200


def test_error_handling():
    """Test error handling for invalid requests."""
    # Test with invalid session ID
    response = client.get("/sessions/invalid-session-id")
    assert response.status_code == 404
    
    # Test with invalid template name
    response = client.get("/templates/invalid-template/fields")
    assert response.status_code == 404


def test_chat_suggestions():
    """Test getting chat suggestions."""
    # Create session first
    session_response = client.post("/sessions")
    session_id = session_response.json()["session_id"]
    
    response = client.get(f"/chat/suggestions?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_conversation_export():
    """Test conversation export."""
    # Create session and send a message
    session_response = client.post("/sessions")
    session_id = session_response.json()["session_id"]
    
    # Send a message to create conversation history
    message_data = {
        "message": "Test message",
        "session_id": session_id
    }
    client.post("/chat/message", json=message_data)
    
    # Export conversation
    export_response = client.post(f"/chat/export?session_id={session_id}&format=json")
    assert export_response.status_code == 200
    export_data = export_response.json()
    assert "conversation" in export_data
    assert export_data["session_id"] == session_id


if __name__ == "__main__":
    pytest.main([__file__])