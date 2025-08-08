# frontend/styles/portfolio_styles.py (continued)
"""
Additional CSS styles for portfolio management
"""

PORTFOLIO_CSS = """
<style>
   /* Portfolio Cards */
   .portfolio-card {
       background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
       border: 1px solid #e9ecef;
       border-radius: 12px;
       padding: 1.5rem;
       margin: 1rem 0;
       box-shadow: 0 4px 6px rgba(0,0,0,0.1);
       transition: all 0.3s ease;
   }
   
   .portfolio-card:hover {
       transform: translateY(-5px);
       box-shadow: 0 8px 15px rgba(0,0,0,0.15);
   }
   
   .portfolio-card.system {
       border-left: 5px solid #2a5298;
       background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
   }
   
   .portfolio-card.custom {
       border-left: 5px solid #4caf50;
       background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
   }
   
   /* Portfolio Stats */
   .portfolio-stats {
       display: flex;
       justify-content: space-around;
       background: rgba(255,255,255,0.8);
       border-radius: 8px;
       padding: 1rem;
       margin: 1rem 0;
   }
   
   .stat-item {
       text-align: center;
       flex: 1;
   }
   
   .stat-value {
       font-size: 1.5rem;
       font-weight: bold;
       color: #2a5298;
   }
   
   .stat-label {
       font-size: 0.9rem;
       color: #666;
       margin-top: 0.25rem;
   }
   
   /* Symbol Tags */
   .symbol-tag {
       display: inline-block;
       background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
       color: white;
       padding: 0.25rem 0.75rem;
       border-radius: 20px;
       font-size: 0.85rem;
       font-weight: 500;
       margin: 0.25rem;
       transition: all 0.2s ease;
   }
   
   .symbol-tag:hover {
       transform: scale(1.05);
       box-shadow: 0 2px 8px rgba(42,82,152,0.3);
   }
   
   .symbol-tag.removable {
       background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
       cursor: pointer;
   }
   
   .symbol-tag.addable {
       background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
       cursor: pointer;
   }
   
   /* Portfolio Creation Form */
   .portfolio-form {
       background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
       border: 1px solid #e0e0e0;
       border-radius: 12px;
       padding: 2rem;
       margin: 1rem 0;
   }
   
   .form-section {
       margin-bottom: 1.5rem;
       padding-bottom: 1rem;
       border-bottom: 1px solid #e9ecef;
   }
   
   .form-section:last-child {
       border-bottom: none;
       margin-bottom: 0;
   }
   
   /* Symbol Search */
   .symbol-search-results {
       background: #f8f9fa;
       border: 1px solid #dee2e6;
       border-radius: 8px;
       padding: 1rem;
       margin: 0.5rem 0;
       max-height: 200px;
       overflow-y: auto;
   }
   
   .symbol-search-item {
       background: white;
       border: 1px solid #e9ecef;
       border-radius: 6px;
       padding: 0.5rem 1rem;
       margin: 0.25rem;
       display: inline-block;
       cursor: pointer;
       transition: all 0.2s ease;
   }
   
   .symbol-search-item:hover {
       background: #e3f2fd;
       border-color: #2a5298;
       transform: translateY(-1px);
   }
   
   /* Portfolio Comparison */
   .comparison-table {
       background: white;
       border-radius: 12px;
       overflow: hidden;
       box-shadow: 0 4px 6px rgba(0,0,0,0.1);
       margin: 1rem 0;
   }
   
   .comparison-header {
       background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
       color: white;
       padding: 1rem;
       font-weight: bold;
   }
   
   .comparison-row {
       padding: 0.75rem 1rem;
       border-bottom: 1px solid #e9ecef;
       transition: background-color 0.2s ease;
   }
   
   .comparison-row:hover {
       background-color: #f8f9fa;
   }
   
   .comparison-row:last-child {
       border-bottom: none;
   }
   
   /* Action Buttons */
   .action-button {
       border-radius: 8px;
       border: none;
       padding: 0.5rem 1rem;
       font-weight: 500;
       transition: all 0.2s ease;
       cursor: pointer;
       margin: 0.25rem;
   }
   
   .action-button.primary {
       background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
       color: white;
   }
   
   .action-button.primary:hover {
       transform: translateY(-2px);
       box-shadow: 0 4px 8px rgba(42,82,152,0.3);
   }
   
   .action-button.success {
       background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
       color: white;
   }
   
   .action-button.success:hover {
       transform: translateY(-2px);
       box-shadow: 0 4px 8px rgba(76,175,80,0.3);
   }
   
   .action-button.danger {
       background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
       color: white;
   }
   
   .action-button.danger:hover {
       transform: translateY(-2px);
       box-shadow: 0 4px 8px rgba(244,67,54,0.3);
   }
   
   .action-button.secondary {
       background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
       color: white;
   }
   
   /* Portfolio Performance Charts */
   .performance-chart-container {
       background: white;
       border-radius: 12px;
       padding: 1.5rem;
       margin: 1rem 0;
       box-shadow: 0 4px 6px rgba(0,0,0,0.1);
   }
   
   /* Template Cards */
   .template-card {
       background: linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%);
       border: 1px solid #c8e6c9;
       border-radius: 8px;
       padding: 1rem;
       margin: 0.5rem 0;
       cursor: pointer;
       transition: all 0.2s ease;
   }
   
   .template-card:hover {
       border-color: #4caf50;
       transform: translateY(-2px);
       box-shadow: 0 4px 8px rgba(76,175,80,0.2);
   }
   
   .template-name {
       font-weight: bold;
       color: #2e7d32;
       margin-bottom: 0.5rem;
   }
   
   .template-symbols {
       font-size: 0.9rem;
       color: #424242;
   }
   
   /* Status Indicators */
   .status-active {
       color: #4caf50;
       font-weight: bold;
   }
   
   .status-inactive {
       color: #f44336;
       font-weight: bold;
   }
   
   .status-system {
       color: #2a5298;
       font-weight: bold;
   }
   
   /* Responsive Design */
   @media (max-width: 768px) {
       .portfolio-card {
           padding: 1rem;
           margin: 0.5rem 0;
       }
       
       .portfolio-stats {
           flex-direction: column;
       }
       
       .stat-item {
           margin: 0.5rem 0;
       }
       
       .symbol-tag {
           font-size: 0.8rem;
           padding: 0.2rem 0.5rem;
       }
       
       .action-button {
           width: 100%;
           margin: 0.25rem 0;
       }
   }
   
   /* Animation Classes */
   .fade-in {
       animation: fadeIn 0.5s ease-in;
   }
   
   @keyframes fadeIn {
       from { opacity: 0; transform: translateY(20px); }
       to { opacity: 1; transform: translateY(0); }
   }
   
   .slide-in {
       animation: slideIn 0.3s ease-out;
   }
   
   @keyframes slideIn {
       from { transform: translateX(-100%); }
       to { transform: translateX(0); }
   }
   
   /* Loading States */
   .loading-skeleton {
       background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
       background-size: 200% 100%;
       animation: loading 1.5s infinite;
   }
   
   @keyframes loading {
       0% { background-position: 200% 0; }
       100% { background-position: -200% 0; }
   }
   
   /* Tooltip Styles */
   .tooltip {
       position: relative;
       display: inline-block;
   }
   
   .tooltip .tooltiptext {
       visibility: hidden;
       width: 200px;
       background-color: #333;
       color: #fff;
       text-align: center;
       border-radius: 6px;
       padding: 5px 10px;
       position: absolute;
       z-index: 1;
       bottom: 125%;
       left: 50%;
       margin-left: -100px;
       opacity: 0;
       transition: opacity 0.3s;
       font-size: 0.85rem;
   }
   
   .tooltip:hover .tooltiptext {
       visibility: visible;
       opacity: 1;
   }
</style>
"""

