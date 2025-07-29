from typing import List, Dict, Union, Any


class BaseResponse:
    def __init__(
        self,
        http_code: int,
        status_code: int,
        message: str,
        data: Union[List, Dict, Any] = None,
        errors: Dict = None,
    ):
        self.http_code = http_code
        self.status_code = status_code
        self.message = message
        self.data = data
        self.errors = errors

    def to_dict(self) -> Dict:
        result = {"statusCode": self.status_code, "message": self.message}
        if self.data:
            result["data"] = self.data
        if self.errors:
            result["errors"] = self.errors
        return result
