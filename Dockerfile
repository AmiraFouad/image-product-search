# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install required dependencies
RUN apt-get update && apt-get install -y unzip curl && \
    apt-get install -y google-chrome-stable

# Set Chrome binary path
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"
ENV PATH="${PATH}:${GOOGLE_CHROME_BIN}"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ChromeDriver manually from your repo
COPY drivers/chromedriver /usr/local/bin/chromedriver
RUN chmod +x /usr/local/bin/chromedriver  # Ensure it has execution permissions

# Copy the rest of the application
COPY . .

# Expose port 5000
EXPOSE 5000

# Start the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
