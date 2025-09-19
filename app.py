import streamlit as st
import pandas as pd
import io
from datetime import datetime
from scraper import AuctionScraper
from cryptography.fernet import Fernet
import base64
import json

# Encrypted Gemini API Keys (Secure)
ENCRYPTION_KEY = b's3Z36OOB8v2CxDQhFg90Ot3AMSxedH80xOrvehmz9h4='
ENCRYPTED_API_KEYS = 'Z0FBQUFBQm96S1RfLUdmTHc1MWgyOHpwRTRKSnNuZEhzQnY5YjJYZnFoYW5HVnFkWV9paGhtdWEwTVJoU3VNWnl4a2ExNlYxdHNMNnJEUGRKM2FJM0xSSFdlTWkwdnkxTVZVbVpxbm82VEZJYnNDSUlVbGRaeDdSMW90ZTEwczdRQTIxTDJ0emdLQWttSm0xTi1odU9RUDRTUlpaRFk2VldObklySzRQempteDVVMWZMTW41YXZmVm5iSkhJWTQ3RWtyaERxYUtBSzZlTUtDM0VCcGdxcE16d1pPTU1WQlRzTUdWRlJoM3pUUV92UmJuZFVidlBtN0R0aHhFT3E0NFZLYUN1ZjM3WWlRLXJCY0Z3VVJmLTAyQU1QTXZnYWZZeXE4TER6eG1IMVVzTXlnQ2F6eUdjM009'

def decrypt_gemini_keys():
    """Decrypt the Gemini API keys at runtime"""
    try:
        fernet = Fernet(ENCRYPTION_KEY)
        
        # Decode from base64
        encrypted_keys = base64.b64decode(ENCRYPTED_API_KEYS.encode())
        
        # Decrypt
        decrypted_json = fernet.decrypt(encrypted_keys).decode()
        
        # Convert back to list
        return json.loads(decrypted_json)
    except Exception as e:
        st.error(f"Failed to decrypt API keys: {str(e)}")
        return []

# Decrypt API keys at startup
GEMINI_API_KEYS = decrypt_gemini_keys()

# Import Amazon functions from amazon.py
try:
    import sys
    import importlib.util
    spec = importlib.util.spec_from_file_location("amazon_module", "amazon.py")
    amazon_module = importlib.util.module_from_spec(spec)
    sys.modules["amazon_module"] = amazon_module
    spec.loader.exec_module(amazon_module)
    
    # Import specific functions we need from amazon.py
    from amazon_module import (
        add_custom_css, get_logo_base64,
        render_upload_tab, render_amazon_grid_tab, render_excel_grid_tab
    )
    AMAZON_AVAILABLE = True
except ImportError as e:
    AMAZON_AVAILABLE = False

# Page Configuration
st.set_page_config(
    page_title="Business Intelligence Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Reset and base styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #000000;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: none;
        background-color: #000000;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Sidebar styling - Force dark theme regardless of system preferences */
    .css-1d391kg {
        background-color: #1a1a1a !important;
        border-right: 1px solid #333333 !important;
    }
    
    .sidebar .sidebar-content {
        background-color: #1a1a1a !important;
    }
    
    /* Force sidebar to stay visible and dark */
    .css-1d391kg {
        display: block !important;
        visibility: visible !important;
        width: 21rem !important;
        min-width: 21rem !important;
        background-color: #1a1a1a !important;
    }
    
    /* Prevent sidebar collapse and force dark background */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        width: 21rem !important;
        min-width: 21rem !important;
        background-color: #1a1a1a !important;
    }
    
    /* Force all sidebar elements to dark theme */
    section[data-testid="stSidebar"] > div {
        background-color: #1a1a1a !important;
    }
    
    section[data-testid="stSidebar"] .css-1v0mbdj {
        background-color: #1a1a1a !important;
    }
    
    /* Override any light theme styling */
    .css-1d391kg, 
    .css-1d391kg > div,
    .css-1d391kg .css-1v0mbdj,
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] .element-container {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
    }
    
    /* Hide sidebar collapse button */
    button[kind="header"][data-testid="baseButton-header"] {
        display: none !important;
    }
    
    /* Ensure sidebar content is always visible */
    .css-1d391kg .css-1v0mbdj {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Additional CSS to keep sidebar open */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            display: block !important;
            width: 21rem !important;
        }
    }
</style>

