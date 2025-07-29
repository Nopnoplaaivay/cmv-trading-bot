import pandas as pd
import numpy as np

from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.base_daily import BaseDailyService
from backend.modules.portfolio.repositories import OptimizedWeightsRepo
from backend.common.consts import MessageConsts


class OptimizedWeightsService(BaseDailyService):
    repo = OptimizedWeightsRepo

    @classmethod
    def update_data(cls, from_date) -> pd.DataFrame:
        pass
