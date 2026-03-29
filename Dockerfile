FROM python:3.10-slim

WORKDIR /app

# Copy everything
COPY . /app

# Install deps
RUN pip install --no-cache-dir -r server/requirements.txt

# Run server
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port 7860"]