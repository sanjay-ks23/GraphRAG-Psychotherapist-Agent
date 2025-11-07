"""API endpoint tests"""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_create_session():
    response = client.post("/v1/sessions", json={
        "user_id": "test_user",
        "consent_token": "test_token",
        "language": "en",
        "age_range": "8-12"
    })
    assert response.status_code == 200
    assert "session_id" in response.json()
