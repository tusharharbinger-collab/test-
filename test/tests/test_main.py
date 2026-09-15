import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from faker import Faker

import main

client = TestClient(main.app)
fake = Faker()


def test_faker_is_actually_installed_from_this_repos_own_requirements():
    """Proves tests run in a real per-repo virtualenv, not pipeline-worker's
    own environment — pipeline-worker never installs `faker`, so this only
    passes if this repo's OWN requirements.txt was actually installed."""
    name = fake.name()
    assert isinstance(name, str) and len(name) > 0


def test_healthz_reports_healthy_with_version_and_cohort():
    resp = client.get("/healthz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["version"] == main.APP_VERSION
    assert body["cohort"] == main.DEPLOYMENT_COHORT


def test_readyz_reports_ready():
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"ready": True}


def test_metrics_exposes_prometheus_text_format():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "hello_requests_total" in resp.text
    assert "hello_request_duration_seconds" in resp.text


def test_hello_returns_a_well_shaped_response_on_success_or_failure():
    """error_rate is probabilistic (0.5% normally), so this asserts the
    response shape is correct for whichever outcome actually occurred,
    rather than assuming success."""
    resp = client.get("/api/v1/hello")
    assert resp.status_code in (200, 500)
    body = resp.json()
    if resp.status_code == 200:
        assert body["success"] is True
        assert body["message"] == "hello, world"
        assert body["version"] == main.APP_VERSION
    else:
        assert body["success"] is False
        assert body["error"] == "internal_error"
