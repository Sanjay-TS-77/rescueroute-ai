FROM --platform=linux/arm64 python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM --platform=linux/arm64 python:3.13-slim
RUN useradd -r -u 1001 appuser
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8080
CMD ["uvicorn", "rescueroute.runtime_http:app", "--host", "0.0.0.0", "--port", "8080"]
