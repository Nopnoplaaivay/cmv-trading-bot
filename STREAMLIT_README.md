# CMV Trading Bot - Streamlit Frontend

A comprehensive, professional-grade Streamlit frontend for the CMV Trading Bot that integrates seamlessly with your existing FastAPI backend and DNSE API client.

## 🌟 Features

### 🔐 Authentication & Security
- Secure JWT-based authentication
- Session management with auto-refresh
- Protected routes and API calls

### 📊 Portfolio Management
- Real-time portfolio analysis
- Current positions visualization
- Target vs current weight comparison
- Performance metrics and charts

### 🎯 Trade Recommendations
- Intelligent buy/sell recommendations
- Priority-based recommendation system
- Bulk execution capabilities
- Individual order execution

### ⚡ Order Management
- Quick order entry form
- Real-time order status tracking
- Order history and management
- Order cancellation

### 🏦 Account Management
- DNSE account setup
- Account status monitoring
- Multi-account support

### 📈 Analytics & Visualization
- Interactive portfolio charts
- Performance tracking
- Risk metrics dashboard
- Historical analysis

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Your FastAPI backend running on `http://localhost:8000`
- DNSE API credentials

### Installation Methods

#### Method 1: Automatic Setup (Recommended)
```bash
# Run the full stack startup script
python run_full_stack.py
```

This will:
- Start your FastAPI backend
- Install all requirements
- Start the Streamlit frontend
- Open your browser automatically

#### Method 2: Manual Setup

1. **Install Requirements**
   ```bash
   pip install -r streamlit_requirements.txt
   ```

2. **Start Backend** (in separate terminal)
   ```bash
   python -m uvicorn backend.app:app --reload
   ```

3. **Start Frontend**
   ```bash
   streamlit run streamlit_enhanced.py
   ```

#### Method 3: Windows Batch Script
```bash
# Double-click or run
run_streamlit.bat
```

### 🌐 Access Points

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 User Interface

### Login Page
- Clean, professional login interface
- Secure authentication with your backend
- Error handling and validation

### Dashboard
- **Portfolio Analysis**: Real-time portfolio overview
- **Trade Execution**: Order placement and management
- **Order History**: Track all your trading activity
- **Account Management**: Setup and manage DNSE accounts

### Key Components

#### 1. Portfolio Summary
```
💰 Available Cash    💎 Net Asset Value    💰 Cash Ratio    📊 Strategy
$25,000.00          $100,000.00          25.0%           Market Neutral
```

#### 2. Current Positions
- Interactive pie chart of portfolio weights
- Top positions bar chart
- Detailed positions table with P&L

#### 3. Trade Recommendations
- **Buy Orders**: Recommendations to increase positions
- **Sell Orders**: Recommendations to reduce positions
- **Bulk Execute**: Execute multiple orders simultaneously

#### 4. Weight Comparison
- Visual comparison of current vs target weights
- Deviation analysis
- Rebalancing insights

## 🔧 Configuration

### API Configuration
```python
# In streamlit_enhanced.py
API_BASE_URL = "http://localhost:8000/api/v1"
```

### Streamlit Configuration
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#2a5298"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## 🎨 Styling & Theme

The application features a professional financial theme with:
- Clean, modern interface
- Responsive design
- Interactive charts and visualizations
- Priority-based color coding for recommendations
- Professional typography and spacing

### Color Scheme
- **Primary**: #2a5298 (Professional blue)
- **Success**: #4caf50 (Green)
- **Warning**: #ff9800 (Orange)
- **Error**: #f44336 (Red)

## 📊 API Integration

### Endpoints Used

#### Authentication
- `POST /auth-service/login`
- `POST /auth-service/logout`

#### Portfolio
- `GET /portfolio-service/analysis/{account_id}`
- `POST /portfolio-service/notify/{account_id}`

#### Accounts
- `POST /accounts-service/setup-dnse`

