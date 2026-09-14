"""
test/main.py — hello-service

Minimal FastAPI web app used to exercise a real build -> test -> canary
deploy -> verify pipeline end-to-end. Deliberately simple: one business
endpoint, health/readiness checks, and Prometheus metrics.

Set INJECT_ERRORS=true to make this instance behave like a bad canary
(higher latency + a real error rate) so a rollout can be exercised against
a genuine statistical rejection instead of only the happy path.
"""
import os
import time
import random

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="hello-service", version=os.environ.get("APP_VERSION", "v1.0.0"))

INJECT_ERRORS = os.environ.get("INJECT_ERRORS", "false").lower() == "true"
DEPLOYMENT_COHORT = os.environ.get("DEPLOYMENT_COHORT", "baseline")
APP_VERSION = os.environ.get("APP_VERSION", "v1.0.0")

REQUEST_COUNT = Counter(
    "hello_requests_total",
    "Total requests to the greeting endpoint",
    ["outcome"],
)
REQUEST_LATENCY = Histogram(
    "hello_request_duration_seconds",
    "Greeting endpoint request latency",
    buckets=(0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5),
)


@app.get("/healthz")
def healthz():
    return {"status": "healthy", "version": APP_VERSION, "cohort": DEPLOYMENT_COHORT}


@app.get("/readyz")
def readyz():
    return {"ready": True}


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/hello")
def hello(response: Response):
    """Healthy by default. INJECT_ERRORS=true simulates a regressed canary."""
    if INJECT_ERRORS:
        latency = random.gauss(0.065, 0.012)
        error_rate = 0.020
    else:
        latency = random.gauss(0.042, 0.005)
        error_rate = 0.005

    time.sleep(max(0, latency))
    REQUEST_LATENCY.observe(latency)

    if random.random() < error_rate:
        response.status_code = 500
        REQUEST_COUNT.labels(outcome="error").inc()
        return {"success": False, "error": "internal_error"}

    REQUEST_COUNT.labels(outcome="success").inc()
    return {"success": True, "message": "hello, world", "version": APP_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