<script>
// JavaScript to keep sidebar expanded
document.addEventListener('DOMContentLoaded', function() {
    // Function to keep sidebar expanded
    function keepSidebarExpanded() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const collapseButton = document.querySelector('button[kind="header"][data-testid="baseButton-header"]');
        
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            sidebar.style.width = '21rem';
            sidebar.style.minWidth = '21rem';
        }
        
        if (collapseButton) {
            collapseButton.style.display = 'none';
        }
    }
    
    // Run immediately and on any changes
    keepSidebarExpanded();
    
    // Watch for changes and maintain sidebar
    const observer = new MutationObserver(keepSidebarExpanded);
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Also run on window resize
    window.addEventListener('resize', keepSidebarExpanded);
});
</script>
    
    /* Sidebar title styling */
    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        padding: 1.5rem 1rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border-radius: 12px;
        border: 1px solid #404040;
    }
    
    /* Section headers in sidebar */
    .section-header {
        font-size: 0.75rem;
        font-weight: 600;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.5rem 0;
        padding-left: 0.5rem;
    }
    
    /* Sidebar button styling */
    .stSidebar .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #404040;
        border-radius: 10px;
        padding: 0.875rem 1.25rem;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        color: #e0e0e0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: left;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stSidebar .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transition: left 0.5s;
    }
    
    .stSidebar .stButton > button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        border-color: #3b82f6;
    }
    
    .stSidebar .stButton > button:hover::before {
        left: 100%;
    }
    
    .stSidebar .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Main content styling */
    .main-content {
        background: #1a1a1a;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        border: 1px solid #333333;
    }
    
    /* Welcome screen styling */
    .welcome-header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem;
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border-radius: 16px;
        border: 1px solid #404040;
    }
    
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .welcome-subtitle {
        font-size: 1.125rem;
        color: #a0a0a0;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #404040;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
        border-color: #3b82f6;
    }
    
    .feature-title {
        font-size: 1.375rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.75rem;
    }
    
    .feature-description {
        color: #a0a0a0;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Page headers */
    .page-header {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #404040;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .page-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .page-subtitle {
        font-size: 1rem;
        color: #a0a0a0;
        font-weight: 400;
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #404040;
        padding: 0.75rem 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        background: #1a1a1a;
        color: #ffffff;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        background: #2a2a2a;
    }
    
    /* Form containers */
    .stForm {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #404040;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #404040;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        padding: 1rem;
        transition: all 0.3s ease;
        color: #ffffff;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }
    
    div[data-testid="metric-container"] [data-testid="metric-value"] {
        color: #ffffff;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-label"] {
        color: #a0a0a0;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 10px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #64748b;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        color: #475569;
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-color: transparent;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1);
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 1px solid #fecaca;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #fed7aa;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
    }
    
    .stInfo {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Session State Management
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'scraper_instance' not in st.session_state:
    st.session_state.scraper_instance = None

# Amazon session states
if 'fullscreen_mode' not in st.session_state:
    st.session_state.fullscreen_mode = False
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'failed_asins' not in st.session_state:
    st.session_state.failed_asins = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'current_processing_id' not in st.session_state:
    st.session_state.current_processing_id = 0
if 'total_processing_count' not in st.session_state:
    st.session_state.total_processing_count = 0

# Helper Functions
def show_login_page():
    """Display the login page for the entire application"""
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0;">
            <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                        border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; 
                        display: inline-block; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">
                <img src="data:image/png;base64,{logo_base64}" 
                     style="max-width: 350px; height: auto;" 
                     alt="NextGen Software Group">
            </div>
            <h1 style="color: #ffffff; font-size: 2.5rem; margin-bottom: 0.5rem;">Business Intelligence Suite</h1>
            <p style="color: #a0a0a0; font-size: 1.1rem; margin-bottom: 3rem;">Secure Access Portal</p>
        </div>
        """.format(logo_base64=get_logo_base64()), unsafe_allow_html=True)
        
        # Login form with dark styling
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%); 
                    border: 1px solid #404040; border-radius: 16px; padding: 2rem; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);">
            <div style="text-align: center; margin-bottom: 2rem;">
                <h3 style="color: #ffffff; margin-bottom: 0.5rem;">🔐 Secure Login</h3>
                <p style="color: #a0a0a0; font-size: 0.9rem;">Enter your credentials to access the dashboard</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                login_button = st.form_submit_button("🚀 Login to Dashboard", use_container_width=True, type="primary")
            
            if login_button:
                if password == "nick123":
                    st.session_state.authenticated = True
                    st.success("🎉 Login successful! Welcome to NextGen Business Intelligence Suite")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please try again.")
                    
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; color: #666666; font-size: 0.8rem;">
            <p>💡 Demo Password: nick123</p>
            <p style="margin-top: 1rem; color: #00d4aa;">Powered by NextGen Software Group</p>
        </div>
        """, unsafe_allow_html=True)

def show_dashboard_logo():
    """Display the NextGen Software Group logo at the top of the dashboard"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2a2a2a 0%, #1e1e1e 100%); 
                border: 1px solid #404040; border-radius: 16px; padding: 2rem; 
                margin-bottom: 2rem; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);">
        <div style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                    border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; 
                    display: inline-block; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);">
            <img src="data:image/png;base64,{logo_base64}" 
                 style="max-width: 400px; height: auto;" 
                 alt="NextGen Software Group">
        </div>
        <h1 style="color: #ffffff; font-size: 2rem; margin: 0.5rem 0; font-weight: 700;">Business Intelligence Suite</h1>
        <p style="color: #a0a0a0; margin: 0.5rem 0 0 0; font-size: 1rem;">Advanced Data Analytics & Automation Platform</p>
        <div style="margin-top: 1rem;">
            <span style="background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%); 
                         color: white; padding: 0.3rem 0.8rem; border-radius: 20px; 
                         font-size: 0.75rem; font-weight: 600;">NextGen Enterprise Edition</span>
        </div>
    </div>
    """.format(logo_base64=get_logo_base64()), unsafe_allow_html=True)

