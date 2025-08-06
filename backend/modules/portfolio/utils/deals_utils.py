from typing import Dict
from backend.modules.portfolio.entities.deals import Deals


class DealsUtils:
    @classmethod
    def extract_deal_data(cls, raw_data: Dict, date: str) -> Dict:
        field_mapping = {
            Deals.date.name: date,
            Deals.brokerAccountId.name: raw_data.get("accountNo"),
            Deals.dealId.name: raw_data.get("id"),
            Deals.symbol.name: raw_data.get("symbol"),
            Deals.status.name: raw_data.get("status"),
            Deals.side.name: raw_data.get("side"),
            Deals.secure.name: raw_data.get("secure"),
            Deals.accumulateQuantity.name: raw_data.get("accumulateQuantity"),
            Deals.tradeQuantity.name: raw_data.get("tradeQuantity"),
            Deals.closedQuantity.name: raw_data.get("closedQuantity"),
            Deals.t0ReceivingQuantity.name: raw_data.get("t0ReceivingQuantity"),
            Deals.t1ReceivingQuantity.name: raw_data.get("t1ReceivingQuantity"),
            Deals.t2ReceivingQuantity.name: raw_data.get("t2ReceivingQuantity"),
            Deals.costPrice.name: raw_data.get("costPrice"),
            Deals.averageCostPrice.name: raw_data.get("averageCostPrice"),
            Deals.marketPrice.name: raw_data.get("marketPrice"),
            Deals.realizedProfit.name: raw_data.get("realizedProfit"),
            Deals.unrealizedProfit.name: raw_data.get("unrealizedProfit"),
            Deals.breakEvenPrice.name: raw_data.get("breakEvenPrice"),
            Deals.dividendReceivingQuantity.name: raw_data.get("dividendReceivingQuantity"),
            Deals.dividendQuantity.name: raw_data.get("dividendQuantity"),
            Deals.cashReceiving.name: raw_data.get("cashReceiving"),
            Deals.rightReceivingCash.name: raw_data.get("rightReceivingCash"),
            Deals.t0ReceivingCash.name: raw_data.get("t0ReceivingCash"),
            Deals.t1ReceivingCash.name: raw_data.get("t1ReceivingCash"),
            Deals.t2ReceivingCash.name: raw_data.get("t2ReceivingCash"),
            Deals.createdDate.name: raw_data.get("createdDate"),
            Deals.modifiedDate.name: raw_data.get("modifiedDate"),
        }

        return {k: v for k, v in field_mapping.items() if v is not None}