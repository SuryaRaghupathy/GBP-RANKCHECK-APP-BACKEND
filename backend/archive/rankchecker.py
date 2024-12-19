# from flask import Flask, request, jsonify, send_file, url_for
# import os
# import pandas as pd
# import logging
# from flask_cors import CORS
# import random
# import time
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# import json

# # Initialize Flask app
# app = Flask(__name__)
# CORS(app)

# # Directories for upload and result files
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
# RESULT_FOLDER = os.path.join(BASE_DIR, "results")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(RESULT_FOLDER, exist_ok=True)

# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['RESULT_FOLDER'] = RESULT_FOLDER

# # Set up logging
# logging.basicConfig(filename="debug.log", level=logging.ERROR, format='%(asctime)s %(levelname)s: %(message)s')

# def random_delay():
#     """Introduce a random delay to mimic human behavior."""
#     time.sleep(random.uniform(2, 5))

# def simulate_realistic_interaction(driver):
#     """Simulate realistic user interactions with error handling."""
#     try:
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(random.uniform(1, 3))
#         actions = ActionChains(driver)
#         actions.move_by_offset(random.randint(0, 50), random.randint(0, 50)).perform()
#     except Exception as e:
#         logging.error(f"Error during interaction simulation: {e}")

# def restart_browser(driver):
#     """Restart the browser to prevent IP blocking issues."""
#     try:
#         driver.quit()
#     except Exception as e:
#         logging.warning(f"Error while closing the browser: {e}")
#     options = webdriver.ChromeOptions()
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')
#     return webdriver.Chrome(options=options)

# def process_csv(file_path):
#     """
#     Process the uploaded CSV file, perform Selenium scraping,
#     and save the results with extracted rankings and positions.
#     """
#     processed_file_path = os.path.join(app.config['RESULT_FOLDER'], 'updated_keyword_and_branch_lists_with_positions.csv')
#     try:
#         # Read the CSV file
#         try:
#             df = pd.read_csv(file_path, encoding="utf-8")
#         except UnicodeDecodeError:
#             df = pd.read_csv(file_path, encoding="ISO-8859-1")

#         # Convert DataFrame to JSON
#         data = df.to_dict(orient="records")

#         # Initialize Selenium WebDriver
#         options = webdriver.ChromeOptions()
#         options.add_argument('--headless')
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-dev-shm-usage')
#         driver = webdriver.Chrome(options=options)

#         try:
#             for idx, entry in enumerate(data):
#                 # Restart browser every 10 iterations to prevent blocking
#                 if idx > 0 and idx % 10 == 0:
#                     driver = restart_browser(driver)

#                 keyword = entry.get("Keyword", "default search term")
#                 brand = entry.get("Brand", "")
#                 branch = entry.get("Branch", "")

#                 # Open Google UK
#                 driver.get("https://www.google.co.uk/?gl=uk")
#                 random_delay()
                
#                 # Perform search
#                 search_bar = driver.find_element(By.NAME, "q")
#                 search_bar.clear()
#                 search_bar.send_keys(keyword)
#                 search_bar.send_keys(Keys.RETURN)
#                 random_delay()

#                 try:
#                     # Extract Maps link
#                     maps_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Maps")
#                     maps_url = maps_link.get_attribute("href")

#                     driver.get(maps_url)
#                     random_delay()

#                     # Scroll and extract ranking list
#                     scrollable_div = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
#                     last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)

#                     while True:
#                         driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
#                         time.sleep(random.uniform(2, 5))
#                         new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
#                         if new_height == last_height:
#                             break
#                         last_height = new_height

#                     elements = driver.find_elements(By.CLASS_NAME, "qBF1Pd.fontHeadlineSmall")
#                     extracted_texts = [element.text for element in elements]
#                     entry["ranking_list"] = extracted_texts

#                     # Find brand and branch position
#                     entry["position"] = None
#                     for index, element in enumerate(extracted_texts):
#                         if brand in element and branch in element:
#                             entry["position"] = index + 1
#                             break
#                 except Exception as e:
#                     logging.error(f"Error extracting rankings for keyword '{keyword}': {e}")
#                     entry["ranking_list"] = []
#                     entry["position"] = None

#                 # Print each ranking list and position
#                 print(f"Keyword: {keyword}")
#                 print(f"Ranking List: {entry['ranking_list']}")
#                 print(f"Position: {entry['position']}")

#         finally:
#             driver.quit()

#         # Save updated data as JSON
#         updated_json_file = os.path.join(app.config['RESULT_FOLDER'], 'updated_keyword_and_branch_lists_with_positions.json')
#         with open(updated_json_file, "w", encoding="utf-8") as jsonfile:
#             json.dump(data, jsonfile, indent=4, ensure_ascii=False)

#         # Convert updated data back to CSV
#         df_updated = pd.DataFrame(data)
#         df_updated.to_csv(processed_file_path, index=False, encoding="utf-8")
#         logging.info(f"Processed data saved to {processed_file_path}")
#         return processed_file_path
#     except Exception as e:
#         logging.error(f"Error processing CSV file: {e}")
#         raise

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     """Handle file upload and initiate processing."""
#     if 'file' not in request.files:
#         return jsonify({"error": "No file provided"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No file selected"}), 400
#     if not file.filename.endswith('.csv'):
#         return jsonify({"error": "Invalid file type. Only CSV files are allowed."}), 400

#     # Clear previous files in the upload folder
#     for existing_file in os.listdir(app.config['UPLOAD_FOLDER']):
#         existing_file_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_file)
#         if os.path.isfile(existing_file_path):
#             os.remove(existing_file_path)

#     # Save the uploaded file
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#     file.save(file_path)
#     logging.info(f"File uploaded: {file_path}")

#     try:
#         # Process the uploaded file
#         result_file = process_csv(file_path)

#         # Generate the result file download URL
#         result_url = url_for('download_result', filename=os.path.basename(result_file), _external=True)
#         return jsonify({"result_url": result_url})
#     except Exception as e:
#         logging.error(f"Error processing uploaded file: {e}")
#         return jsonify({"error": str(e)}), 500

# @app.route('/results/<filename>', methods=['GET'])
# def download_result(filename):
#     """Allow users to download the processed results."""
#     try:
#         result_path = os.path.join(app.config['RESULT_FOLDER'], filename)
#         if os.path.exists(result_path):
#             return send_file(result_path, as_attachment=True)
#         else:
#             logging.warning(f"File not found: {filename}")
#             return jsonify({"error": "File not found"}), 404
#     except Exception as e:
#         logging.error(f"Error serving file '{filename}': {e}")
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)