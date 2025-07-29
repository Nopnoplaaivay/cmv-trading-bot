import numpy as np


class DataUtils:
    @classmethod
    def round_and_fix_near_zero_column(cls, col, decimal=4, eps=1e-8):
        if np.issubdtype(col.dtype, np.number):
            col = col.round(decimal)
            col = col.mask(col.abs() < eps, 0.0)  # thay giá trị gần 0 thành 0.0
        return col
