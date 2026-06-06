FROM python:3.12-slim

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .

EXPOSE 8000

# BUG 1 — uvicorn is told to listen on port 9000.
# The compose file maps 8000:8000 (host:container), so host port 8000
# forwards to container port 8000 — but nothing is listening there.
# Symptom:  curl localhost:8000 → connection refused
# Find it:  docker logs <container>  (shows the port uvicorn actually bound)
# Fix:      change 9000 to 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
