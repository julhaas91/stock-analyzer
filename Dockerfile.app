FROM python:3.12.3-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Set environment variables
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV GCP_PROJECT_ID="julius-private-sandbox"
ENV GCP_PROJECT_NUMBER="815648219579"
ENV GCP_BUCKET_NAME="stock-advisor-cache"

# Copy dependency management files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

# Copy application files
COPY src/ .
COPY .env .
COPY header.png .

CMD uv run streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port=$PORT