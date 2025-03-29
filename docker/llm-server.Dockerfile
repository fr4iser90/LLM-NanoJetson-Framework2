# LLM Server für Jetson Nano
FROM nvcr.io/nvidia/l4t-ml:r35.2.1-py3

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Optimierungen für Jetson
RUN echo "export OPENBLAS_NUM_THREADS=4" >> ~/.bashrc
RUN echo "export CUDA_LAUNCH_BLOCKING=1" >> ~/.bashrc

# Copy source code
COPY src /app/src

CMD ["python3", "-m", "src.llm.server"] 