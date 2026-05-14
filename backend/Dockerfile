FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch first so pip doesn't pull in the full CUDA stack.
# The CUDA wheel is ~2 GB; the CPU wheel is ~250 MB and sufficient for inference.
RUN pip install --no-cache-dir \
    torch>=2.2.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
