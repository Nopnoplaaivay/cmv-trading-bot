"""
CSS styles for CMV Trading Bot frontend
"""

# Advanced CSS styling
MAIN_CSS = """
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #2a5298;
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    .recommendation-high {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 5px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(244,67,54,0.2);
    }
    
    .recommendation-medium {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left: 5px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(255,152,0,0.2);
    }
    
    .recommendation-low {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left: 5px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(76,175,80,0.2);
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(21,87,36,0.1);
    }
    
    .error-box {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(114,28,36,0.1);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(42,82,152,0.3);
    }
    
    .order-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
    }
    
    .status-pending { color: #ff9800; }
    .status-filled { color: #4caf50; }
    .status-cancelled { color: #f44336; }
    .status-rejected { color: #e91e63; }
</style>
"""
