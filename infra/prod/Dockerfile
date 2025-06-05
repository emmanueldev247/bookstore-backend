FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application code (assume you've committed everything you need)
COPY . .

# Ensure scripts are executable
RUN chmod +x /app/infra/scripts/entrypoint.web.sh \
    && chmod +x /app/infra/scripts/entrypoint.worker.sh

# Expose the same port
EXPOSE 5000

# Default entrypoint: run the web script (which in production branch will run `python run.py`)
ENTRYPOINT ["/app/infra/scripts/entrypoint.web.sh"]