def to_excel(df: pd.DataFrame, site_name: str):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Auction Data')
        
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
    
    return output.getvalue()

def stop_scraping():
    if st.session_state.scraper_instance:
        st.session_state.scraper_instance.stop()
    st.session_state.is_scraping = False
    st.session_state.scraper_instance = None

def display_results(site_name):
    if not st.session_state.results_df.empty:
        st.markdown("---")
        st.subheader(f"{site_name} Scraping Results")
        st.dataframe(st.session_state.results_df, use_container_width=True)
        
        excel_data = to_excel(st.session_state.results_df, site_name)
        st.download_button(
            label=f"Download {site_name} Results as Excel",
            data=excel_data,
            file_name=f"{site_name.replace('.', '')}_auction_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

def create_ai_scraper_ui(site_name):
    st.markdown(f"""
    <div class="page-header">
        <h1 class="page-title">🤖 {site_name} AI-Powered Auction Scraper</h1>
        <p class="page-subtitle">🧠 Uses Google Gemini AI to find retail prices from product images</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form(key=f'{site_name}_form'):
        url = st.text_input(
            "🔗 Auction URL", 
            placeholder=f"Enter the {site_name} auction catalog URL here", 
            key=f'url_{site_name}',
            help=f"Paste the full {site_name} auction catalog URL"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("📄 Start Page", min_value=1, value=1, step=1, key=f'start_{site_name}')
        with col2:
            end_page = st.number_input("🔚 End Page (0 for no limit)", min_value=0, value=0, step=1, key=f'end_{site_name}')
        
        st.info("ℹ️ AI-powered price detection is enabled with built-in Gemini API keys")
        
        submitted = st.form_submit_button(
            f"🚀 Start {site_name} Scraping", 
            type="primary", 
            use_container_width=True, 
            disabled=st.session_state.is_scraping
        )

    return submitted, url, start_page, end_page, []

def create_direct_scraper_ui(site_name, placeholder_url, special_note=None):
    st.markdown(f"""
    <div class="page-header">
        <h1 class="page-title">📊 {site_name} Direct Price Scraper</h1>
        <p class="page-subtitle">⚡ No AI needed - uses existing retail price data from the site</p>
    </div>
    """, unsafe_allow_html=True)
    
    if special_note:
        st.warning(f"💡 {special_note}")

    with st.form(key=f'{site_name}_form'):
        url = st.text_input(
            "🔗 Auction URL", 
            placeholder=placeholder_url, 
            key=f'url_{site_name}',
            help=f"Paste the full {site_name} auction URL"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("📄 Start Page", min_value=1, value=1, step=1, key=f'start_{site_name}')
        with col2:
            end_page = st.number_input("🔚 End Page (0 for no limit)", min_value=0, value=0, step=1, key=f'end_{site_name}')
        
        submitted = st.form_submit_button(
            f"🚀 Start {site_name} Scraping", 
            type="primary", 
            use_container_width=True, 
            disabled=st.session_state.is_scraping
        )

    return submitted, url, start_page, end_page

def run_scraper(site_name, url, start_page, end_page, requires_ai=True):
    if not url:
        st.error("Please enter a valid URL.")
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
    
    # Use built-in API keys for AI-powered scrapers
    scraper_api_keys = GEMINI_API_KEYS if requires_ai else []
    st.session_state.scraper_instance = AuctionScraper(
        gemini_api_keys=scraper_api_keys,
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

def show_welcome():
    # Show the dashboard logo
    show_dashboard_logo()
    
    st.markdown("""
    <div class="welcome-header">
        <h1 class="welcome-title">🎯 Business Intelligence Dashboard</h1>
        <p class="welcome-subtitle">
            🔍 Comprehensive data collection and analysis tools for auction sites and e-commerce platforms.<br>
            📊 Select a tool from the navigation panel to begin your analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards using columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3 class="feature-title">🤖 AI-Powered Auction Analytics</h3>
            <p class="feature-description">
                🚀 Advanced scraping capabilities for HiBid, BiddingKings, and BidLlama platforms 
                with integrated AI price detection and market analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3 class="feature-title">📈 Direct Market Intelligence</h3>
            <p class="feature-description">
                ⚡ Real-time data extraction from 8 major auction platforms with built-in 
                retail price comparisons and recovery analytics.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3 class="feature-title">📦 Product Image Management</h3>
            <p class="feature-description">
                💼 Professional-grade CSV processing and image visualization tools for 
                Amazon product catalogs and inventory management.
            </p>
        </div>
        """, unsafe_allow_html=True)

def show_amazon_environment():
    if not AMAZON_AVAILABLE:
        st.error("❌ Amazon functionality not available. Please ensure amazon.py is in the same directory.")
        return
    
    # Add Amazon CSS
    if hasattr(amazon_module, 'add_custom_css'):
        amazon_module.add_custom_css()
    
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📦 Amazon Product Image Viewer</h1>
        <p class="page-subtitle">🖼️ Upload and manage product image catalogs with advanced grid visualization</p>
    </div>
    """, unsafe_allow_html=True)
    
    amazon_tabs = st.tabs(["📤 Upload CSV", "📦 Amazon Grid Images", "📋 Excel Grid Images"])
    
    with amazon_tabs[0]:
        if hasattr(amazon_module, 'render_upload_tab'):
            amazon_module.render_upload_tab()
    
    with amazon_tabs[1]:
        if hasattr(amazon_module, 'render_amazon_grid_tab'):
            amazon_module.render_amazon_grid_tab()
    
    with amazon_tabs[2]:
        if hasattr(amazon_module, 'render_excel_grid_tab'):
            amazon_module.render_excel_grid_tab()

# Check if user is authenticated
if not st.session_state.authenticated:
    show_login_page()
else:
    # Streamlit Sidebar Navigation (only show if authenticated)
    with st.sidebar:
        st.markdown('<div class="sidebar-title">NextGen Business Intelligence</div>', unsafe_allow_html=True)
        
        if st.button("🏠 Dashboard", key="home_btn", use_container_width=True):
            st.session_state.current_view = 'home'
            st.rerun()

        if AMAZON_AVAILABLE:
            if st.button("📦 Amazon Product Viewer", key="amazon_btn", use_container_width=True):
                st.session_state.current_view = 'amazon'
                st.rerun()

        st.markdown('<div class="section-header">🤖 AI AUCTION SCRAPERS</div>', unsafe_allow_html=True)
        
        if st.button("🎯 HiBid Scraper", key="hibid_btn", use_container_width=True):
            st.session_state.current_view = 'hibid'
            st.rerun()

        if st.button("👑 BiddingKings Scraper", key="biddingkings_btn", use_container_width=True):
            st.session_state.current_view = 'biddingkings'
            st.rerun()

        if st.button("🦙 BidLlama Scraper", key="bidllama_btn", use_container_width=True):
            st.session_state.current_view = 'bidllama'
            st.rerun()

        st.markdown('<div class="section-header">📊 DIRECT PRICE SCRAPERS</div>', unsafe_allow_html=True)
        
        if st.button("🏛️ Nellis Scraper", key="nellis_btn", use_container_width=True):
            st.session_state.current_view = 'nellis'
            st.rerun()

        if st.button("🎪 BidFTA Scraper", key="bidfta_btn", use_container_width=True):
            st.session_state.current_view = 'bidfta'
            st.rerun()

        if st.button("🏢 MAC.bid Scraper", key="macbid_btn", use_container_width=True):
            st.session_state.current_view = 'macbid'
            st.rerun()

        if st.button("📈 A-Stock Scraper", key="astock_btn", use_container_width=True):
            st.session_state.current_view = 'astock'
            st.rerun()

        if st.button("🎰 702Auctions Scraper", key="702auctions_btn", use_container_width=True):
            st.session_state.current_view = '702auctions'
            st.rerun()

        if st.button("🌄 Vista Scraper", key="vista_btn", use_container_width=True):
            st.session_state.current_view = 'vista'
            st.rerun()

        if st.button("💎 BidSoflo Scraper", key="bidsoflo_btn", use_container_width=True):
            st.session_state.current_view = 'bidsoflo'
            st.rerun()

        if st.button("🛒 BidAuctionDepot Scraper", key="bidauctiondepot_btn", use_container_width=True):
            st.session_state.current_view = 'bidauctiondepot'
            st.rerun()
            
        # Logout button at bottom - THIS IS THE FIXED LINE
        st.markdown('<hr style="margin: 2rem 0;">', unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_view = 'home'
            st.rerun()

    # Main Content Area (only show if authenticated)
    # Display content based on current view
    if st.session_state.current_view == 'home':
        show_welcome()

    elif st.session_state.current_view == 'amazon':
        show_amazon_environment()

    elif st.session_state.current_view == 'hibid':
        submitted, url, start_page, end_page, keys = create_ai_scraper_ui("HiBid")
        if submitted: 
            run_scraper("HiBid", url, start_page, end_page, keys, requires_ai=True)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_hibid")
        display_results("HiBid")

    elif st.session_state.current_view == 'biddingkings':
        submitted, url, start_page, end_page, keys = create_ai_scraper_ui("BiddingKings")
        if submitted: 
            run_scraper("BiddingKings", url, start_page, end_page, keys, requires_ai=True)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bk")
        display_results("BiddingKings")

    elif st.session_state.current_view == 'bidllama':
        submitted, url, start_page, end_page, keys = create_ai_scraper_ui("BidLlama")
        if submitted: 
            run_scraper("BidLlama", url, start_page, end_page, keys, requires_ai=True)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bl")
        display_results("BidLlama")

    elif st.session_state.current_view == 'nellis':
        submitted, url, start_page, end_page = create_direct_scraper_ui("Nellis", "https://www.nellisauction.com/browse/co/denver/7822/all")
        if submitted: 
            run_scraper("Nellis", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_nellis")
        display_results("Nellis")

    elif st.session_state.current_view == 'bidfta':
        submitted, url, start_page, end_page = create_direct_scraper_ui("BidFTA", "https://www.bidfta.com/browse-all-categories")
        if submitted: 
            run_scraper("BidFTA", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bidfta")
        display_results("BidFTA")

    elif st.session_state.current_view == 'macbid':
        submitted, url, start_page, end_page = create_direct_scraper_ui("MAC.bid", "https://www.mac.bid/past-auctions/44592")
        if submitted: 
            run_scraper("MAC.bid", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_macbid")
        display_results("MAC.bid")

    elif st.session_state.current_view == 'astock':
        submitted, url, start_page, end_page = create_direct_scraper_ui("A-Stock", "https://a-stock.bid")
        if submitted: 
            run_scraper("A-Stock", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_astock")
        display_results("A-Stock")

    elif st.session_state.current_view == '702auctions':
        submitted, url, start_page, end_page = create_direct_scraper_ui("702Auctions", "https://bid.702auctions.com", special_note="Pages start from 0 internally. Use 'Start Page' input.")
        if submitted: 
            run_scraper("702Auctions", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_702")
        display_results("702Auctions")

    elif st.session_state.current_view == 'vista':
        submitted, url, start_page, end_page = create_direct_scraper_ui("Vista", "https://vistaauction.com", special_note="Pages start from 0 internally. Use 'Start Page' input.")
        if submitted: 
            run_scraper("Vista", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_vista")
        display_results("Vista")

    elif st.session_state.current_view == 'bidsoflo':
        submitted, url, start_page, end_page = create_direct_scraper_ui("BidSoflo", "https://bid.bidsoflo.us/Public/Auction/AuctionItems?AuctionId=...")
        if submitted: 
            run_scraper("BidSoflo", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_bidsoflo")
        display_results("BidSoflo")

    elif st.session_state.current_view == 'bidauctiondepot':
        submitted, url, start_page, end_page = create_direct_scraper_ui("BidAuctionDepot", "https://bidauctiondepot.com/search/product-buyer-auction/...")
        if submitted: 
            run_scraper("BidAuctionDepot", url, start_page, end_page, requires_ai=False)
        if st.session_state.is_scraping: 
            st.button("🛑 Stop Scraping", on_click=stop_scraping, use_container_width=True, key="stop_depot")
        display_results("BidAuctionDepot")
