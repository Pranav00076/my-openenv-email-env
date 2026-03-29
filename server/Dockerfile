FROM python:3.10-slim

WORKDIR /app
COPY . /app

# Install system deps
RUN apt-get update && apt-get install -y git

# Copy requirements
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run server
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port 7860"]