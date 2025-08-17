import streamlit as st
import pandas as pd
import time
from typing import List, Dict, Optional

from frontend.services.admin import AdminService
from frontend.utils.helpers import format_currency, format_percentage


def clear_user_management_cache():
    if hasattr(AdminService.get_all_users, "clear"):
        AdminService.get_all_users.clear()


def user_management_page():
    if not st.session_state.get("authenticated", False):
        st.error("❌ Please login to access this page")
        return

    if st.session_state.get("role") != "admin":
        st.error("❌ Access denied. This page is only accessible by administrators.")
        return

    st.title("👥 User Management")
    st.markdown("---")

    # Create tabs for different management functions
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 All Users", "➕ Create User", "✏️ Edit User", "🗑️ Delete User"]
    )

    with tab1:
        render_users_list()

    with tab2:
        render_create_user_form()

    with tab3:
        render_edit_user_form()

    with tab4:
        render_delete_user_form()


def render_users_list():
    st.subheader("📋 All Users")

    # Refresh button
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh", key="refresh_users"):
            AdminService.get_all_users.clear()
            st.rerun()

    with st.spinner("Loading users..."):
        users_data = AdminService.get_all_users()

    if not users_data or not users_data.get("success"):
        st.error("Failed to load users data")
        return

    users = users_data.get("data", [])

    if not users:
        st.info("No users found in the system")
        return

    # Display users in a table
    users_df = pd.DataFrame(users)

    # Format the dataframe for better display
    if not users_df.empty:
        # Rename columns for better display
        display_columns = {
            "id": "ID",
            "account": "Account",
            "role": "Role",
            "mobile": "Mobile",
            "email": "Email",
            "createdAt": "Created At",
            "updatedAt": "Updated At",
        }

        # Select and rename columns that exist
        available_columns = [
            col for col in display_columns.keys() if col in users_df.columns
        ]
        display_df = users_df[available_columns].rename(columns=display_columns)

        # Format datetime columns if they exist
        for col in ["Created At", "Updated At"]:
            if col in display_df.columns:
                display_df[col] = pd.to_datetime(
                    display_df[col], errors="coerce"
                ).dt.strftime("%Y-%m-%d %H:%M")

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Show statistics
        st.markdown("#### 📊 User Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Users", len(users))

        with col2:
            admin_count = len([u for u in users if u.get("role") == "admin"])
            st.metric("Admins", admin_count)

        with col3:
            premium_count = len([u for u in users if u.get("role") == "premium"])
            st.metric("Premium Users", premium_count)

        with col4:
            free_count = len([u for u in users if u.get("role") == "free"])
            st.metric("Free Users", free_count)


def render_create_user_form():
    st.subheader("➕ Create New User")

    with st.form("create_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            account = st.text_input(
                "Account/Username *",
                placeholder="Enter username",
                help="Unique username for the user",
            )

            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Enter password",
                help="Password for the user account",
            )

        with col2:
            role = st.selectbox(
                "Role *",
                options=["free", "premium", "admin"],
                index=0,
                help="User role determines access permissions",
            )

            confirm_password = st.text_input(
                "Confirm Password *", type="password", placeholder="Re-enter password"
            )

        st.markdown("#### Optional Information")
        col3, col4 = st.columns(2)

        with col3:
            mobile = st.text_input("Mobile Phone", placeholder="Enter mobile number")

        with col4:
            email = st.text_input("Email", placeholder="Enter email address")

        # Submit button
        submitted = st.form_submit_button("🚀 Create User", type="primary")

        if submitted:
            if not account or not password:
                st.error("Account and password are required!")
                return

            if password != confirm_password:
                st.error("Passwords do not match!")
                return

            if len(password) < 6:
                st.error("Password must be at least 6 characters long!")
                return

            # Create user
            with st.spinner("Creating user..."):
                result = AdminService.create_user(
                    account=account,
                    password=password,
                    role=role,
                    mobile=mobile if mobile else None,
                    email=email if email else None,
                )

            if result.get("success"):
                st.success(f"✅ User '{account}' created successfully!")
                st.balloons()

                # Clear cache and refresh
                AdminService.get_all_users.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(
                    f"❌ Failed to create user: {result.get('error', 'Unknown error')}"
                )


