FROM python:3.10-slim

WORKDIR /app

# Copy everything
COPY . /app

RUN apt-get update && apt-get install -y git

# Install deps
RUN pip install --no-cache-dir -r requirements.txt

# Run server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]