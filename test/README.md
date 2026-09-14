# hello-service

A deliberately minimal FastAPI web app, built to be onboarded as a project
in a progressive-delivery / canary CD platform. It exists purely to
exercise a real pipeline (build → test → deploy → verify) end-to-end
against a repo you actually control.

## Endpoints

| Method | Path              | Purpose                                   |
|--------|-------------------|--------------------------------------------|
| GET    | `/healthz`        | Liveness check                             |
| GET    | `/readyz`         | Readiness check                            |
| GET    | `/metrics`        | Prometheus metrics (request count + latency) |
| GET    | `/api/v1/hello`   | The one business endpoint                  |

## Configuration (environment variables)

| Variable            | Default    | Effect                                                  |
|---------------------|------------|----------------------------------------------------------|
| `APP_VERSION`        | `v1.0.0`   | Reported in `/healthz` and `/api/v1/hello` responses     |
| `DEPLOYMENT_COHORT`  | `baseline` | Reported in `/healthz` — set to `canary` on the canary deployment |
| `INJECT_ERRORS`      | `false`    | Set to `true` to simulate a regressed canary: ~65ms latency and a 2% error rate on `/api/v1/hello`, instead of the healthy ~42ms / 0.5% default. Use this to test that your pipeline's verification step correctly detects a bad rollout and rolls it back. |

## Run locally

```bash
pip install -r requirements.txt
python main.py          # serves on :8080
```

## Run the tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Build the image

```bash
docker build -t hello-service:v1.0.0 .
docker run -p 8080:8080 hello-service:v1.0.0
```

## Using this with a canary pipeline

Point your pipeline's build stage at this folder's `Dockerfile`, and its
test stage at `pytest test/tests/ -v` (adjust the path to wherever this
folder lives in your pipeline config). To test a rollback scenario, build a
second image tag with `INJECT_ERRORS=true` baked in (or set it at deploy
time on the canary Deployment) and confirm your pipeline detects the
regression and rolls back instead of promoting it.