def render_edit_user_form():
    st.subheader("✏️ Edit User")

    with st.spinner("Loading users..."):
        users_data = AdminService.get_all_users()

    if not users_data or not users_data.get("success"):
        st.error("Failed to load users data")
        return

    users = users_data.get("data", [])

    if not users:
        st.info("No users found to edit")
        return

    # User selector
    user_options = {f"{user['account']} (ID: {user['id']})": user for user in users}
    selected_user_display = st.selectbox(
        "Select User to Edit",
        options=list(user_options.keys()),
        key="edit_user_selector",
    )

    if not selected_user_display:
        return

    selected_user = user_options[selected_user_display]

    st.markdown(f"**Editing user:** {selected_user['account']}")

    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_password = st.text_input(
                "New Password (leave empty to keep current)",
                type="password",
                placeholder="Enter new password",
            )

            new_role = st.selectbox(
                "Role",
                options=["free", "premium", "admin"],
                index=["free", "premium", "admin"].index(
                    selected_user.get("role", "free")
                ),
                help="Change user role",
            )

        with col2:
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter new password",
            )

        # Optional fields
        st.markdown("#### Update Optional Information")
        col3, col4 = st.columns(2)

        with col3:
            new_mobile = st.text_input(
                "Mobile Phone",
                value=selected_user.get("mobile", None) or None,
                placeholder="Enter mobile number",
            )

        with col4:
            new_email = st.text_input(
                "Email",
                value=selected_user.get("email", None) or None,
                placeholder="Enter email address",
            )

        submitted = st.form_submit_button("💾 Update User", type="primary")

        if submitted:
            if new_password and new_password != confirm_new_password:
                st.error("New passwords do not match!")
                return

            if new_password and len(new_password) < 6:
                st.error("New password must be at least 6 characters long!")
                return

            with st.spinner("Updating user..."):
                result = AdminService.update_user(
                    target_account=selected_user["account"],
                    new_password=new_password if new_password else None,
                    new_role=(
                        new_role if new_role != selected_user.get("role") else None
                    ),
                    new_mobile=(
                        new_mobile if new_mobile != selected_user.get("mobile") else None
                    ),
                    new_email=(
                        new_email if new_email != selected_user.get("email") else None
                    ),
                )

            if result.get("success"):
                st.success(
                    f"✅ User '{selected_user['account']}' updated successfully!"
                )

                # Clear cache and refresh
                AdminService.get_all_users.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(
                    f"❌ Failed to update user: {result.get('error', 'Unknown error')}"
                )


def render_delete_user_form():
    st.subheader("🗑️ Delete User")
    st.warning("⚠️ **Warning:** Deleting a user is irreversible!")

    # Load users
    with st.spinner("Loading users..."):
        users_data = AdminService.get_all_users()

    if not users_data or not users_data.get("success"):
        st.error("Failed to load users data")
        return

    users = users_data.get("data", [])
    current_user_id = st.session_state.get("user_id")

    # Filter out current admin user
    deletable_users = [user for user in users if user.get("id") != current_user_id]

    if not deletable_users:
        st.info("No users available for deletion (cannot delete your own account)")
        return

    # User selector
    user_options = {
        f"{user['account']} (ID: {user['id']}) - {user.get('role', 'unknown')}": user
        for user in deletable_users
    }
    selected_user_display = st.selectbox(
        "Select User to Delete",
        options=list(user_options.keys()),
        key="delete_user_selector",
        help="You cannot delete your own account",
    )

    if not selected_user_display:
        return

    selected_user = user_options[selected_user_display]

    # Show user details
    st.markdown("#### User Details:")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**Account:** {selected_user['account']}")
        st.write(f"**Role:** {selected_user.get('role', 'N/A')}")

    with col2:
        st.write(f"**Mobile:** {selected_user.get('mobile', 'N/A')}")
        st.write(f"**Email:** {selected_user.get('email', 'N/A')}")

    with col3:
        st.write(f"**Created:** {selected_user.get('createdAt', 'N/A')}")
        st.write(f"**Updated:** {selected_user.get('updatedAt', 'N/A')}")

    # Confirmation
    st.markdown("---")
    confirm_text = st.text_input(
        f"Type '{selected_user['account']}' to confirm deletion:",
        placeholder=f"Type {selected_user['account']} here",
    )

    # Delete button
    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button(
            "🗑️ DELETE",
            type="primary",
            disabled=confirm_text != selected_user["account"],
            key="confirm_delete_button",
        ):
            if confirm_text == selected_user["account"]:
                with st.spinner("Deleting user..."):
                    result = AdminService.delete_user(user_id=str(selected_user["id"]))

                if result.get("success"):
                    st.success(
                        f"✅ User '{selected_user['account']}' deleted successfully!"
                    )

                    # Clear cache and refresh
                    AdminService.get_all_users.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(
                        f"❌ Failed to delete user: {result.get('error', 'Unknown error')}"
                    )
            else:
                st.error("Please type the account name correctly to confirm deletion!")

    with col2:
        if confirm_text != selected_user["account"]:
            st.info("Type the account name exactly to enable the delete button")


# CSS for user management page
USER_MANAGEMENT_CSS = """
<style>
    .user-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e6ed;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-stats {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .danger-zone {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-zone {
        background: #f0fff4;
        border: 1px solid #9ae6b4;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
"""
