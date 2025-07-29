from backend.common.responses import BaseResponse


class BaseExceptionResponse(BaseResponse, Exception):
    def __init__(self, http_code, status_code, message, errors=None):
        BaseResponse.__init__(self, http_code=http_code, status_code=status_code, message=message, errors=errors)
        Exception.__init__(self, str({"message": message, "errors": errors}))
