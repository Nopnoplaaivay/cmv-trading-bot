import json
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from backend.api import api_router
from backend.common.consts import MessageConsts, CommonConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.utils.logger import LOGGER


app = FastAPI(
    title="PAPER TRADING APP",
    description="Welcome to API documentation",
    docs_url="/docs" if CommonConsts.DEBUG else None,
    redoc_url="/docs" if CommonConsts.DEBUG else None,
)
app_cors = CORSMiddleware(
    app, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


async def pydantic_exception_handler(request: Request, exception: RequestValidationError):
    errors = {}
    for error in exception.errors():
        field = []
        _errors = errors
        if len(error["loc"]) == 1:
            if "ctx" in error and "discriminator_key" in error["ctx"]:
                field = error["ctx"]["discriminator_key"]
                if field not in _errors:
                    _errors[field] = []
                _errors[field].append(error["msg"])
                continue
        for i in range(1, len(error["loc"])):
            field = error["loc"][i]
            if field not in _errors:
                _errors[field] = [] if i == len(error["loc"]) - 1 else {}
            _errors = _errors[field]
        _errors.append(error["msg"])
    exception = BaseExceptionResponse(
        http_code=400,
        status_code=400,
        message=MessageConsts.BAD_REQUEST,
        errors=errors,
    )
    error_response = exception.to_dict()
    LOGGER.error(json.dumps(error_response))
    return JSONResponse(
        status_code=exception.http_code,
        content=error_response,
    )


async def response_exception_handler(request: Request, exception):
    if isinstance(exception, BaseExceptionResponse):
        error_response = exception.to_dict()
    else:
        errors = (
            None if not CommonConsts.DEBUG else {"key": MessageConsts.INTERNAL_SERVER_ERROR, "message": str(exception)}
        )
        exception = BaseExceptionResponse(
            http_code=500,
            status_code=500,
            message=MessageConsts.INTERNAL_SERVER_ERROR,
            errors=errors,
        )
        error_response = exception.to_dict()
    LOGGER.error(json.dumps(error_response))
    return JSONResponse(
        status_code=exception.http_code,
        content=error_response,
    )


@app.exception_handler(RequestValidationError)
async def exception_handler(request, exception):
    return await pydantic_exception_handler(request=request, exception=exception)


@app.exception_handler(Exception)
async def exception_handler(request, exception):
    return await response_exception_handler(request=request, exception=exception)


app.include_router(prefix="/api/v1", router=api_router)