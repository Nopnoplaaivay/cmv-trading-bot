#!/usr/bin/env python3
"""
Test script for admin role update functionality
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.modules.auth.services.auth import AuthService
from backend.modules.auth.dtos import UpdateRoleDTO
from backend.modules.auth.types import JwtPayload
from backend.utils.logger import LOGGER


async def test_admin_role_update():
    """Test the admin role update functionality."""

    print("=" * 60)
    print("Testing Admin Role Update Functionality")
    print("=" * 60)

    # Mock admin user (in real scenario this comes from JWT token)
    admin_user = JwtPayload(
        sessionId="mock-session-id",
        userId=1,
        role="admin",
        iat=1691145600,
        exp=1691232000,
    )

    # Mock non-admin user
    regular_user = JwtPayload(
        sessionId="mock-session-id-2",
        userId=2,
        role="free",
        iat=1691145600,
        exp=1691232000,
    )

    print("Test Scenarios:")
    print("-" * 40)

    # Test cases
    test_cases = [
        {
            "name": "Admin updating user to premium",
            "admin": admin_user,
            "payload": UpdateRoleDTO(target_account="testuser", new_role="premium"),
            "should_succeed": True,
        },
        {
            "name": "Admin updating user to admin",
            "admin": admin_user,
            "payload": UpdateRoleDTO(target_account="testuser", new_role="admin"),
            "should_succeed": True,
        },
        {
            "name": "Non-admin trying to update role",
            "admin": regular_user,
            "payload": UpdateRoleDTO(target_account="testuser", new_role="premium"),
            "should_succeed": False,
        },
        {
            "name": "Admin using invalid role",
            "admin": admin_user,
            "payload": UpdateRoleDTO(target_account="testuser", new_role="invalid"),
            "should_succeed": False,
        },
        {
            "name": "Admin targeting non-existent user",
            "admin": admin_user,
            "payload": UpdateRoleDTO(target_account="nonexistent", new_role="premium"),
            "should_succeed": False,
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Admin role: {test_case['admin'].role}")
        print(f"   Target: {test_case['payload'].target_account}")
        print(f"   New role: {test_case['payload'].new_role}")

        try:
            result = await AuthService.update_user_role(
                admin_user=test_case["admin"], payload=test_case["payload"]
            )

            if test_case["should_succeed"]:
                print(f"   ✅ SUCCESS: {result['message']}")
            else:
                print(f"   ❌ UNEXPECTED SUCCESS: {result}")

        except Exception as e:
            if not test_case["should_succeed"]:
                print(f"   ✅ EXPECTED FAILURE: {str(e)}")
            else:
                print(f"   ❌ UNEXPECTED FAILURE: {str(e)}")

    print("\n" + "=" * 60)
    print("API Usage Examples:")
    print("=" * 60)

    print(
        """
    # Using curl to update user role (Admin only):
    curl -X PUT http://localhost:8000/auth/admin/update-role \\
         -H "Content-Type: application/json" \\
         -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN" \\
         -d '{
             "target_account": "user123",
             "new_role": "premium"
         }'
    
    # Response format:
    {
        "http_code": 200,
        "status_code": 200,
        "message": "Success",
        "data": {
            "message": "Successfully updated user123 role to premium",
            "target_account": "user123",
            "new_role": "premium",
            "updated_by": 1
        }
    }
    
    # Valid roles: "free", "premium", "admin"
    # Only admin users can use this endpoint
    # Admin cannot demote their own account
    """
    )

    print("\n" + "=" * 60)
    print("Admin Role Update Test Completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: This test will fail on actual database operations
    # since we're using mock data. It's mainly for demonstrating
    # the logic and validation flow.
    print("Note: This test demonstrates the logic flow.")
    print("Database operations will fail with mock data.")
    print("Use this as a reference for the API functionality.\n")

    try:
        asyncio.run(test_admin_role_update())
    except Exception as e:
        print(f"Test completed with expected database errors: {e}")
