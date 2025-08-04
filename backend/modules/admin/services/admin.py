from typing import Dict

from backend.common.responses.exceptions import BaseExceptionResponse
from backend.common.consts import SQLServerConsts, MessageConsts
from backend.modules.base.query_builder import TextSQL
from backend.modules.auth.types import JwtPayload
from backend.modules.auth.entities import Users, Sessions
from backend.modules.auth.repositories import UsersRepo, SessionsRepo
from backend.modules.admin.dtos import UpdateRoleDTO
from backend.utils.logger import LOGGER


class AdminService:
    @classmethod
    async def get_all_users(cls):
        records = await UsersRepo.get_all()
        return records

    @classmethod
    async def update_user_role(
        cls, admin_user: JwtPayload, payload: UpdateRoleDTO
    ) -> Dict[str, str]:
        if admin_user.role != "admin":
            raise BaseExceptionResponse(
                http_code=403,
                status_code=403,
                message=MessageConsts.FORBIDDEN,
                errors="Only admin users can update roles",
            )

        # Validate the new role
        valid_roles = ["free", "premium", "admin"]
        if payload.new_role not in valid_roles:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors=f"Invalid role. Valid roles are: {', '.join(valid_roles)}",
            )

        # Check if target user exists
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

        # Prevent admin from demoting themselves
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

        # Update the user's role
        await UsersRepo.update(
            record={
                Users.id.name: target_user[Users.id.name],
                Users.account.name: payload.target_account,
                Users.role.name: payload.new_role,
            },
            identity_columns=[Users.id.name],
            returning=False,
            text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
        )

        # Update all active sessions of the target user with new role
        target_user_sessions = await SessionsRepo.get_by_condition(
            {Sessions.userId.name: target_user[Users.id.name]}
        )
        if len(target_user_sessions) > 0:
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
                text_clauses={"__updatedAt__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
            )

        LOGGER.info(
            f"Admin {admin_user.userId} updated user {payload.target_account} role to {payload.new_role}"
        )

        return {
            "message": f"Successfully updated {payload.target_account} role to {payload.new_role}",
            "target_account": payload.target_account,
            "new_role": payload.new_role,
            "updated_by": admin_user.userId,
        }
