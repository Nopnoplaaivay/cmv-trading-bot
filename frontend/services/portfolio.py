import streamlit as st
import requests
from typing import Optional, Dict, List
from .auth import get_auth_headers, handle_auth_error
from ..utils.config import API_BASE_URL


class PortfolioService:
    @staticmethod
    def create_custom_portfolio(portfolio_name: str, symbols: List[str], description: str = None) -> Dict:
        """Create a new custom portfolio"""
        try:
            response = requests.post(
                f"{API_BASE_URL}/portfolio-service/custom",
                json={
                    "portfolio_name": portfolio_name,
                    "portfolio_desc": description,
                    "symbols": symbols
                },
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 201:
                return {"success": True, "data": response.json().get("data")}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    @staticmethod
    @st.cache_data(ttl=60)
    def get_my_portfolios() -> Optional[List[Dict]]:
        try:
            response = requests.get(
                f"{API_BASE_URL}/portfolio-service/me",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("data", [])
            elif handle_auth_error(response):
                return None
            else:
                st.error(f"Failed to get portfolios: {response.json().get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            return None

    @staticmethod
    @st.cache_data(ttl=60)
    def get_my_portfolio_by_id(portfolio_id: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{API_BASE_URL}/portfolio-service/{portfolio_id}",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("data", [])
            elif handle_auth_error(response):
                return None
            else:
                st.error(f"Failed to get portfolios: {response.json().get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            return None


    @staticmethod
    @st.cache_data(ttl=30)  # Cache for 30 seconds
    def get_system_portfolio_analysis(
        broker_account_id: str, strategy_type: str = "market_neutral"
    ) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{API_BASE_URL}/portfolio-service/analysis/{broker_account_id}",
                headers=get_auth_headers(),
                params={"strategy_type": strategy_type},
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("data")
            elif handle_auth_error(response):
                return None
            else:
                error_msg = response.json().get("message", "Unknown error")
                st.error(f"Failed to get portfolio analysis: {error_msg}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"API connection error: {str(e)}")
            return None


    @staticmethod
    @st.cache_data(ttl=30)
    def get_portfolio_analysis(portfolio_id: str, strategy_type: str = "market_neutral") -> Optional[Dict]:
        """Get analysis for specific portfolio"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/portfolio-service/{portfolio_id}/analysis",
                params={"strategy_type": strategy_type},
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return response.json().get("data")
            elif handle_auth_error(response):
                return None
            else:
                st.error(f"Failed to get analysis: {response.json().get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            return None

    @staticmethod
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_all_symbols() -> List[str]:
        """Get all available symbols from API"""
        # Fallback list of Vietnam symbols
        vietnam_symbols = [
            "VIC", "VHM", "VRE", "TCB", "VCB", "BID", "CTG", "MBB",
            "HPG", "MSN", "VNM", "SAB", "GAS", "PLX", "POW", "REE",
            "GMD", "DXG", "KDH", "NVL", "PDR", "STB", "TPB", "ACB",
            "EIB", "HDB", "LPB", "NAB", "OCB", "SHB", "SSB", "VIB",
            "APG", "BCM", "BVH", "CII", "DGC", "FPT", "GEX", "HNG",
            "IDI", "IJC", "KBC", "MWG", "NLG", "PNJ", "ROS", "SSI"
        ]

        try:
            response = requests.get(
                f"{API_BASE_URL}/portfolio-service/symbols",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                if isinstance(data, dict) and "records" in data:
                    # Extract symbols from records
                    symbols = [record.get("symbol") for record in data["records"] if record.get("symbol")]
                    return symbols if symbols else vietnam_symbols
                elif isinstance(data, list):
                    # Direct list of symbols
                    return data if data else vietnam_symbols
                else:
                    return vietnam_symbols
            elif handle_auth_error(response):
                return vietnam_symbols
            else:
                # Use fallback symbols on API error
                return vietnam_symbols

        except requests.exceptions.RequestException as e:
            # Use fallback symbols on network error
            return vietnam_symbols
            st.error(f"Network error: {str(e)}")
            return None

    @staticmethod
    def update_portfolio_symbols(portfolio_id: str, symbols: List[str]) -> Dict:
        """Update symbols in a custom portfolio"""
        try:
            response = requests.put(
                f"{API_BASE_URL}/portfolio-service/{portfolio_id}/symbols",
                json=symbols,  # Send symbols directly as list
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                # Clear cache after successful update
                PortfolioService.get_my_portfolios.clear()
                return {"success": True, "data": response.json().get("data")}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

#     @staticmethod
#     def delete_portfolio(portfolio_id: str) -> Dict:
#         """Delete a custom portfolio"""
#         try:
#             response = requests.delete(
#                 f"{API_BASE_URL}/portfolio-service/portfolios/{portfolio_id}",
#                 headers=get_auth_headers(),
#                 timeout=30,
#             )

#             if response.status_code == 200:
#                 # Clear cache after successful deletion
#                 PortfolioService.get_my_portfolios.clear()
#                 return {"success": True}
#             elif handle_auth_error(response):
#                 return {"success": False, "error": "Authentication failed"}
#             else:
#                 error_msg = response.json().get("message", "Unknown error")
#                 return {"success": False, "error": error_msg}

#         except requests.exceptions.RequestException as e:
#             return {"success": False, "error": f"Network error: {str(e)}"}


#     @staticmethod
#     @st.cache_data(ttl=300)  # Cache for 5 minutes
#     def search_symbols(query: str) -> List[str]:
#         """Search for stock symbols (mock implementation)"""
#         # In real implementation, this would call an API to search symbols
#         vietnam_symbols = [
#             "VIC", "VHM", "VRE", "TCB", "VCB", "BID", "CTG", "MBB",
#             "HPG", "MSN", "VNM", "SAB", "GAS", "PLX", "POW", "REE",
#             "GMD", "DXG", "KDH", "NVL", "PDR", "STB", "TPB", "ACB",
#             "EIB", "HDB", "LPB", "NAB", "OCB", "SHB", "SSB", "VIB",
#             "APG", "BCM", "BVH", "CII", "DGC", "FPT", "GEX", "HNG",
#             "IDI", "IJC", "KBC", "MWG", "NLG", "PNJ", "ROS", "SSI"
#         ]
        
#         if not query:
#             return vietnam_symbols[:20]  # Return first 20 if no query
        
#         # Simple filtering based on query
#         filtered = [symbol for symbol in vietnam_symbols 
#                    if query.upper() in symbol.upper()]
#         return filtered[:10]  # Return top 10 matches