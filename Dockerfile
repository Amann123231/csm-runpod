FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Set working directory
WORKDIR /app

# Install git and other dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    huggingface_hub \
    transformers \
    torchaudio \
    soundfile \
    fastapi \
    uvicorn \
    python-multipart \
    runpod

# Clone the CSM repository
RUN git clone https://github.com/SesameAILabs/csm.git /app/csm

# Install CSM requirements
WORKDIR /app/csm
RUN pip install --no-cache-dir -r requirements.txt

# Copy the handler script
WORKDIR /app
COPY handler.py /app/

# Set environment variables
ENV PYTHONPATH=/app:/app/csm

# RunPod API will run the handler.py file
CMD ["python", "-u", "handler.py"] 