from fastapi.testclient import TestClient
from app.main import app
from common.core.security import create_access_token
from common.core.settings import get_settings


def test_suggestions_endpoint():
    client = TestClient(app)
    settings = get_settings()
    token = create_access_token(sub="test-user", email="test@example.com", settings=settings)
    response = client.post(
        "/api/v1/ai/suggestions",
        headers={"Authorization": f"Bearer {token}"},
        json={"campaign_id": 1, "asset_text": "short sales copy"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "suggestions" in body
    assert len(body["suggestions"]) >= 1

