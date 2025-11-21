import time
import logging
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

class PropertyScraper:
    def __init__(self, base_url, output_file="properties.csv"):
        self.base_url = base_url
        self.output_file = output_file
        self.data = []
        
        # Setup Chrome Options
        self.options = Options()
        self.options.add_argument("--headless")  # Run in background
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize Driver using WebDriver Manager
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def fetch_page(self):
        """Loads the page and handles dynamic scrolling."""
        try:
            logging.info(f"Navigating to {self.base_url}...")
            self.driver.get(self.base_url)
            
            # Wait for listing container (Update 'listing-card' to actual class name)
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll to bottom to trigger any lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) # Allow rendering
            
            return self.driver.page_source
        except Exception as e:
            logging.error(f"Error fetching page: {e}")
            return None

    def parse_html(self, html_content):
        """Parses HTML using BeautifulSoup."""
        if not html_content:
            return

        soup = BeautifulSoup(html_content, "html.parser")
        
        # UPDATE THESE SELECTORS based on your target website
        # Example selectors are generic placeholders
        listings = soup.find_all("article", class_="property-listing") 
        
        logging.info(f"Found {len(listings)} potential listings.")

        for card in listings:
            try:
                # Extract Title
                title_tag = card.find("h2", class_="title")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                # Extract Price
                price_tag = card.find("div", class_="price")
                price = price_tag.get_text(strip=True) if price_tag else "0"
                
                # Extract Address
                addr_tag = card.find("span", class_="address")
                address = addr_tag.get_text(strip=True) if addr_tag else "N/A"

                # Extract Link
                link_tag = card.find("a", href=True)
                link = link_tag['href'] if link_tag else ""
                if link and not link.startswith("http"):
                    link = self.base_url + link

                entry = {
                    "Title": title,
                    "Price": price,
                    "Address": address,
                    "URL": link
                }
                self.data.append(entry)
                
            except Exception as e:
                logging.warning(f"Skipping item due to error: {e}")

    def save_to_csv(self):
        """Exports data to CSV."""
        if not self.data:
            logging.warning("No data to save.")
            return

        df = pd.DataFrame(self.data)
        
        # Basic Data Cleaning
        df['Price'] = df['Price'].replace(r'[$,]', '', regex=True)
        df.drop_duplicates(subset=['URL'], inplace=True)
        
        df.to_csv(self.output_file, index=False)
        logging.info(f"Data saved to {self.output_file}. Total records: {len(df)}")

    def close(self):
        self.driver.quit()

    def run(self):
        html = self.fetch_page()
        self.parse_html(html)
        self.save_to_csv()
        self.close()

if __name__ == "__main__":
    # REPLACE THIS URL with the real property site you want to scrape
    TARGET_URL = "https://www.example.com/real-estate/listings"
    
    scraper = PropertyScraper(base_url=TARGET_URL)
    scraper.run()
