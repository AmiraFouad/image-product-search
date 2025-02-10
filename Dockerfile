# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies and Chrome
RUN apt-get update && apt-get install -y wget curl unzip \
    && wget -q -O google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome.deb \
    && rm google-chrome.deb \
    && wget -q https://chromedriver.storage.googleapis.com/$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip \
    && apt-get clean

# Set Chrome and ChromeDriver environment variables
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"
ENV CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
ENV PATH="${PATH}:/usr/local/bin/"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 5000
EXPOSE 5000

# Start the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
