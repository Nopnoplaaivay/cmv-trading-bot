import streamlit as st
import requests
from typing import Optional, Dict

from frontend.services.auth import get_auth_headers, handle_auth_error
from frontend.utils.config import API_BASE_URL


class AdminService:
    @staticmethod
    @st.cache_data(ttl=60)
    def get_all_users() -> Optional[Dict]:
        try:
            response = requests.get(
                f"{API_BASE_URL}/admin-service/get-users",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json().get("data", [])}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    @staticmethod
    def create_user(
        account: str,
        password: str,
        role: str = "free",
        mobile: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict:
        try:
            payload = {
                "account": account,
                "password": password,
                "role": role,
                "mobile": mobile,
                "email": email,
            }

            response = requests.post(
                f"{API_BASE_URL}/admin-service/create-user",
                json=payload,
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
    def update_user(
        target_account: str,
        new_password: Optional[str] = None,
        new_role: Optional[str] = None,
        new_mobile: Optional[str] = None,
        new_email: Optional[str] = None,
    ) -> Dict:
        try:
            payload = {
                "target_account": target_account,
                "new_password": new_password,
                "new_role": new_role,
                "new_mobile": new_mobile,
                "new_email": new_email,
            }

            response = requests.put(
                f"{API_BASE_URL}/admin-service/update-user",
                json=payload,
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json().get("data")}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    @staticmethod
    def delete_user(user_id: str) -> Dict:
        try:
            response = requests.delete(
                f"{API_BASE_URL}/admin-service/delete-user/{user_id}",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return {"success": True, "message": "User deleted successfully"}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                return {"success": False, "error": "Unknown error"}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    @staticmethod
    def get_user_details(user_id: str) -> Dict:
        try:
            response = requests.get(
                f"{API_BASE_URL}/admin-service/get-user-details/{user_id}",
                headers=get_auth_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json().get("data")}
            elif handle_auth_error(response):
                return {"success": False, "error": "Authentication failed"}
            else:
                error_msg = response.json().get("message", "Unknown error")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Network error: {str(e)}"}
