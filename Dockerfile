FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

WORKDIR /app

# Install lightweight CPU PyTorch first so cloud Docker builds stay fast and small (~600MB instead of 4GB CUDA)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

COPY . .

# Pre-generate calibrated EMIT NetCDF4 benchmark scenes at container build time
RUN python src/benchmark_generator.py

EXPOSE 7860 8000

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-7860}"]
