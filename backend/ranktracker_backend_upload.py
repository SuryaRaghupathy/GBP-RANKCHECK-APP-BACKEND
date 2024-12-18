import os
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from flask import Flask, request, jsonify, send_file, url_for
from flask_cors import CORS
from fake_useragent import UserAgent
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure upload and result folders
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
RESULT_FOLDER = os.path.join(BASE_DIR, "results")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Set up logging
logging.basicConfig(filename="debug.log", level=logging.ERROR)


def random_delay():
    """Introduce a random delay to mimic human behavior."""
    time.sleep(random.uniform(5, 15))


def simulate_realistic_interaction(driver):
    """Simulate realistic user interactions with error handling."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 3))  # Mimic human pause
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(0, 50), random.randint(0, 50)).perform()
    except Exception as e:
        logging.error(f"Error during interaction simulation: {e}")


def fetch_all_rankings(driver):
    """Scrolls down the page and fetches all ranking elements safely."""
    rankings = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Find ranking elements
        try:
            elements = driver.find_elements(By.CLASS_NAME, "qBF1Pd.fontHeadlineSmall")
            rankings += [el.text for el in elements if el.text not in rankings]  # Avoid duplicates
        except Exception as e:
            logging.error(f"Error fetching ranking elements: {e}")

        # Scroll down incrementally
        try:
            driver.execute_script("window.scrollBy(0, 300);")  # Scroll incrementally
            time.sleep(random.uniform(2, 4))  # Add delay to let elements load
        except Exception as e:
            logging.error(f"Error during scrolling: {e}")
            break  # Stop scrolling if an error occurs

        # Check if new elements are loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Exit loop if no new elements are loaded
        last_height = new_height

    return rankings


def process_csv(file_path):
    """Processes a CSV file to extract ranking information using Selenium."""
    ua = UserAgent()
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={ua.random}")  # Use random user agent

    driver = webdriver.Chrome(options=options)

    results = []

    try:
        df = pd.read_csv(file_path)
        for i, row in df.iterrows():
            if i > 30:  # Limit to 30 searches per session
                logging.error("Request limit reached. Restarting browser.")
                driver.quit()
                driver = webdriver.Chrome(options=options)

            keyword = row.get("Keyword", "default search")
            brand = row.get("Brand", "")
            branch = row.get("Branch", "")

            driver.get("https://www.google.co.uk/?gl=uk")
            random_delay()

            search_bar = driver.find_element(By.NAME, "q")
            search_bar.send_keys(keyword)
            search_bar.send_keys(Keys.RETURN)
            random_delay()

            try:
                maps_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Maps")
                maps_url = maps_link.get_attribute("href")
                driver.get(maps_url)
                random_delay()

                # Fetch all rankings by scrolling
                rankings = fetch_all_rankings(driver)
                position = next(
                    (idx + 1 for idx, el in enumerate(rankings) if brand in el and branch in el), None
                )

                simulate_realistic_interaction(driver)

                results.append({
                    "Keyword": keyword,
                    "Ranking List": rankings,
                    "Position": position,
                })

            except Exception as e:
                logging.error(f"Error fetching data for keyword '{keyword}': {e}")
                results.append({
                    "Keyword": keyword,
                    "Ranking List": [],
                    "Position": None,
                })

    finally:
        driver.quit()

    # Save results
    result_file = os.path.join(app.config['RESULT_FOLDER'], "results.csv")
    pd.DataFrame(results).to_csv(result_file, index=False)
    return result_file


@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint to handle file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file type. Only CSV allowed"}), 400

    # Clear the upload folder
    for existing_file in os.listdir(app.config['UPLOAD_FOLDER']):
        existing_file_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_file)
        if os.path.isfile(existing_file_path):
            os.remove(existing_file_path)

    # Save the new file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        result_file = process_csv(file_path)
        result_url = url_for('download_result', filename=os.path.basename(result_file), _external=True)
        return jsonify({"result_url": result_url})
    except Exception as e:
        logging.error(f"Error processing uploaded file: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/results/<filename>', methods=['GET'])
def download_result(filename):
    """Endpoint to download the processed results."""
    result_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    if os.path.exists(result_path):
        return send_file(result_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
