FROM python:3.10-slim

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

COPY ml_engine/tests/requirements-ci.txt .

RUN pip install --no-cache-dir -r requirements-ci.txt

RUN pip install torch==2.0.1+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html

WORKDIR /workspace