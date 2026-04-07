FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple

WORKDIR /app

COPY vendor/uv-0.8.22-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl /tmp/uv-0.8.22-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
RUN pip install --no-cache-dir /tmp/uv-0.8.22-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl \
    && rm -f /tmp/uv-0.8.22-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

COPY pyproject.toml uv.lock ./
RUN uv export --no-dev --frozen --no-editable --no-emit-project --no-hashes --output-file requirements.deploy.txt
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
RUN pip install --no-cache-dir -r requirements.deploy.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/scripts /app/scripts

RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import json, urllib.request; response = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); payload = json.load(response); raise SystemExit(0 if payload.get('status') == 'healthy' else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
