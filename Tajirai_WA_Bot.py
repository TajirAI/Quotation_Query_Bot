import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import time
import os
import json
from rapidfuzz import fuzz
from fpdf import FPDF
import re

class processor:
    def __init__(self,):
        self.pdf_path = ""
        self.mill_names = ["Crescent Textile Mills", "Mahmood Textile Mills Ltd", "Interloop Limited", "Fateh Textile Mill", "Nishat Mills Limited"]
        self.PRODUCTS_FILE = "product_prices.json"
        self.CATEGORIES_FILE = "categories.json"      
        self.product_data = self.load_data(self.PRODUCTS_FILE)
        self.category_data = self.load_data(self.CATEGORIES_FILE)

    def load_data(self,file_path):
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        return {}

    def save_to_pdf(self,text, file_name="Mill_Quotation.pdf"):
        """Save cleaned text to a PDF."""
        # Remove time from the text using regex
        text_without_time = re.sub(r'\b\d{1,2}:\d{2}(?:\s?[APap][Mm])?\b', '', text)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add a title to the PDF
        pdf.cell(200, 10, txt="Mill_Quotation", ln=True, align="C")

        # Add the content as it is
        pdf.multi_cell(0, 10, txt=text_without_time.strip())  # Use multi_cell to handle line breaks automatically

        pdf.output(file_name)
        print(f"Saved data to {file_name}")

        # Return the absolute path of the saved PDF
        return os.path.abspath(file_name)

    def send_pdf_in_chat(self,driver, file_path):
        try:
            # Locate the attachment button
            attach_button = driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span/div/div[1]/div[2]/button')
            attach_button.click()
            # Locate the file input element and upload the PDF
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(file_path)
            time.sleep(1)  # Short delay to allow the file to upload

            # Locate and click the send button
            send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@data-icon='send']"))
            )
            send_button.click()
            print(f"Sent PDF: {file_path}")
        except NoSuchElementException as e:
            print(f"Could not send PDF: {str(e)}")

    def functionality(self,query_input):
        query_input_new = query_input
        query_input = str(query_input).lower()
        print(query_input)
        
        results = []  # Initialize an empty list to store results
        
        for product_name, product in self.product_data.items():
            if query_input == product_name.lower().strip():  # Normalize product name for comparison
                results.append(f"{product_name}: {product['purchase_price']}/{product['selling_price']}")
                return results  # Return the exact match as a list
            
        category_matches = {
            name: details
            for name, details in self.product_data.items()
            if details["category"].lower() == query_input
        }

        matches = []

        keys = ['Product:', 'Mill:', 'Price:', 'Date:']

        for product_name in self. product_data.keys():
            similarity_score = fuzz.token_set_ratio(query_input, product_name)
            if similarity_score >= 75:  # Threshold for similarity
                matches.append((product_name, similarity_score))
        
        # Check if the message content matches "Mills Name"

        if "mills name" in query_input:
            response_message = ",".join(self.mill_names)
            print("Sent response with mill names.")
            return response_message
        elif all(key in query_input_new for key in keys):
            print("entered")
            self.pdf_path = self.save_to_pdf(query_input_new)  # Save the message content to PDF
            pdfer = "pdfer"
            return pdfer
        elif "category" == query_input or "categories" == query_input:
            return self.category_data["categories"]  # Assuming this is a list
        elif category_matches:
            for name, details in category_matches.items():
                results.append(
                    f"{name}: {details['purchase_price']}/{details['selling_price']}"
                )
            return results  # Return as a list
        elif matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            best_match, score = matches[0]
            product = self.product_data[best_match]
            results.append(f"{best_match}: {product['purchase_price']}/{product['selling_price']}")
            return results  # Return as a list
        else:
            return None
    
    def run_browser(self,):
        options = uc.ChromeOptions()
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("user-data-dir=C:\\Users\\Qasim Hameed\\AppData\\Local\\Google\\Chrome\\User Data")
        options.add_argument("--profile-directory=Profile 14")

        print("Initializing Chrome Driver!")
        driver = uc.Chrome(options=options)
        driver.maximize_window()

        try:
            driver.get("https://web.whatsapp.com/")
            print("Waiting for WhatsApp Web to load...")
            time.sleep(10)
            actions = ActionChains(driver)

            while True:
                unread_chats = driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'unread message')]")

                if unread_chats:
                    for i, unread in enumerate(unread_chats[1:], start=1):
                        try:
                            unread_count = int(unread.text)
                        except ValueError:
                            print("Could not read unread count; skipping this chat.")
                            continue

                        try:
                            chat_container = unread
                            chat_container.click()
                            time.sleep(1)

                            incoming_messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]//span[@class='_ao3e selectable-text copyable-text']")
                            unread_messages = incoming_messages[-unread_count:]
                            for j, message in enumerate(unread_messages, start=1):
                                message_text = message.text
                                print(f"Query: {message_text}")
                                result = self.functionality(query_input=message_text)
                                answer = driver.find_element(By.XPATH, "//div[@aria-placeholder='Type a message']")
                                if isinstance(result, list):  # Check if the result is a list
                                    print("case1")          
                                    for i in result:
                                        answer.send_keys(i)
                                        answer.send_keys(Keys.SHIFT, Keys.ENTER)
                                    actions.key_down(Keys.ENTER).perform()
                                elif result == "pdfer":
                                    print("case2")
                                    self.send_pdf_in_chat(driver, self.pdf_path)
                                elif result == None:
                                    pass
                                else:
                                    print("case3")
                                    answer.send_keys(result)
                                    actions.key_down(Keys.ENTER).perform()


                        except NoSuchElementException as e:
                            print(f"Could not find chat container: {str(e)}")
                            continue
                        except TimeoutException:
                            print("Timeout while waiting for chat to be clickable.")
                            continue

                try:
                    pinned_chat = driver.find_element(By.XPATH, "//span[@data-icon='pinned2']")
                    pinned_chat.click()
                    time.sleep(1)
                except NoSuchElementException:
                    print("Pinned chat not found.")

                time.sleep(2)
        except (WebDriverException, NoSuchElementException) as e:
            print(f"An error occurred: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                    print("Driver quit successfully.")
                except WebDriverException as e:
                    print(f"Error during driver quit: {str(e)}")

processing = processor()
processing.run_browser()