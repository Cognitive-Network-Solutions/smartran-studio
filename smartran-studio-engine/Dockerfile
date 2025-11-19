# Use official RAPIDS notebooks image with CUDA 12 support
# This includes cuDF, cuML, cuGraph, dask-cudf, and Jupyter notebooks pre-installed
FROM rapidsai/notebooks:25.06-cuda12.8-py3.11

# Set non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /workspace

# Copy your development dependencies
COPY requirements.txt /workspace/requirements.txt


# Clean any CPU TF and install a Sionna-compatible TF with its CUDA/cuDNN
RUN pip install --upgrade pip \
    && pip uninstall -y tensorflow tensorflow-cpu tf-nightly || true \
    && pip install --no-cache-dir "tensorflow[and-cuda]==2.19.*" \
    && pip install --no-cache-dir sionna==1.1.0 \
    && pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY cns_sionna_sim.py ./
COPY sionna_sim_helpers.py ./



# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
