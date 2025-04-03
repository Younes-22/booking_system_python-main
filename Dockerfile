# Builder stage
FROM python:3.10-slim AS builder
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.10-slim
WORKDIR /app

# Install MySQL client (only needed if your app runs mysql commands)
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

# Copy necessary files
COPY --from=builder /root/.local /root/.local
COPY app/ .

ENV PATH=/root/.local/bin:$PATH

# Directly start your application
CMD ["python", "app.py"]

#from yt vid
#multi stage builds