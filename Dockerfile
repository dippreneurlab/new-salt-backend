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
ENV PORT=5010

COPY --from=builder /opt/venv /opt/venv

EXPOSE 5010
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "5010"]
