FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (WeasyPrint requires some libs)
RUN apt-get update && apt-get install -y \
    libmagic-dev \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo2-dev \
    python3-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the code
COPY . /app/

# Expose the port
EXPOSE 8000

# Default command (overridden by docker-compose for dev)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
