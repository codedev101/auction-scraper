import streamlit as st
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import traceback
import os

# Page configuration
st.set_page_config(
    page_title="Pydoll BidLlama Test",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Pydoll BidLlama Test")
st.write("Testing Pydoll browser automation with BidLlama auction site")

# Check if Pydoll is available
try:
    from pydoll.browser import Chrome
    from pydoll.browser.options import ChromiumOptions
    st.success("✅ Pydoll imported successfully")
except ImportError as e:
    st.error("❌ Pydoll not installed. Add 'pydoll' to requirements.txt")
    st.stop()

async def scrape_bidllama(url, status_placeholder, progress_bar):
    """Scrape BidLlama with Pydoll"""
    browser = None
    results = []
    
    try:
        status_placeholder.info("Setting up browser options...")
        
        # Setup Chrome options for Streamlit Cloud
        options = ChromiumOptions()
        
        # Try different Chrome binary locations
        chrome_paths = [
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/snap/bin/chromium'
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if chrome_path:
            options.binary_location = chrome_path
            status_placeholder.info(f"Found Chrome at: {chrome_path}")
        else:
            status_placeholder.warning("No Chrome binary found, using default...")
        
        # Add arguments for headless operation in containerized environment
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--window-size=1920,1080')
        
        status_placeholder.info("Starting browser...")
        browser = Chrome(options=options)
        tab = await browser.start()
        progress_bar.progress(20)
        
        status_placeholder.info(f"Navigating to BidLlama...")
        await tab.go_to(url)
        progress_bar.progress(40)
        
        status_placeholder.info("Waiting for page to load...")
        await asyncio.sleep(5)
        progress_bar.progress(60)
        
        # Try to wait for specific elements
        try:
            await tab.find(xpath="//p[@class='item-lot-number']", timeout=10)
            status_placeholder.success("Found item-lot-number elements!")
        except Exception as e:
            status_placeholder.warning(f"Could not find item-lot-number elements: {e}")
        
        progress_bar.progress(80)
        
        # Get page content
        status_placeholder.info("Extracting page content...")
        try:
            content = await tab.execute_script("return document.documentElement.outerHTML")
            
            # Debug content type
            content_info = {
                "type": str(type(content)),
                "length": len(content) if hasattr(content, '__len__') else 'No length',
                "is_string": isinstance(content, str)
            }
            
            # Make sure content is a string
            if not isinstance(content, str):
                content = str(content)
            
            soup = BeautifulSoup(content, 'html.parser')
            
        except Exception as e:
            status_placeholder.error(f"Error getting page content: {e}")
            # Try alternative method
            try:
                status_placeholder.info("Trying alternative content extraction...")
                content = await tab.execute_script("return document.body.innerHTML")
                if not isinstance(content, str):
                    content = str(content)
                soup = BeautifulSoup(f"<html><body>{content}</body></html>", 'html.parser')
                content_info = {"alternative_method": True}
            except Exception as e2:
                status_placeholder.error(f"Alternative method failed: {e2}")
                return [], {"error": str(e2)}
        
        progress_bar.progress(90)
        
        # Find lot number tags
        lot_number_tags = soup.find_all("p", class_="item-lot-number")
        
        for i, tag in enumerate(lot_number_tags):
            results.append({
                "index": i + 1,
                "tag": str(tag),
                "text": tag.text.strip(),
                "parent": tag.parent.name if tag.parent else "None"
            })
        
        # If no lot number tags found, show some sample p tags for debugging
        if not lot_number_tags:
            all_p_tags = soup.find_all("p")
            sample_p_tags = []
            for i, p in enumerate(all_p_tags[:5]):
                sample_p_tags.append({
                    "index": i + 1,
                    "classes": p.get('class', []),
                    "text": p.text.strip()[:100] + "..." if len(p.text.strip()) > 100 else p.text.strip()
                })
            content_info["sample_p_tags"] = sample_p_tags
        
        # Get page info
        try:
            title = await tab.execute_script("return document.title")
            ready_state = await tab.execute_script("return document.readyState")
            url_check = await tab.execute_script("return window.location.href")
        except:
            title = "Unknown"
            ready_state = "Unknown"
            url_check = "Unknown"
        
        page_info = {
            "title": title,
            "ready_state": ready_state,
            "current_url": url_check,
            "total_p_tags": len(soup.find_all("p")) if soup else 0,
            "lot_number_tags": len(lot_number_tags),
            "content_info": content_info,
            "chrome_path": chrome_path
        }
        
        progress_bar.progress(100)
        status_placeholder.success(f"Scraping complete! Found {len(lot_number_tags)} lot number tags")
        
        return results, page_info
        
    except Exception as e:
        status_placeholder.error(f"Scraping failed: {e}")
        return [], {"error": str(e), "traceback": traceback.format_exc()}
    
    finally:
        if browser:
            try:
                await browser.stop()
            except:
                pass

def run_scraper(url):
    """Run the scraper in Streamlit"""
    
    # Create UI elements
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    # Run the async scraper
    try:
        results, page_info = asyncio.run(scrape_bidllama(url, status_placeholder, progress_bar))
        
        # Display results
        st.subheader("📊 Scraping Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Lot Number Tags Found", len(results))
            
        with col2:
            st.metric("Total P Tags", page_info.get("total_p_tags", "Unknown"))
        
        # Page information
        st.subheader("📄 Page Information")
        st.json(page_info)
        
        # Results table
        if results:
            st.subheader("🏷️ Lot Number Tags")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            
            # Show individual tags
            st.subheader("🔍 Individual Tags")
            for result in results[:5]:  # Show first 5
                with st.expander(f"Tag {result['index']} - {result['text'][:50]}..."):
                    st.code(result['tag'], language='html')
        else:
            st.warning("No lot number tags found")
            
            # Debug: Show some sample p tags
            if 'error' not in page_info:
                st.subheader("🐛 Debug: Sample P Tags")
                st.write("Let's see what p tags are available on the page...")
                
    except Exception as e:
        st.error(f"❌ Failed to run scraper: {e}")
        st.code(traceback.format_exc())

# Main UI
st.sidebar.header("Configuration")

default_url = "https://bid.bidllama.com/lots#YXVjdGlvbltpZF09MTIxOTYmYXVjdGlvbltsb2NhdGlvbl09YWxsJmF1Y3Rpb25bc3RhdHVzXT1wYXN0JmF1Y3Rpb25bdHlwZV09YWxsJmxpbWl0PTMwJmxvdFtjYXRlZ29yeV09YWxsJmxvdFtsb2NhdGlvbl09YWxsJmxvdFttaWxlX3JhZGl1c109MjUmcGFnZT0x"

url = st.sidebar.text_input(
    "BidLlama URL:",
    value=default_url,
    help="Enter the BidLlama auction URL to scrape"
)

if st.sidebar.button("🚀 Start Scraping", type="primary"):
    if url:
        run_scraper(url)
    else:
        st.error("Please enter a URL")

# Instructions
st.sidebar.markdown("""
### 📋 Instructions
1. Make sure `pydoll` is in your requirements.txt
2. Click "Start Scraping" to test
3. Check the results below

### 🎯 What this tests:
- Pydoll browser startup
- Page navigation
- JavaScript execution
- Element finding
- Content extraction
""")

# Add requirements info
st.sidebar.markdown("""
### 📦 Requirements.txt
```
streamlit
pydoll
beautifulsoup4
pandas
```
""")
