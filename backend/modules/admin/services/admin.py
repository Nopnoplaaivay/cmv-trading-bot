from typing import Dict, List, Optional
import hashlib

from backend.common.responses.exceptions import BaseExceptionResponse
from backend.common.consts import SQLServerConsts, MessageConsts
from backend.modules.auth.decorators import payload
from backend.modules.base.query_builder import TextSQL
from backend.modules.auth.types import JwtPayload
from backend.modules.auth.entities import Users, Sessions, Role
from backend.modules.auth.repositories import UsersRepo, SessionsRepo
from backend.modules.admin.dtos import (
    CreateUserDTO,
    UpdateUserInfoDTO
)
from backend.utils.logger import LOGGER


class AdminService:
    @classmethod
    async def get_all_users(cls):
        records = await UsersRepo.get_all()
        return records

    # @classmethod
    # async def update_user_role(
    #     cls, admin_user: JwtPayload, payload: UpdateRoleDTO
    # ) -> Dict[str, str]:
    #     valid_roles = ["free", "premium", "admin"]
    #     if payload.new_role not in valid_roles:
    #         raise BaseExceptionResponse(
    #             http_code=400,
    #             status_code=400,
    #             message=MessageConsts.BAD_REQUEST,
    #             errors=f"Invalid role. Valid roles are: {', '.join(valid_roles)}",
    #         )

    #     target_users = await UsersRepo.get_by_condition(
    #         {Users.account.name: payload.target_account}
    #     )
    #     if not target_users:
    #         raise BaseExceptionResponse(
    #             http_code=404,
    #             status_code=404,
    #             message=MessageConsts.NOT_FOUND,
    #             errors="Target user not found",
    #         )

    #     target_user = target_users[0]

    #     if (
    #         target_user[Users.id.name] == admin_user.userId
    #         and payload.new_role != "admin"
    #     ):
    #         raise BaseExceptionResponse(
    #             http_code=400,
    #             status_code=400,
    #             message=MessageConsts.BAD_REQUEST,
    #             errors="Admin cannot demote their own account",
    #         )

    #     await UsersRepo.update(
    #         record={
    #             Users.id.name: target_user[Users.id.name],
    #             Users.account.name: payload.target_account,
    #             Users.role.name: payload.new_role,
    #         },
    #         identity_columns=[Users.id.name],
    #         returning=False,
    #         text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
    #     )

    #     target_user_sessions = await SessionsRepo.get_by_condition(
    #         {Sessions.userId.name: target_user[Users.id.name]}
    #     )
    #     if len(target_user_sessions) > 0:
    #         sessions = [
    #             {
    #                 Sessions.id.name: session[Sessions.id.name],
    #                 Sessions.role.name: payload.new_role,
    #             }
    #             for session in target_user_sessions
    #         ]
    #         await SessionsRepo.update_many(
    #             records=sessions,
    #             identity_columns=[Sessions.id.name],
    #             returning=False,
    #             text_clauses={
    #                 "__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)
    #             },
    #         )

    #     LOGGER.info(
    #         f"Admin {admin_user.userId} updated user {payload.target_account} role to {payload.new_role}"
    #     )

    #     return {
    #         "message": f"Successfully updated {payload.target_account} role to {payload.new_role}",
    #         "target_account": payload.target_account,
    #         "new_role": payload.new_role,
    #         "updated_by": admin_user.userId,
    #     }

    @classmethod
    async def create_user(
        cls, admin_user: JwtPayload, payload: CreateUserDTO
    ) -> Dict[str, str]:
        if admin_user.role != "admin":
            raise BaseExceptionResponse(
                http_code=403,
                status_code=403,
                message=MessageConsts.FORBIDDEN,
                errors="Only admin users can create users",
            )

        # Validate role
        valid_roles = ["free", "premium", "admin"]
        if payload.role not in valid_roles:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors=f"Invalid role. Valid roles are: {', '.join(valid_roles)}",
            )

        # Check if user already exists
        existing_users = await UsersRepo.get_by_condition(
            {Users.account.name: payload.account}
        )
        if existing_users:
            raise BaseExceptionResponse(
                http_code=409,
                status_code=409,
                message=MessageConsts.CONFLICT,
                errors="User account already exists",
            )

        # Hash password (same method as auth service)
        hashed_password = hashlib.sha256(payload.password.encode()).hexdigest()

        # Create user record
        new_user = {
            Users.account.name: payload.account,
            Users.password.name: hashed_password,
            Users.role.name: payload.role,
            Users.mobile.name: payload.mobile,
            Users.email.name: payload.email,
        }

        created_user = await UsersRepo.insert(
            record=new_user,
            returning=True
        )

        LOGGER.info(
            f"Admin {admin_user.userId} created new user {payload.account} with role {payload.role}"
        )

        return {
            "message": f"Successfully created user {payload.account}",
            "user_id": created_user[Users.id.name],
            "account": payload.account,
            "role": payload.role,
            "created_by": admin_user.userId,
        }

    @classmethod
    async def update_user_info(
        cls, admin_user: JwtPayload, payload: UpdateUserInfoDTO
    ) -> Dict[str, str]:
        target_users = await UsersRepo.get_by_condition(
            {Users.account.name: payload.target_account}
        )
        if not target_users:
            raise BaseExceptionResponse(
                http_code=404,
                status_code=404,
                message=MessageConsts.NOT_FOUND,
                errors="Target user not found",
            )

        target_user = target_users[0]
        update_data = {
            Users.id.name: target_user[Users.id.name],
            Users.account.name: payload.target_account,
        }

        if payload.new_role is not None:
            valid_roles = ["free", "premium", "admin"]
            if payload.new_role not in valid_roles:
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message=MessageConsts.BAD_REQUEST,
                    errors=f"Invalid role. Valid roles are: {', '.join(valid_roles)}",
                )

            if (
                target_user[Users.id.name] == admin_user.userId
                and payload.new_role != "admin"
            ):
                raise BaseExceptionResponse(
                    http_code=400,
                    status_code=400,
                    message=MessageConsts.BAD_REQUEST,
                    errors="Admin cannot demote their own account",
                )

            update_data[Users.role.name] = payload.new_role

        # Hash new password if provided
        if payload.new_password is not None:
            update_data[Users.password.name] = hashlib.sha256(
                payload.new_password.encode()
            ).hexdigest()

        # Set new mobile and email
        if payload.new_mobile is not None:
            update_data[Users.mobile.name] = payload.new_mobile

        if payload.new_email is not None:
            update_data[Users.email.name] = payload.new_email

        # Update user
        await UsersRepo.update(
            record=update_data,
            identity_columns=[Users.id.name],
            returning=False,
            text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
        )

        # Update sessions if role changed
        if payload.new_role is not None:
            target_user_sessions = await SessionsRepo.get_by_condition(
                {Sessions.userId.name: target_user[Users.id.name]}
            )
            if target_user_sessions:
                sessions = [
                    {
                        Sessions.id.name: session[Sessions.id.name],
                        Sessions.role.name: payload.new_role,
                    }
                    for session in target_user_sessions
                ]
                await SessionsRepo.update_many(
                    records=sessions,
                    identity_columns=[Sessions.id.name],
                    returning=False,
                    text_clauses={
                        "__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)
                    },
                )

        updated_fields = []
        if payload.new_password:
            updated_fields.append("password")
        if payload.new_role:
            updated_fields.append(f"role to {payload.new_role}")
        if payload.new_mobile:
            updated_fields.append("mobile")
        if payload.new_email:
            updated_fields.append("email")

        LOGGER.info(
            f"Admin {admin_user.userId} updated user {payload.target_account}: {', '.join(updated_fields)}"
        )

        return {
            "message": f"Successfully updated user {payload.target_account}",
            "target_account": payload.target_account,
            "updated_fields": updated_fields,
            "updated_by": admin_user.userId,
        }

    @classmethod
    async def delete_user(
        cls, admin_user: JwtPayload, user_id: str
    ) -> Dict[str, str]:
        target_users = await UsersRepo.get_by_condition(
            {Users.id.name: user_id}
        )
        if not target_users:
            raise BaseExceptionResponse(
                http_code=404,
                status_code=404,
                message=MessageConsts.NOT_FOUND,
                errors="Target user not found",
            )

        target_user = target_users[0]

        if target_user[Users.id.name] == admin_user.userId:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors="Admin cannot delete their own account",
            )
        await UsersRepo.delete({Users.id.name: target_user[Users.id.name]})

        LOGGER.info(
            f"Admin {admin_user.userId} deleted user {user_id} (ID: {target_user[Users.id.name]})"
        )

        return 

    @classmethod
    async def get_user_details(
        cls, admin_user: JwtPayload, user_id: str
    ) -> Dict:
        target_users = await UsersRepo.get_by_condition(
            {Users.id.name: user_id}
        )
        if not target_users:
            raise BaseExceptionResponse(
                http_code=404,
                status_code=404,
                message=MessageConsts.NOT_FOUND,
                errors="Target user not found",
            )

        target_user = target_users[0]

        user_sessions = await SessionsRepo.get_by_condition(
            {Sessions.userId.name: target_user[Users.id.name]}
        )

        return {
            "user_info": {
                "id": target_user[Users.id.name],
                "account": target_user[Users.account.name],
                "role": target_user[Users.role.name],
                "mobile": target_user.get(Users.mobile.name),
                "email": target_user.get(Users.email.name),
            },
            "active_sessions": len(user_sessions),
            "session_details": [
                {
                    "session_id": session[Sessions.id.name],
                    "created_at": session.get(Sessions.createdAt.name),
                    "updated_at": session.get(Sessions.updatedAt.name),
                }
                for session in user_sessions
            ],
        }
