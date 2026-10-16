# Small, non-root production image for Taskflow.
# Base pinned by digest (immutable, like the action SHAs); Dependabot keeps it current.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

# The pipeline passes the commit SHA here; /health reports it after deploy.
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
# Render (and most hosts) tell the app which port to use via $PORT.
# exec: uvicorn replaces the shell as PID 1, so it receives SIGTERM and stops cleanly.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
