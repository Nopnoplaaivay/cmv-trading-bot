from typing import Dict
from backend.common.responses import BaseResponse


class PaginationResponse(BaseResponse):
    def __init__(self, http_code, status_code, message, data, page, page_size, total):
        super().__init__(http_code=http_code, status_code=status_code, message=message, data=data)
        self.page = page
        self.page_size = page_size
        self.total = total

    def to_dict(self) -> Dict:
        result = super().to_dict()
        if self.page is not None:
            result["page"] = self.page
        if self.page_size is not None:
            result["pageSize"] = self.page_size
        if self.total is not None:
            result["total"] = self.total
        return result
