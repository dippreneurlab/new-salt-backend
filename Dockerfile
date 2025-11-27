FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

FROM base AS builder
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

# Cloud Run requires the container to listen on $PORT (default 8080)
ENV PORT=8080

COPY --from=builder /opt/venv /opt/venv
COPY . .

EXPOSE 8080

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
