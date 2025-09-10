import streamlit as st
import pandas as pd
import io
from datetime import datetime
from scraper import AuctionScraper

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Auction Scraper Pro",
    page_icon="🤖",
    layout="wide"
)

# --- App State Management ---
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'scraper_instance' not in st.session_state:
    st.session_state.scraper_instance = None


# --- Helper Functions ---
def to_excel(df: pd.DataFrame):
    """Converts a DataFrame to an Excel file in memory."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Auction Data')
        # You can add more sheets or formatting here if needed
    processed_data = output.getvalue()
    return processed_data

def stop_scraping():
    """Stops the scraping process and cleans up."""
    if st.session_state.scraper_instance:
        st.session_state.scraper_instance.stop()
    st.session_state.is_scraping = False
    st.session_state.scraper_instance = None
    st.info("Scraping stopped by user.")

# --- UI Layout ---

# Header
st.markdown("""
<div style="background-color: #6200EA; padding: 20px; border-radius: 15px; text-align: center;">
    <h1 style="color: white; font-weight: bold;">AI AUCTION SCRAPER PRO</h1>
    <p style="color: rgba(255, 255, 255, 0.8);">Track auction prices and analyze recovery rates with AI</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Sidebar for API keys and instructions
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("AI features require at least one Google Gemini API key.")
    
    keys = []
    for i in range(4):
        key = st.text_input(f"Gemini API Key {i+1}", type="password", key=f"api_key_{i}")
        if key:
            keys.append(key)
    
    st.session_state.api_keys = keys
    
    st.markdown("---")
    st.header("📖 How to Use")
    st.markdown("""
    1.  **Enter API Keys**: Add your Gemini API keys on the left.
    2.  **Select Tab**: Choose the auction site you want to scrape.
    3.  **Enter URL**: Paste the auction catalog URL.
    4.  **Set Pages**: Define the start and end page range.
    5.  **Start Scraping**: Click the button to begin.
    6.  **Export**: Once done, download the results as an Excel file.
    """)

# Main content area with tabs
hibid_tab, biddingkings_tab, bidllama_tab = st.tabs(["HiBid Scraper", "BiddingKings Scraper", "BidLlama Scraper"])

def create_scraper_ui(site_name):
    """Creates a standardized UI for each scraper tab."""
    st.subheader(f"{site_name} Auction Scraper")

    # Input Form
    with st.form(key=f'{site_name}_form'):
        url = st.text_input("Auction URL", placeholder=f"Enter the {site_name} auction catalog URL here", key=f'url_{site_name}')
        
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Start Page", min_value=1, value=1, step=1, key=f'start_{site_name}')
        with col2:
            end_page = st.number_input("End Page (0 for no limit)", min_value=0, value=0, step=1, key=f'end_{site_name}')
        
        submitted = st.form_submit_button("🚀 Start Scraping", type="primary", use_container_width=True, disabled=st.session_state.is_scraping)

    # Placeholders for dynamic content
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    metric_cols = st.columns(3)
    pages_metric = metric_cols[0].empty()
    lots_metric = metric_cols[1].empty()
    recovery_metric = metric_cols[2].empty()
    
    dataframe_placeholder = st.empty()

    if submitted:
        if not url:
            st.error("Please enter a valid URL.")
        elif not st.session_state.api_keys:
            st.error("Please enter at least one Gemini API Key in the sidebar.")
        else:
            # Reset UI elements
            st.session_state.is_scraping = True
            st.session_state.results_df = pd.DataFrame()
            dataframe_placeholder.dataframe(st.session_state.results_df)
            pages_metric.metric("Pages Scraped", 0)
            lots_metric.metric("Lots Scraped", 0)
            recovery_metric.metric("Average Recovery", "0%")
            progress_placeholder.progress(0)
            
            # Prepare UI placeholders to pass to the scraper
            ui_placeholders = {
                'status': status_placeholder,
                'progress': progress_placeholder,
                'dataframe': dataframe_placeholder,
                'metrics': {
                    'pages': pages_metric,
                    'lots': lots_metric,
                    'recovery': recovery_metric
                }
            }
            
            # Initialize and run the scraper
            st.session_state.scraper_instance = AuctionScraper(
                gemini_api_keys=st.session_state.api_keys,
                ui_placeholders=ui_placeholders
            )
            
            results = st.session_state.scraper_instance.run(site_name, url, start_page, end_page)
            
            if results:
                st.session_state.results_df = pd.DataFrame(results)
                status_placeholder.success(f"Scraping complete! Found {len(results)} items.")
            else:
                status_placeholder.warning("Scraping finished, but no items were found.")
            
            st.session_state.is_scraping = False
            st.rerun() # Rerun to update button states and show download button

    if st.session_state.is_scraping:
        st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True)

    if not st.session_state.results_df.empty:
        st.markdown("---")
        st.subheader("📊 Scraping Results")
        dataframe_placeholder.dataframe(st.session_state.results_df, use_container_width=True)
        
        # Prepare file for download
        excel_data = to_excel(st.session_state.results_df)
        
        st.download_button(
            label="💾 Download Results as Excel",
            data=excel_data,
            file_name=f"{site_name}_auction_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


with hibid_tab:
    create_scraper_ui("HiBid")

with biddingkings_tab:
    create_scraper_ui("BiddingKings")
    
with bidllama_tab:
    create_scraper_ui("BidLlama")