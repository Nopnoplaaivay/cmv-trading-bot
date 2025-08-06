from typing import Dict, Any
from backend.modules.portfolio.entities.balances import Balances


class BalanceUtils:
    @classmethod
    def extract_balance_data(cls, raw_data: Dict, date: str) -> Dict:
        field_mapping = {
            Balances.date.name: date,
            Balances.brokerAccountId.name: raw_data.get("investorAccountId"),
            Balances.totalCash.name: raw_data.get("totalCash"),
            Balances.availableCash.name: raw_data.get("availableCash"),
            Balances.termDeposit.name: raw_data.get("termDeposit"),
            Balances.depositInterest.name: raw_data.get("depositInterest"),
            Balances.stockValue.name: raw_data.get("stockValue"),
            Balances.marginableAmount.name: raw_data.get("marginableAmount"),
            Balances.nonMarginableAmount.name: raw_data.get("nonMarginableAmount"),
            Balances.totalDebt.name: raw_data.get("totalDebt"),
            Balances.netAssetValue.name: raw_data.get("netAssetValue"),
            Balances.receivingAmount.name: raw_data.get("receivingAmount"),
            Balances.secureAmount.name: raw_data.get("secureAmount"),
            Balances.depositFeeAmount.name: raw_data.get("depositFeeAmount"),
            Balances.maxLoanLimit.name: raw_data.get("maxLoanLimit"),
            Balances.withdrawableCash.name: raw_data.get("withdrawableCash"),
            Balances.collateralValue.name: raw_data.get("collateralValue"),
            Balances.orderSecured.name: raw_data.get("orderSecured"),
            Balances.purchasingPower.name: raw_data.get("purchasingPower"),
            Balances.cashDividendReceiving.name: raw_data.get("cashDividendReceiving"),
            Balances.marginDebt.name: raw_data.get("marginDebt"),
            Balances.marginRate.name: raw_data.get("marginRate"),
            Balances.ppWithdraw.name: raw_data.get("ppWithdraw"),
            Balances.blockMoney.name: raw_data.get("blockMoney"),
            Balances.totalRemainDebt.name: raw_data.get("totalRemainDebt"),
            Balances.totalUnrealizedDebt.name: raw_data.get("totalUnrealizedDebt"),
            Balances.blockedAmount.name: raw_data.get("blockedAmount"),
            Balances.advancedAmount.name: raw_data.get("advancedAmount"),
            Balances.advanceWithdrawnAmount.name: raw_data.get(
                "advanceWithdrawnAmount"
            ),
        }

        return {k: v for k, v in field_mapping.items() if v is not None}