from flask import Flask, request, render_template, jsonify, send_file
import os
import requests
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import uuid
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Set up Chrome options
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/google-chrome"
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Ensure ChromeDriver has the correct path and permissions
chrome_driver_path = "/usr/local/bin/chromedriver"
os.chmod(chrome_driver_path, 0o755)  # Make sure it's executable

# Start the ChromeDriver service
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Initialize Flask app
app = Flask(__name__)

UPLOAD_FOLDER = os.path.abspath('uploads/')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

global_search_data = {
    "current_country_index": 0,
    "selected_countries": [],
    "product_data": {},
    "image_paths": []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    global global_search_data
    if 'files' not in request.files or 'countries' not in request.form:
        return jsonify({'error': 'No file or countries selected'}), 400

    files = request.files.getlist('files')
    selected_countries = request.form.getlist('countries')

    image_paths = []

    for file in files:
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filename = f"{uuid.uuid4()}-{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        image_paths.append(file_path)

    global_search_data["current_country_index"] = 0
    global_search_data["selected_countries"] = selected_countries
    global_search_data["product_data"] = {}
    global_search_data["image_paths"] = image_paths

    return process_next_country()

def process_next_country():
    global global_search_data
    index = global_search_data["current_country_index"]
    if index >= len(global_search_data["selected_countries"]):
        return render_template('no_more_countries.html')

    country = global_search_data["selected_countries"][index]
    products = reverse_image_search_multiple(global_search_data["image_paths"], country)
    global_search_data["product_data"][country] = products
    return render_template('results.html', products=products, current_country=country, next_available=True,
                           final_step=False)

def reverse_image_search_multiple(image_paths, country):
    wait = WebDriverWait(driver, 30)
    results = []

    try:
        for image_path in image_paths:
            driver.get("https://images.google.com/?hl=en")
            camera_icon = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Search by image']")))
            camera_icon.click()

            file_input = wait.until(EC.presence_of_element_located((By.NAME, "encoded_image")))
            file_input.send_keys(image_path)

            products_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nPDzT[jsname='VIftV']")))
            products_tab.click()

            search_box = wait.until(EC.presence_of_element_located((By.ID, "APjFqb")))
            search_box.click()
            search_box.send_keys(Keys.SPACE + country)
            time.sleep(1)
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)

            product_links = driver.execute_script("""
                return Array.from(document.querySelectorAll('a.LBcIee')).map(link => link.href);
            """)

            for product_link in product_links:
                product_details = extract_product_details(product_link)
                if product_details:
                    results.append(product_details)
    except Exception as e:
        print(f"Error in image search: {e}")
    return results

def extract_product_details(product_link):
    try:
        response = requests.get(product_link, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text if soup.find('title') else 'No title available'
        description_tag = soup.find("meta", attrs={"name": "description"})
        description = description_tag["content"] if description_tag else "No description available"

        price_selectors = [
            "meta[property='og:price:amount']",
            "span.price",
            "span[class*='price']",
            "div[class*='price']",
            "p[class*='price']",
            "span[data-price]",
            "meta[itemprop='price']",
            "div[class*='product-price']",
            "span[class*='current-price']",
            "div[class*='sale-price']",
            "div[class*='product-now-price']",
            "span[class*='product-now-price']",
            "span[class*='STRPrice  STRPrice_red']"
        ]

        price = "Price not found"
        for selector in price_selectors:
            price_element = soup.select_one(selector)
            if price_element:
                price = price_element.get_text(strip=True) if price_element.name != 'meta' else price_element.get(
                    'content', '').strip()
                break

        return {
            "website": product_link.split('/')[2],
            "product_name": title,
            "price": price,
            "description": description,
            "product_link": product_link
        }
    except Exception as e:
        print(f"Error extracting product details: {e}")
        return None

@app.route('/next-country')
def next_country():
    global global_search_data
    global_search_data["current_country_index"] += 1
    if global_search_data["current_country_index"] >= len(global_search_data["selected_countries"]):
        return render_template('no_more_countries.html')
    return process_next_country()

@app.route('/auto-download/<country>')
def auto_download(country):
    df = pd.DataFrame(global_search_data["product_data"].get(country, []))
    excel_io = BytesIO()
    df.to_excel(excel_io, index=False, engine='xlsxwriter')
    excel_io.seek(0)
    return send_file(excel_io, download_name=f'{country}.xlsx', as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(debug=True, host='0.0.0.0', port=port)
