FROM python:3.9-slim

WORKDIR /app

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    chromium \
    chromium-driver

# Set Chrome and ChromeDriver environment variables
ENV CHROMEDRIVER_PATH="/usr/lib/chromium/chromedriver"
ENV GOOGLE_CHROME_BIN="/usr/bin/chromium"

# Install required Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Start the application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
