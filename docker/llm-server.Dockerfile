# Use the official L4T ML container
FROM nvcr.io/nvidia/l4t-ml:r35.2.1-py3

WORKDIR /app

# System dependencies (only add what's not in base image)
RUN apt-get update && apt-get install -y \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Jetson optimizations
ENV OPENBLAS_NUM_THREADS=4
ENV CUDA_LAUNCH_BLOCKING=1

# Copy source code
COPY src /app/src

CMD ["python3", "-m", "src.llm.server"] 