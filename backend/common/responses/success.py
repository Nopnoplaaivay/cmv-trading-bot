from backend.common.responses import BaseResponse


class SuccessResponse(BaseResponse):
    def __init__(self, http_code, status_code, message, data=None):
        super().__init__(http_code=http_code, status_code=status_code, message=message, data=data)
