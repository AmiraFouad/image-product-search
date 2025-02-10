# Use an official lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y wget curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb

# Install ChromeDriver (matching Chrome version)
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROME_VERSION/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Set Chrome binary path
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"
ENV PATH="${PATH}:/usr/local/bin"

# Copy only necessary files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port 5000
EXPOSE 5000

# Start the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
