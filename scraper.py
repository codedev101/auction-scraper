import sys
import os
import requests
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import statistics
import traceback
import io
import pandas as pd

# Google Gemini API imports
from google import genai

class AuctionScraper:
    def __init__(self, gemini_api_keys, ui_placeholders):
        self.running = True
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.products = []
        self.percentages = []
        self.ui = ui_placeholders
        self.gemini_api_keys = [key for key in gemini_api_keys if key]
        self.current_api_key_index = 0
        self.gemini_client = None
        
        # Rate limiting variables
        self.request_times = []
        self.max_requests_per_minute = 10
        
        if self.gemini_api_keys:
            self.setup_gemini()

    def stop(self):
        self.running = False

    def setup_gemini(self):
        try:
            if not self.gemini_api_keys:
                self.ui['status'].warning("No Gemini API keys found.")
                return

            api_key = self.gemini_api_keys[self.current_api_key_index]
            self.gemini_client = genai.Client(api_key=api_key)
            self.ui['status'].info(f"AI price lookup enabled with Gemini Client (API Key {self.current_api_key_index + 1})")

        except Exception as e:
            self.ui['status'].error(f"An unexpected error occurred setting up Gemini AI: {e}.")
            self.gemini_client = None
            traceback.print_exc()

    def can_make_request(self):
        """Check if we can make a request without hitting rate limits"""
        now = datetime.now()
        self.request_times = [req_time for req_time in self.request_times if now - req_time < timedelta(minutes=1)]
        return len(self.request_times) < self.max_requests_per_minute

    def wait_for_rate_limit(self):
        """Wait until we can make another request"""
        while not self.can_make_request():
            if self.request_times:
                oldest_request = min(self.request_times)
                wait_time = 60 - (datetime.now() - oldest_request).total_seconds()
                if wait_time > 0:
                    self.ui['status'].info(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                    time.sleep(max(1, wait_time))
            else:
                break

    def record_request(self):
        """Record that we made a request"""
        self.request_times.append(datetime.now())

    def get_retail_price(self, product_name, image_url):
        if not self.gemini_client:
            return None
            
        for attempt in range(len(self.gemini_api_keys)):
            try:
                self.wait_for_rate_limit()
                
                response = requests.get(image_url, headers=self.headers, stream=True, timeout=15)
                if response.status_code != 200:
                    print(f"Failed to download image: {image_url}")
                    return None
                
                image_bytes = response.content
                
                prompt_text = f"""
                **Task**: Find the retail price and a direct product link for the item in the image, described as '{product_name}'.
                **Output Format**: You MUST reply ONLY in the format: `PRICE, URL`. Example: `199.99, https://www.amazon.com/product`.
                **Rules**:
                1. If you cannot find the exact item, find the CLOSEST SIMILAR item from a major retailer (Amazon, Walmart, etc.). NEVER return "NONE" or "Not Found".
                2. The price must be a number only (e.g., `123.45`). No currency symbols.
                3. The URL must be a direct retail link, not an auction site.
                Your entire response must be just the price and the link, separated by a comma.
                """
                
                contents = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt_text},
                            {"inline_data": {"mime_type": "image/png", "data": image_bytes}}
                        ]
                    }
                ]
                
                self.record_request()
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents
                )

                response_text = response.text.strip()
                match = re.search(r'([\d,]+\.?\d*)\s*,\s*(https?://\S+)', response_text)
                if match:
                    price = match.group(1).replace(',', '')
                    link = match.group(2)
                    return f"{price}, {link}"
                else:
                    print(f"AI response format invalid: {response_text}")
                    raise ValueError("Invalid AI response format")

            except Exception as e:
                error_str = str(e)
                
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    self.ui['status'].warning("Rate limit hit! Waiting 30 seconds before retry...")
                    time.sleep(30)
                    
                    try:
                        self.record_request()
                        response = self.gemini_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=contents
                        )
                        response_text = response.text.strip()
                        match = re.search(r'([\d,]+\.?\d*)\s*,\s*(https?://\S+)', response_text)
                        if match:
                            price = match.group(1).replace(',', '')
                            link = match.group(2)
                            return f"{price}, {link}"
                    except Exception as retry_e:
                        self.ui['status'].warning(f"Retry failed: {retry_e}")
                
                print("\n--- ERROR IN get_retail_price ---")
                traceback.print_exc()
                print("---------------------------------\n")
                
                self.current_api_key_index = (self.current_api_key_index + 1) % len(self.gemini_api_keys)
                self.ui['status'].warning(f"Switching to Gemini API Key {self.current_api_key_index + 1} due to error.")
                self.setup_gemini()
                self.request_times = []
        
        self.ui['status'].error("All Gemini API keys failed. Disabling AI for this session.")
        self.gemini_client = None
        return None

    def run(self, site, url, start_page, end_page):
        try:
            # Use requests-based scraping instead of Selenium
            self.ui['status'].info("Starting scraper with requests-based approach (Cloud compatible)")
            
            if site == "HiBid": 
                self.scrape_hibid_requests(url, start_page, end_page)
            else:
                self.ui['status'].error(f"Only HiBid is supported in cloud mode currently. {site} requires Selenium.")
                
        except Exception as e:
            self.ui['status'].error(f"An unexpected error occurred during scraping: {e}")
            traceback.print_exc()
        
        return self.products

    def scrape_hibid_requests(self, url, start_page, end_page):
        """HiBid scraping using requests only (no Selenium needed)"""
        base_url = url.split("/catalog")[0]
        page = start_page
        
        while self.running and (end_page == 0 or page <= end_page):
            self.ui['status'].info(f"Scraping HiBid Page: {page}...")
            current_url = f"{url}{'&' if '?' in url else '?'}apage={page}"
            
            try:
                response = requests.get(current_url, headers=self.headers, timeout=30)
                if response.status_code != 200:
                    self.ui['status'].error(f"Failed to load page {page}")
                    break
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                products = [p for p in soup.find_all("app-lot-tile") if p.find("strong", class_="lot-price-realized")]
                
                if not products:
                    self.ui['status'].success("No more items with prices. Scraping complete.")
                    break

                self.ui['metrics']['pages'].metric("Pages Scraped", page)

                for i, p in enumerate(products, 1):
                    if not self.running: 
                        break
                        
                    title_tag = p.find("h2", class_="lot-title")
                    link_tag = p.find("a")
                    img_tag = p.find("img", class_="lot-thumbnail img-fluid")
                    price_tag = p.find("strong", class_="lot-price-realized")
                    
                    if all([title_tag, link_tag, img_tag, price_tag]):
                        self.process_item(
                            title=title_tag.text.strip(),
                            product_url=base_url + link_tag.get("href"),
                            image_url=img_tag['src'],
                            sold_price_text=price_tag.text,
                            item_index=i,
                            total_items_on_page=len(products)
                        )
                    time.sleep(1)  # Be respectful to the server
                    
            except Exception as e:
                self.ui['status'].error(f"Error on page {page}: {e}")
                break
                
            page += 1

    def process_item(self, title, product_url, image_url, sold_price_text, item_index, total_items_on_page):
        try:
            self.ui['status'].info(f"Processing item {item_index}/{total_items_on_page}: {title[:40]}...")
            sold_price_float = round(float(sold_price_text.replace("$", "").replace("USD", "").replace(",", "").strip()), 2)
            
            ai_result = self.get_retail_price(title, image_url)
            if ai_result:
                price_part, link_part = ai_result.split(',', 1)
                retail_price_float = round(float(price_part.strip().replace('$', '')), 2)
                
                if retail_price_float > 0:
                    percentage = round((sold_price_float / retail_price_float) * 100, 2)
                    self.percentages.append(percentage)
                    
                    data = {
                        "Link": product_url, 
                        "Title": title, 
                        "Sold Price": f"${sold_price_float:,.2f}",
                        "Retail Price": f"${retail_price_float:,.2f}",
                        "Recovery": f"{percentage:.1f}%"
                    }
                    self.products.append(data)
                    
                    df = pd.DataFrame(self.products)
                    self.ui['dataframe'].dataframe(df, width='stretch')
                    
                    avg_recovery = statistics.mean(self.percentages) if self.percentages else 0
                    self.ui['metrics']['lots'].metric("Lots Scraped", len(self.products))
                    self.ui['metrics']['recovery'].metric("Average Recovery", f"{avg_recovery:.1f}%")
                    self.ui['progress'].progress(item_index / total_items_on_page, text=f"Page Progress: {item_index}/{total_items_on_page}")
            else:
                self.ui['status'].warning(f"Skipping '{title[:30]}...' - AI could not find a retail price.")
        except Exception as e:
            self.ui['status'].warning(f"Skipping item '{title[:30]}...' due to error: {e}")
