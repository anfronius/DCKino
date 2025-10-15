FROM mcr.microsoft.com/playwright/python:v1.54.0-noble

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (Playwright already installed in base image)
RUN pip install --no-cache-dir -r requirements.txt

# Copy scraping application code
COPY DCKinoSites/ ./DCKinoSites/

# Create data directories and link DCKinoSites/data to /app/data for volume mount
RUN mkdir -p /app/data && \
    rm -rf /app/DCKinoSites/data && \
    ln -s /app/data /app/DCKinoSites/data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create .scrapy cache directory
RUN mkdir -p /app/DCKinoSites/.scrapy

# Set working directory to DCKinoSites for scrapy commands
WORKDIR /app/DCKinoSites

# Default command runs the spider script only - no data processing
CMD ["python", "utils/run_spiders.py"]