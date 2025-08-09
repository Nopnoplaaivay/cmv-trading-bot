import streamlit as st
import requests
from typing import Optional, Dict
from ..utils.config import API_BASE_URL
from .auth import get_auth_headers, handle_auth_error




def setup_dnse_account(custody_code: str, password: str) -> bool:
    """Setup DNSE account via API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/accounts-service/setup",
            json={"username": custody_code, "password": password},
            headers=get_auth_headers(),
            timeout=30,
        )

        if response.status_code == 200:
            return True
        elif handle_auth_error(response):
            return False
        else:
            error_msg = response.json().get("message", "Unknown error")
            st.error(f"Failed to setup DNSE account: {error_msg}")
            return False

    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {str(e)}")
        return False


def send_portfolio_notification(
    broker_account_id: str,
    strategy_type: str = "market_neutral",
    include_trade_plan: bool = True,
) -> bool:
    """Send portfolio notification to Telegram"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio-service/notify/{broker_account_id}",
            headers=get_auth_headers(),
            params={
                "strategy_type": strategy_type,
                "include_trade_plan": include_trade_plan,
            },
            timeout=30,
        )
        return response.status_code == 200

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send notification: {str(e)}")
        return False
