from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


from main import create_app  # noqa: E402


def _expected_routes() -> set[tuple[str, str]]:
    return {
        ("GET", "/health"),
        # Generic authenticated CRUD endpoints
        ("POST", "/spots/"),
        ("GET", "/spots/"),
        ("GET", "/spots/{entity_id}"),
        ("PUT", "/spots/{entity_id}"),
        ("DELETE", "/spots/{entity_id}"),
        ("POST", "/client-errors/"),
        ("GET", "/client-errors/"),
        ("GET", "/client-errors/{entity_id}"),
        ("PUT", "/client-errors/{entity_id}"),
        ("DELETE", "/client-errors/{entity_id}"),
        # Auth endpoints
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        # Social endpoints
        ("GET", "/social/me"),
        ("PUT", "/social/me"),
        ("GET", "/social/users/search"),
        ("GET", "/social/users/{user_id}/profile"),
        ("GET", "/social/spots"),
        ("POST", "/social/spots"),
        ("PUT", "/social/spots/{spot_id}"),
        ("DELETE", "/social/spots/{spot_id}"),
        ("GET", "/social/users/{user_id}/spots"),
        ("POST", "/social/favorites/{spot_id}"),
        ("DELETE", "/social/favorites/{spot_id}"),
        ("GET", "/social/favorites"),
        ("GET", "/social/users/{user_id}/favorites"),
        ("GET", "/social/follow/requests"),
        ("POST", "/social/follow/requests/{follower_id}/approve"),
        ("POST", "/social/follow/requests/{follower_id}/reject"),
        ("POST", "/social/follow/{user_id}"),
        ("DELETE", "/social/follow/{user_id}"),
        ("GET", "/social/followers/{user_id}"),
        ("GET", "/social/following/{user_id}"),
        ("DELETE", "/social/followers/{user_id}"),
        ("POST", "/social/block/{user_id}"),
        ("DELETE", "/social/block/{user_id}"),
        ("GET", "/social/blocked"),
        ("POST", "/social/share/{spot_id}"),
        ("POST", "/social/support/tickets"),
        ("GET", "/social/spots/{spot_id}/comments"),
        ("POST", "/social/spots/{spot_id}/comments"),
        ("PATCH", "/social/comments/{comment_id}"),
        ("DELETE", "/social/comments/{comment_id}"),
        ("POST", "/social/meetups"),
        ("GET", "/social/meetups"),
        ("PUT", "/social/meetups/{meetup_id}"),
        ("DELETE", "/social/meetups/{meetup_id}"),
        ("GET", "/social/meetups/invites"),
        ("POST", "/social/meetups/{meetup_id}/respond"),
        ("GET", "/social/meetups/{meetup_id}/comments"),
        ("POST", "/social/meetups/{meetup_id}/comments"),
        ("PATCH", "/social/meetup-comments/{comment_id}"),
        ("DELETE", "/social/meetup-comments/{comment_id}"),
    }


@pytest.fixture()
def app(monkeypatch):
    _ = monkeypatch
    return create_app()


def test_route_inventory_contains_all_expected_endpoints(app):
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", set())
        for method in methods:
            if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                routes.add((method, route.path))

    missing = _expected_routes() - routes
    assert not missing, f"Missing routes: {sorted(missing)}"


def test_openapi_is_reachable(app):
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert "paths" in payload


def test_healthcheck_is_reachable(app, monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("core.application.ping_mongo", lambda: True)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "services": {
            "api": "ok",
            "mongo": "ok",
        },
    }


@pytest.mark.parametrize(
    ("method", "path", "json_body", "expected_status"),
    [
        ("POST", "/auth/register", {}, 422),
        ("POST", "/auth/login", {}, 422),
        # Generic authenticated routers
        ("POST", "/spots/", {}, 401),
        ("GET", "/spots/", None, 401),
        ("GET", "/spots/507f1f77bcf86cd799439012", None, 401),
        ("PUT", "/spots/507f1f77bcf86cd799439012", {}, 401),
        ("DELETE", "/spots/507f1f77bcf86cd799439012", None, 401),
        # Social endpoints (authentication boundary)
        ("GET", "/social/me", None, 401),
        ("GET", "/social/favorites", None, 401),
        ("GET", "/social/follow/requests", None, 401),
        ("GET", "/social/blocked", None, 401),
        ("POST", "/social/spots/507f1f77bcf86cd799439011/comments", {"message": "hello"}, 401),
        ("PATCH", "/social/comments/507f1f77bcf86cd799439013", {"message": "edit"}, 401),
        ("DELETE", "/social/comments/507f1f77bcf86cd799439013", None, 401),
        ("GET", "/social/meetups", None, 401),
        ("POST", "/social/meetups", {"title": "M", "starts_at": "2027-01-01T12:00:00Z"}, 401),
        ("GET", "/social/meetups/507f1f77bcf86cd799439013/comments", None, 401),
    ],
)
def test_endpoints_return_expected_unauthenticated_status(app, method, path, json_body, expected_status):
    client = TestClient(app)
    response = client.request(method, path, json=json_body)
    assert response.status_code == expected_status
