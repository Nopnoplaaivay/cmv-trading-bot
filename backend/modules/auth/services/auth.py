import os
import hashlib
import uuid
import jwt
from cachetools import TTLCache
from datetime import timedelta
from typing import Dict

from backend.common.consts import MessageConsts, CommonConsts, SQLServerConsts
from backend.modules.base.query_builder import TextSQL
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.auth.dtos import RegisterDTO, LoginDTO, LogoutDTO, RefreshDTO
from backend.modules.auth.types import JwtPayload, RefreshPayload
from backend.modules.auth.entities import Users, Sessions
from backend.modules.auth.repositories import UsersRepo, SessionsRepo
from backend.utils.jwt_utils import JWTUtils
from backend.utils.time_utils import TimeUtils
from backend.utils.logger import LOGGER

black_list = TTLCache(maxsize=1000, ttl=24 * 60 * 60)

class AuthService:
    @classmethod
    async def register(cls, payload: RegisterDTO) -> None:
        if await UsersRepo.get_by_condition({Users.account.name: payload.account}):
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors="Account already exists",
            )
        if payload.password != payload.confirm_password:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors="Passwords do not match",
            )
        salted_password = f"{CommonConsts.SALT}{payload.password}"
        user = await UsersRepo.insert(
            record={
                Users.account.name: payload.account,
                Users.password.name: hashlib.sha256(
                    salted_password.encode("utf-8")
                ).hexdigest(),
                Users.role.name: payload.role
            },
            returning=True,
        )

        LOGGER.info(f"User {payload.account} has been created")

    @classmethod
    async def login(cls, payload: LoginDTO) -> Dict[str, str]:
        records = await UsersRepo.get_by_condition(
            {Users.account.name: payload.account}
        )
        user = records[0] if records else None
        if not user:
            raise BaseExceptionResponse(
                http_code=400,
                status_code=400,
                message=MessageConsts.BAD_REQUEST,
                errors="Account does not exist",
            )
        salted_password = f"{CommonConsts.SALT}{payload.password}"
        if (
            user[Users.password.name]
            != hashlib.sha256(salted_password.encode("utf-8")).hexdigest()
        ):
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Invalid credentials",
            )
        return await cls.create_token_pair(user)

    @classmethod
    async def create_token_pair(cls, user: Dict) -> Dict[str, str]:
        session_id = str(uuid.uuid4())
        signature = os.urandom(16).hex()
        expires_at = TimeUtils.get_current_vn_time() + timedelta(
            seconds=CommonConsts.REFRESH_TOKEN_EXPIRES_IN
        )
        session = await SessionsRepo.insert(
            record={
                Sessions.id.name: session_id,
                Sessions.user_id.name: user[Users.id.name],
                Sessions.signature.name: signature,
                Sessions.expires_at.name: expires_at,
                Sessions.role.name: user[Users.role.name],
            },
            returning=True,
        )

        at_payload = JwtPayload(
            sessionId=session[Sessions.id.name],
            userId=user[Users.id.name],
            role=user[Users.role.name],
        )
        rt_payload = RefreshPayload(
            sessionId=session[Sessions.id.name],
            userId=user[Users.id.name],
            role=user[Users.role.name],
            signature=signature,
        )

        access_token = JWTUtils.create_access_token(payload=at_payload)
        refresh_token = JWTUtils.create_refresh_token(payload=rt_payload)


        return {"accessToken": access_token, "refreshToken": refresh_token, "accountId": account_id}

    @classmethod
    async def logout(cls, payload: LogoutDTO):
        key = f"SESSION_BLACKLIST:{payload.userId}:{payload.sessionId}"
        black_list[key] = payload.exp
        session = await SessionsRepo.get_by_condition(
            {Sessions.id.name: payload.sessionId}
        )
        if session:
            await SessionsRepo.delete({Sessions.id.name: payload.sessionId})

        # show black list
        LOGGER.info(f"Black list: {black_list}")
        LOGGER.info(f"User {payload.userId} has been logged out")

    @classmethod
    async def refresh_token(cls, payload: RefreshDTO):
        sessions = await SessionsRepo.get_by_condition(
            {Sessions.id.name: payload.sessionId}
        )
        if len(sessions) == 0:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Invalid session",
            )
        session = sessions[0]
        if session[Sessions.signature.name] != payload.signature:
            # Remove all sessions of the user
            await SessionsRepo.delete({Sessions.user_id.name: payload.userId})
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Invalid signature",
            )

        new_signature = os.urandom(16).hex()
        await SessionsRepo.update(
            record={
                Sessions.id.name: payload.sessionId,
                Sessions.signature.name: new_signature,
            },
            identity_columns=[Sessions.id.name],
            returning=False,
            text_clauses={"__updated_at__": TextSQL(SQLServerConsts.GMT_7_NOW_VARCHAR)},
        )

        access_token_payload = JwtPayload(
            sessionId=session[Sessions.id.name],
            userId=payload.userId,
            role=payload.role,
        )
        refresh_token_payload = RefreshPayload(
            sessionId=session[Sessions.id.name],
            userId=payload.userId,
            role=payload.role,
            signature=new_signature,
        )
        access_token = JWTUtils.create_access_token(payload=access_token_payload)
        refresh_token = JWTUtils.create_refresh_token(payload=refresh_token_payload)  # expires in = session.expies in
        
        return {"accessToken": access_token, "refreshToken": refresh_token}

    @classmethod    
    async def verify_access_token(cls, access_token: str):
        try:
            decoded_payload = JWTUtils.decode_token(token=access_token, secret_key=CommonConsts.AT_SECRET_KEY)

            session_id = decoded_payload.get("sessionId")
            user_id = decoded_payload.get("userId")
            role = decoded_payload.get("role")
            iat = decoded_payload.get("iat")
            exp = decoded_payload.get("exp")

            # Check if the token is blacklisted
            blacklist_key = f"SESSION_BLACKLIST:{user_id}:{session_id}"
            if blacklist_key in black_list:
                sessions = await SessionsRepo.delete({Sessions.user_id.name: user_id})
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.UNAUTHORIZED,
                    errors="Token has been revoked",
                )

            # Validate the session associated with the token
            sessions = await SessionsRepo.get_by_condition({Sessions.id.name: session_id})
            if not sessions:
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.UNAUTHORIZED,
                    errors="Invalid session",
                )

            session = sessions[0]
            if session[Sessions.user_id.name] != user_id:
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.UNAUTHORIZED,
                    errors="Session does not match user",
                )

            return JwtPayload(
                sessionId=session_id,
                userId=user_id,
                role=role,
                iat=iat,
                exp=exp
            )

        except jwt.ExpiredSignatureError:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Token has expired",
            )
        except jwt.InvalidTokenError:
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Invalid token",
            )
        
    @classmethod
    async def verify_refresh_token(cls, refresh_token: str):
        try:
            decoded_payload = JWTUtils.decode_token(token=refresh_token, secret_key=CommonConsts.RT_SECRET_KEY)

            session_id = decoded_payload.get("sessionId")
            user_id = decoded_payload.get("userId")
            role = decoded_payload.get("role")
            iat = decoded_payload.get("iat")
            exp = decoded_payload.get("exp")

            # Validate the session associated with the token
            sessions = await SessionsRepo.get_by_condition({Sessions.id.name: session_id})
            if not sessions:
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.UNAUTHORIZED,
                    errors="Invalid session",
                )

            session = sessions[0]
            if session[Sessions.user_id.name] != user_id:
                raise BaseExceptionResponse(
                    http_code=401,
                    status_code=401,
                    message=MessageConsts.UNAUTHORIZED,
                    errors="Session does not match user",
                )

            # Return the decoded payload as a RefreshPayload object
            return RefreshPayload(
                sessionId=session_id,
                userId=user_id,
                role=role,
                iat=iat,
                exp=exp
            )

        except jwt.ExpiredSignatureError:
            # Token has expired
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Token has expired",
            )
        except jwt.InvalidTokenError:
            # Token is invalid (e.g., tampered or malformed)
            raise BaseExceptionResponse(
                http_code=401,
                status_code=401,
                message=MessageConsts.UNAUTHORIZED,
                errors="Invalid token",
            )