# Update main CSS to include portfolio styles
ENHANCED_MAIN_CSS = """
<style>
   /* Original styles */
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
   
   /* Enhanced Button Styles */
   .stButton > button {
       border-radius: 8px;
       border: none;
       background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
       color: white;
       padding: 0.5rem 1rem;
       transition: all 0.2s;
       font-weight: 500;
   }
   
   .stButton > button:hover {
       transform: translateY(-2px);
       box-shadow: 0 4px 8px rgba(42,82,152,0.3);
   }
   
   /* Tab Styling */
   .stTabs [data-baseweb="tab-list"] {
       gap: 8px;
   }
   
   .stTabs [data-baseweb="tab"] {
       border-radius: 8px 8px 0 0;
       background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
       border: 1px solid #dee2e6;
       color: #495057;
       font-weight: 500;
   }
   
   .stTabs [aria-selected="true"] {
       background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
       color: white;
       border-color: #2a5298;
   }
   
   /* Form Styling */
   .stTextInput > div > div > input {
       border-radius: 8px;
       border: 2px solid #e9ecef;
       transition: border-color 0.2s;
   }
   
   .stTextInput > div > div > input:focus {
       border-color: #2a5298;
       box-shadow: 0 0 0 0.2rem rgba(42,82,152,0.25);
   }
   
   .stSelectbox > div > div > div {
       border-radius: 8px;
       border: 2px solid #e9ecef;
   }
   
   .stTextArea > div > div > textarea {
       border-radius: 8px;
       border: 2px solid #e9ecef;
   }
   
   /* Sidebar Enhancement */
   .sidebar .sidebar-content {
       background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
   }
   
   /* Alert Boxes */
   .alert-success {
       background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
       border: 1px solid #c3e6cb;
       color: #155724;
       padding: 1rem;
       border-radius: 8px;
       margin: 1rem 0;
   }
   
   .alert-warning {
       background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
       border: 1px solid #ffeaa7;
       color: #856404;
       padding: 1rem;
       border-radius: 8px;
       margin: 1rem 0;
   }
   
   .alert-error {
       background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
       border: 1px solid #f5c6cb;
       color: #721c24;
       padding: 1rem;
       border-radius: 8px;
       margin: 1rem 0;
   }
   
   .alert-info {
       background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
       border: 1px solid #bee5eb;
       color: #0c5460;
       padding: 1rem;
       border-radius: 8px;
       margin: 1rem 0;
   }
   
   /* Loading Spinner */
   .loading-container {
       display: flex;
       justify-content: center;
       align-items: center;
       padding: 2rem;
   }
   
   .spinner {
       border: 4px solid #f3f3f3;
       border-top: 4px solid #2a5298;
       border-radius: 50%;
       width: 40px;
       height: 40px;
       animation: spin 1s linear infinite;
   }
   
   @keyframes spin {
       0% { transform: rotate(0deg); }
       100% { transform: rotate(360deg); }
   }
</style>
""" + PORTFOLIO_CSS