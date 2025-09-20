import streamlit as st
import pandas as pd
import io
from datetime import datetime
from scraper import AuctionScraper

# --- Page Configuration ---
st.set_page_config(
    page_title="Ultimate Auction Scraper Pro - 11 Sites",
    page_icon="🤖",
    layout="wide"
)

# --- Custom CSS for Eye-Catching Design ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .main-title {
        color: white;
        font-size: 3rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-subtitle {
        color: #e8f4fd;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    
    .ai-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .no-ai-badge {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .site-info {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .stTab [data-baseweb="tab-list"] {
        gap: 2px;
        flex-wrap: wrap;
    }
    
    .stTab [data-baseweb="tab"] {
        height: 60px;
        padding: 8px 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 8px;
        color: white;
        font-weight: bold;
        border: none;
        font-size: 0.85rem;
    }
    
    .stTab [aria-selected="true"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        padding: 1rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    div[data-testid="metric-container"] > div {
        color: white;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: white;
        font-size: 2rem;
    }
    
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .status-info {
        background: linear-gradient(135deg, #4cc9f0 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
    }
    
    .fix-notice {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
    }
    
    .results-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Management ---
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'scraper_instance' not in st.session_state:
    st.session_state.scraper_instance = None

# --- Helper Functions ---
def to_excel(df: pd.DataFrame, site_name: str):
    """Converts a DataFrame to an Excel file in memory with enhanced formatting."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Auction Data')
        
        # Add summary sheet if we have recovery data
        if not df.empty and 'Recovery' in df.columns:
            import statistics
            summary_data = []
            percentages = []
            for recovery in df['Recovery']:
                try:
                    percentage = float(str(recovery).replace('%', ''))
                    percentages.append(percentage)
                except (ValueError, TypeError):
                    continue
            
            if percentages:
                summary_data.append(['Total Items', len(df)])
                summary_data.append(['Average Recovery', f"{statistics.mean(percentages):.2f}%"])
                summary_data.append(['Highest Recovery', f"{max(percentages):.2f}%"])
                summary_data.append(['Lowest Recovery', f"{min(percentages):.2f}%"])
                summary_data.append(['Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                summary_data.append(['Site', site_name])
                
                summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
    
    processed_data = output.getvalue()
    return processed_data

def stop_scraping():
    """Stops the scraping process and cleans up."""
    if st.session_state.scraper_instance:
        st.session_state.scraper_instance.stop()
    st.session_state.is_scraping = False
    st.session_state.scraper_instance = None

def display_results(site_name):
    """Displays the results dataframe and download button."""
    if not st.session_state.results_df.empty:
        st.markdown("---")
        st.subheader(f"📊 {site_name} Scraping Results")
        st.dataframe(st.session_state.results_df, use_container_width=True)
        
        excel_data = to_excel(st.session_state.results_df, site_name)
        st.download_button(
            label=f"💾 Download {site_name} Results as Excel",
            data=excel_data,
            file_name=f"{site_name.replace('.', '')}_auction_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --- UI Layout ---

# Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">ULTIMATE AUCTION SCRAPER PRO</h1>
    <p class="main-subtitle">Complete Edition - 11 Auction Sites with AI and Direct Price Scraping</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for API keys and instructions
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("""
    <div class="site-info">
        <h4>🤖 AI-Powered Sites (3)</h4>
        <span class="ai-badge">HiBid</span>
        <span class="ai-badge">BiddingKings</span>
        <span class="ai-badge">BidLlama</span>
        <p style="margin-top: 10px; font-size: 0.9rem;">These sites use AI to find retail prices from product images.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="site-info">
        <h4>📊 Direct Price Sites (8)</h4>
        <span class="no-ai-badge">Nellis</span>
        <span class="no-ai-badge">BidFTA</span>
        <span class="no-ai-badge">MAC.bid</span>
        <span class="no-ai-badge">A-Stock</span>
        <span class="no-ai-badge">702Auctions</span>
        <span class="no-ai-badge">Vista</span>
        <span class="no-ai-badge">BidSoflo</span>
        <span class="no-ai-badge">BidAuctionDepot</span>
        <p style="margin-top: 10px; font-size: 0.9rem;">These sites already provide retail prices, no AI needed.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("AI features require at least one Google Gemini API key for HiBid, BiddingKings, and BidLlama.")
    
    keys = []
    for i in range(4):
        key = st.text_input(f"Gemini API Key {i+1}", type="password", key=f"api_key_{i}")
        if key:
            keys.append(key)
    
    st.session_state.api_keys = keys
    
    st.markdown("---")
    st.header("📖 How to Use")
    st.markdown("""
    **For AI Sites (HiBid, BiddingKings, BidLlama):**
    1. Enter your Gemini API keys above
    2. Select the AI-powered tab
    3. Enter the auction catalog URL
    4. Set page range and start scraping
    
    **For Direct Price Sites (All Others):**
    1. No API keys needed
    2. Select the appropriate tab
    3. Enter the auction URL
    4. Start scraping immediately
    
    **Export:** Download results as Excel with summary statistics.
    """)

# Main content area with tabs for all 11 sites
hibid_tab, biddingkings_tab, bidllama_tab, nellis_tab, bidfta_tab, macbid_tab, astock_tab, auctions702_tab, vista_tab, bidsoflo_tab, bidauctiondepot_tab = st.tabs([
    "🤖 HiBid", "🤖 BiddingKings", "🤖 BidLlama", 
    "📊 Nellis", "📊 BidFTA", "📊 MAC.bid",
    "🏠 A-Stock", "🏬 702Auctions", "🔍 Vista", "💎 BidSoflo", "🛒 BidAuctionDepot"
])

def create_ai_scraper_ui(site_name):
    """Creates UI for AI-powered scrapers (HiBid, BiddingKings, BidLlama)."""
    st.markdown(f"""
    <div class="status-info">
        🤖 {site_name} AI-Powered Auction Scraper
        <br><small>Uses Google Gemini AI to find retail prices from product images</small>
    </div>
    """, unsafe_allow_html=True)

    # Input Form
    with st.form(key=f'{site_name}_form'):
        url = st.text_input(
            "Auction URL", 
            placeholder=f"Enter the {site_name} auction catalog URL here", 
            key=f'url_{site_name}',
            help=f"Paste the full {site_name} auction catalog URL"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Start Page", min_value=1, value=1, step=1, key=f'start_{site_name}')
        with col2:
            end_page = st.number_input("End Page (0 for no limit)", min_value=0, value=0, step=1, key=f'end_{site_name}')
        
        submitted = st.form_submit_button(
            f"🚀 Start {site_name} Scraping", 
            type="primary", 
            use_container_width=True, 
            disabled=st.session_state.is_scraping
        )

    return submitted, url, start_page, end_page

def create_direct_scraper_ui(site_name, placeholder_url, special_note=None):
    """Creates UI for direct price scrapers."""
    st.markdown(f"""
    <div class="status-info">
        📊 {site_name} Direct Price Scraper
        <br><small>No AI needed - uses existing retail price data from the site</small>
    </div>
    """, unsafe_allow_html=True)
    
    if special_note:
        st.markdown(f"""
        <div class="fix-notice">
            ✅ {special_note}
        </div>
        """, unsafe_allow_html=True)

    with st.form(key=f'{site_name}_form'):
        url = st.text_input(
            "Auction URL", 
            placeholder=placeholder_url, 
            key=f'url_{site_name}',
            help=f"Paste the full {site_name} auction URL"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Start Page", min_value=1, value=1, step=1, key=f'start_{site_name}')
        with col2:
            end_page = st.number_input("End Page (0 for no limit)", min_value=0, value=0, step=1, key=f'end_{site_name}')
        
        submitted = st.form_submit_button(
            f"🚀 Start {site_name} Scraping", 
            type="primary", 
            use_container_width=True, 
            disabled=st.session_state.is_scraping
        )

    return submitted, url, start_page, end_page

def run_scraper(site_name, url, start_page, end_page, requires_ai=True):
    """Common function to run any scraper."""
    if not url:
        st.error("Please enter a valid URL.")
        return
    
    if requires_ai and not st.session_state.api_keys:
        st.error("Please enter at least one Gemini API Key in the sidebar for AI-powered scraping.")
        return
    
    st.session_state.is_scraping = True
    st.session_state.results_df = pd.DataFrame()

    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    metric_cols = st.columns(3)
    pages_metric = metric_cols[0].empty()
    lots_metric = metric_cols[1].empty()
    recovery_metric = metric_cols[2].empty()
    
    dataframe_placeholder = st.empty()
    
    pages_metric.metric("Pages Scraped", 0)
    lots_metric.metric("Lots Scraped", 0)
    recovery_metric.metric("Average Recovery", "0%")
    progress_placeholder.progress(0)
    
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
    
    api_keys = st.session_state.api_keys if requires_ai else []
    st.session_state.scraper_instance = AuctionScraper(
        gemini_api_keys=api_keys,
        ui_placeholders=ui_placeholders
    )
    
    try:
        results = st.session_state.scraper_instance.run(site_name, url, start_page, end_page)
        
        if results:
            st.session_state.results_df = pd.DataFrame(results)
            status_placeholder.success(f"Scraping complete! Found {len(results)} items.")
        else:
            status_placeholder.warning("Scraping finished, but no items were found.")
            
    except Exception as e:
        status_placeholder.error(f"An error occurred during scraping: {str(e)}")
    
    st.session_state.is_scraping = False
    st.rerun()

# --- Tab Implementations ---

with hibid_tab:
    submitted, url, start_page, end_page = create_ai_scraper_ui("HiBid")
    if submitted: run_scraper("HiBid", url, start_page, end_page, requires_ai=True)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_hibid")
    display_results("HiBid")

with biddingkings_tab:
    submitted, url, start_page, end_page = create_ai_scraper_ui("BiddingKings")
    if submitted: run_scraper("BiddingKings", url, start_page, end_page, requires_ai=True)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bk")
    display_results("BiddingKings")

with bidllama_tab:
    submitted, url, start_page, end_page = create_ai_scraper_ui("BidLlama")
    if submitted: run_scraper("BidLlama", url, start_page, end_page, requires_ai=True)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bl")
    display_results("BidLlama")

with nellis_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("Nellis", "https://www.nellisauction.com/browse/co/denver/7822/all")
    if submitted: run_scraper("Nellis", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_nellis")
    display_results("Nellis")

with bidfta_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("BidFTA", "https://www.bidfta.com/browse-all-categories")
    if submitted: run_scraper("BidFTA", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bidfta")
    display_results("BidFTA")

with macbid_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("MAC.bid", "https://www.mac.bid/past-auctions/44592")
    if submitted: run_scraper("MAC.bid", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_macbid")
    display_results("MAC.bid")

with astock_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("A-Stock", "https://a-stock.bid")
    if submitted: run_scraper("A-Stock", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_astock")
    display_results("A-Stock")

with auctions702_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("702Auctions", "https://bid.702auctions.com", special_note="Pages start from 0 internally. Use 'Start Page' input.")
    if submitted: run_scraper("702Auctions", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_702")
    display_results("702Auctions")

with vista_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("Vista", "https://vistaauction.com", special_note="Pages start from 0 internally. Use 'Start Page' input.")
    if submitted: run_scraper("Vista", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_vista")
    display_results("Vista")

with bidsoflo_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("BidSoflo", "https://bid.bidsoflo.us/Public/Auction/AuctionItems?AuctionId=...")
    if submitted: run_scraper("BidSoflo", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bidsoflo")
    display_results("BidSoflo")

with bidauctiondepot_tab:
    submitted, url, start_page, end_page = create_direct_scraper_ui("BidAuctionDepot", "https://bidauctiondepot.com/search/product-buyer-auction/...")
    if submitted: run_scraper("BidAuctionDepot", url, start_page, end_page, requires_ai=False)
    if st.session_state.is_scraping: st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_depot")
    display_results("BidAuctionDepot")
