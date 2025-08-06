from typing import List, Dict
from backend.utils.logger import LOGGER


class PortfolioReportGenerator:
    @staticmethod
    def generate_telegram_report(
        analysis_result: dict, include_trade_plan: bool = True
    ) -> str:
        """Generate a formatted Telegram report"""
        try:
            account_id = analysis_result.get("account_id", "N/A")
            strategy_type = analysis_result.get("strategy_type", "N/A")
            account_balance = analysis_result.get("account_balance", {})
            current_positions = analysis_result.get("current_positions", [])
            recommendations = analysis_result.get("recommendations", [])
            analysis_date = analysis_result.get("analysis_date", "N/A")

            # Start building report
            report_lines = []
            report_lines.append("📊 <b>BÁO CÁO DANH MỤC ĐẦU TƯ</b>")
            report_lines.append(f"📅 Ngày giao dịch: {analysis_date}")
            report_lines.append(f"💼 Tài khoản: <code>{account_id}</code>")
            report_lines.append(
                f"📈 Chiến lược: {strategy_type.replace('_', ' ').title()}"
            )
            report_lines.append("")

            # Account balance summary
            report_lines.append("💰 <b>TÌNH HÌNH TÀI KHOẢN</b>")
            net_asset = account_balance.get("net_asset_value", 0)
            available_cash = account_balance.get("available_cash", 0)
            cash_ratio = account_balance.get("cash_ratio", 0)

            report_lines.append(f"• Tổng tài sản: <b>💎{net_asset:,.0f} VND</b>")
            report_lines.append(f"• Tiền mặt: <b>💵{available_cash:,.0f} VND</b>")
            report_lines.append(f"• Tỷ lệ tiền mặt: <b>🏦{cash_ratio:.1f}%</b>")
            report_lines.append("")

            # Current portfolio (top 5)
            if current_positions:
                report_lines.append(
                    f"📋 <b>DANH MỤC HIỆN TẠI</b> ({len(current_positions)} cổ phiếu)"
                )
                for i, pos in enumerate(current_positions[:5], 1):
                    symbol = pos.get("symbol", "N/A")
                    weight_pct = pos.get("weight", {}).get("percentage", 0)
                    quantity = pos.get("quantity", 0)
                    market_price = pos.get("market_price", {}).get("amount", 0)

                    report_lines.append(
                        f"{i}. <b>{symbol}</b>: {weight_pct:.1f}% "
                        f"({quantity:,} cổ 💵{market_price:,.0f} VND)"
                    )

                # if len(current_positions) > 5:
                #     report_lines.append(
                #         f"... và {len(current_positions) - 5} cổ phiếu khác"
                #     )
                report_lines.append("")

            # Recommendations
            buy_recs = [r for r in recommendations if r.get("action") == "BUY"]
            sell_recs = [r for r in recommendations if r.get("action") == "SELL"]

            if recommendations and include_trade_plan:
                report_lines.append(
                    f"🎯 <b>KHUYẾN NGHỊ GIAO DỊCH</b> ({len(recommendations)} giao dịch)"
                )

                if buy_recs:
                    report_lines.append(
                        f"📈 <b>MUA VÀO</b> ({len(buy_recs)} cổ phiếu):"
                    )
                    for rec in buy_recs[:]:
                        symbol = rec.get("symbol", "N/A")
                        target_weight = rec.get("target_weight", {}).get(
                            "percentage", 0
                        )
                        amount = rec.get("amount", {}).get("amount", 0)
                        action_price = rec.get("action_price", {}).get("amount", 0)
                        action_quantity = rec.get("action_quantity", 0)
                        priority = rec.get("priority", "N/A")

                        report_lines.append(
                            f"• <b>{symbol}</b>: {target_weight:.1f}% "
                            f"(KL: {action_quantity:,} - Giá {action_price:,.0f} VND) "
                            # f"💵 Tổng giá trị: {amount:,.0f} VND - {priority}"
                        )
                    # if len(buy_recs) > 3:
                    #     report_lines.append(f"... và {len(buy_recs) - 3} cổ phiếu khác")
                    report_lines.append("")

                if sell_recs:
                    report_lines.append(
                        f"📉 <b>BÁN RA</b> ({len(sell_recs)} cổ phiếu):"
                    )
                    for rec in sell_recs[:]:
                        symbol = rec.get("symbol", "N/A")
                        current_weight = rec.get("current_weight", {}).get(
                            "percentage", 0
                        )
                        target_weight = rec.get("target_weight", {}).get(
                            "percentage", 0
                        )
                        action_price = rec.get("action_price", {}).get("amount", 0)
                        action_quantity = rec.get("action_quantity", 0)
                        amount = rec.get("amount", {}).get("amount", 0)
                        priority = rec.get("priority", "N/A")

                        report_lines.append(
                            f"• <b>{symbol}</b>: {current_weight:.1f}% → {target_weight:.1f}% "
                            f"(KL: {action_quantity:,} - Giá: {action_price:,.0f} VND) "
                            # f"💵 Thu về: {amount:,.0f} VND - {priority}"
                        )
                    # if len(sell_recs) > 3:
                    #     report_lines.append(
                    #         f"... và {len(sell_recs) - 3} cổ phiếu khác"
                    #     )
            elif not recommendations:
                report_lines.append(
                    "✅ <b>DANH MỤC ĐÃ CÂN BẰNG</b> - Không cần điều chỉnh"
                )

            return "\n".join(report_lines)

        except Exception as e:
            LOGGER.error(f"Error generating Telegram report: {e}")
            return (
                f"❌ <b>LỖI TẠO BÁO CÁO</b>\nKhông thể tạo báo cáo portfolio: {str(e)}"
            )
