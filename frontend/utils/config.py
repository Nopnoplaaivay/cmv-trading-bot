import os


# API Configuration
API_BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1")

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "CMV Trading Bot",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Application Settings
APP_SETTINGS = {
    "auto_refresh_interval": 30,  # seconds
    "order_simulation_delay": 0.5,  # seconds
    "cache_ttl": 30,  # seconds
}