#### DNSE Trading (Simulated)
The frontend includes simulated DNSE trading functions that demonstrate:
- Order placement
- Order status tracking
- Order cancellation

> **Note**: In production, these would integrate with your actual DNSE API client.

## 🔄 Real-time Features

### Auto-refresh
- Portfolio data auto-refresh every 30 seconds
- Real-time order status updates
- Live performance metrics

### Caching
- Smart caching of portfolio data (30-second TTL)
- Efficient API call management
- Reduced backend load

## 🛡️ Security Features

### Session Management
- Secure JWT token storage
- Automatic token refresh
- Session timeout handling

### API Security
- Bearer token authentication
- CORS-compliant requests
- Error handling and validation

## 📈 Advanced Features

### Portfolio Analytics
- Risk metrics (Volatility, Sharpe Ratio, Beta)
- Performance tracking
- Drawdown analysis
- Historical performance simulation

### Order Management
- Bulk order execution
- Progress tracking
- Success/failure reporting
- Order history persistence

### Notifications
- Telegram integration
- Portfolio report notifications
- Trade execution alerts

## 🔧 Customization

### Adding New Features
1. **New API Endpoints**: Add functions in the API integration section
2. **New UI Components**: Create new display functions
3. **New Pages**: Add to the navigation system
4. **Custom Styling**: Modify the CSS in the markdown sections

### Configuration Options
```python
# Customizable settings
WEIGHT_TOLERANCE = 2.0  # Minimum weight difference for recommendations
AUTO_REFRESH_INTERVAL = 30  # Seconds
ORDER_SIMULATION = True  # Enable simulated trading
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Backend Connection Error
```
Error: API connection error: Connection refused
```
**Solution**: Ensure your FastAPI backend is running on `http://localhost:8000`

#### 2. Authentication Failed
```
Error: Login failed: Invalid credentials
```
**Solution**: Check your username/password or backend authentication configuration

#### 3. No Portfolio Data
```
Error: Failed to load portfolio data
```
**Solution**: Verify your broker account ID and ensure DNSE account is set up

#### 4. Module Import Error
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution**: Install requirements with `pip install -r streamlit_requirements.txt`

### Debug Mode
Enable debug logging by adding:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Dependencies

### Core Requirements
- `streamlit>=1.28.0`: Web application framework
- `requests>=2.31.0`: HTTP client for API calls
- `pandas>=2.0.0`: Data manipulation and analysis
- `plotly>=5.17.0`: Interactive charts and visualizations
- `numpy>=1.24.0`: Numerical computing

### Development Tools
- `watchdog`: File monitoring for auto-reload
- `pytest`: Testing framework
- `black`: Code formatting

## 🔮 Future Enhancements

### Planned Features
- [ ] Real-time market data integration
- [ ] Advanced charting with technical indicators
- [ ] Portfolio optimization tools
- [ ] Risk management dashboard
- [ ] Mobile-responsive design improvements
- [ ] Multi-language support
- [ ] Dark theme option
- [ ] Export functionality for reports

### Integration Roadmap
- [ ] Direct DNSE API integration
- [ ] WebSocket support for real-time updates
- [ ] Database persistence for UI preferences
- [ ] Advanced analytics with ML predictions
- [ ] Multi-broker support

## 📞 Support

### Getting Help
1. **Documentation**: Check this README and code comments
2. **API Documentation**: Visit `http://localhost:8000/docs`
3. **Debug Logs**: Check terminal output for error messages
4. **Configuration**: Verify `.streamlit/config.toml` settings

### Reporting Issues
When reporting issues, please include:
- Error messages from terminal
- Browser console errors
- Steps to reproduce
- System information (OS, Python version)

## 📄 License

This project is part of the CMV Trading Bot system. Please refer to the main project license.

---

**Built with ❤️ using Streamlit and modern Python technologies**

*Professional trading interface designed for serious portfolio management*
