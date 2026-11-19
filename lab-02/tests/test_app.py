from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as shop


@pytest.fixture
def file_client(monkeypatch, tmp_path):
    monkeypatch.setattr(shop, "DATABASE_URL", None)
    monkeypatch.setattr(shop, "COUNTER_FILE", tmp_path / "visits.txt")
    return shop.app.test_client()


def test_health_returns_expected_body():
    response = shop.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "ok\n"


def test_ready_reports_configured_file_store(file_client, tmp_path):
    response = file_client.get("/ready")

    assert response.status_code == 200
    assert response.get_json() == {
        "ready": True,
        "store": f"file:{tmp_path / 'visits.txt'}",
    }


def test_ready_fails_when_configured_database_is_unavailable(monkeypatch):
    def unavailable():
        raise ConnectionError("database unavailable")

    monkeypatch.setattr(shop, "DATABASE_URL", "postgresql://example/visits")
    monkeypatch.setattr(shop, "_db", unavailable)

    response = shop.app.test_client().get("/ready")

    assert response.status_code == 503
    assert response.get_json() == {
        "ready": False,
        "error": "database unavailable",
    }


def test_visits_increments_and_persists(file_client, tmp_path):
    first = file_client.get("/visits")
    second = file_client.get("/visits")

    assert first.status_code == second.status_code == 200
    assert first.get_json() == {"visits": 1, "store": "file"}
    assert second.get_json() == {"visits": 2, "store": "file"}
    assert (tmp_path / "visits.txt").read_text() == "2"


def test_visits_reports_file_error(file_client, tmp_path, monkeypatch):
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setattr(shop, "COUNTER_FILE", blocker / "visits.txt")

    response = file_client.get("/visits")

    assert response.status_code == 503
    assert response.get_json()["store"] == "file"
    assert "error" in response.get_json()
