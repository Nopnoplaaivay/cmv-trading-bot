import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, Any


from backend.common.consts import MessageConsts
from backend.common.responses.exceptions import BaseExceptionResponse
from backend.modules.portfolio.services.portfolio_balance_service import BalanceService
from backend.modules.portfolio.services.portfolio_deals_service import DealsService
from backend.modules.portfolio.services import StocksUniverseService
from backend.modules.portfolio.services.portfolio_service import PortfoliosService
from backend.modules.portfolio.services.portfolio_notification_service import PortfolioNotificationService
from backend.modules.notifications.service import notify_error, notify_success
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


LOGGER_PREFIX = "[Pipeline]"


class DailyDataPipelineService:
    """Pipeline to update all portfolio data daily at 7PM"""

    PIPELINE_TIME = time(0, 0)  # 7:00 PM
    TEST_INTERVAL_MINUTES = 5  # Run every 5 minutes in test mode

    @classmethod
    async def run_pipeline(cls) -> Dict[str, Any]:
        """Run the complete daily data update pipeline"""
        start_time = datetime.now()
        LOGGER.info(f"{LOGGER_PREFIX} Starting daily data pipeline")

        pipeline_results = {
            "start_time": start_time.isoformat(),
            "steps": {},
            "success": True,
            "total_duration": 0,
        }

        try:
            # Step 1: Update Balance Data
            LOGGER.info(f"{LOGGER_PREFIX} Phase 1: Updating balance data...")
            balance_start = datetime.now()
            balance_result = await BalanceService.update_newest_balances_daily()
            balance_duration = (datetime.now() - balance_start).total_seconds()

            pipeline_results["steps"]["balance_update"] = {
                # "result": balance_result,
                "duration_seconds": balance_duration,
                "success": balance_result.get("success", False),
            }

            if not balance_result.get("success", False):
                pipeline_results["success"] = False
                LOGGER.error("Balance update failed, continuing with pipeline...")

            # Step 2: Update Deals Data
            LOGGER.info(f"{LOGGER_PREFIX} Phase 2: Updating deals data...")
            deals_start = datetime.now()
            deals_result = await DealsService.update_newest_deals_daily()
            deals_duration = (datetime.now() - deals_start).total_seconds()

            pipeline_results["steps"]["deals_update"] = {
                # "result": deals_result,
                "duration_seconds": deals_duration,
                "success": deals_result.get("success", False),
            }

            if not deals_result.get("success", False):
                pipeline_results["success"] = False
                LOGGER.error(f"{LOGGER_PREFIX} Deals update failed, continuing with pipeline...")

            # Step 3: Update Universe Top Monthly
            LOGGER.info(f"{LOGGER_PREFIX} Phase 3: Updating universe top monthly...")
            universe_start = datetime.now()
            universe_result = (
                await StocksUniverseService.update_newest_data_all_monthly()
            )
            universe_duration = (datetime.now() - universe_start).total_seconds()

            pipeline_results["steps"]["universe_update"] = {
                # "result": universe_result,
                "duration_seconds": universe_duration,
                "success": universe_result,
            }

            if not universe_result:
                pipeline_results["success"] = False
                LOGGER.error(f"{LOGGER_PREFIX} Universe update failed, continuing with pipeline...")

            # Step 4: Update Optimized Weights
            LOGGER.info(f"{LOGGER_PREFIX} Phase 4: Updating qOptimized weights...")
            weights_start = datetime.now()
            weights_result = await PortfoliosService.update_newest_data_all_daily()
            weights_duration = (datetime.now() - weights_start).total_seconds()

            pipeline_results["steps"]["weights_update"] = {
                # "result": weights_result,
                "duration_seconds": weights_duration,
                "success": weights_result,
            }

            if not weights_result:
                pipeline_results["success"] = False
                LOGGER.error(f"{LOGGER_PREFIX} Weights update failed, continuing with pipeline...")

            # Step 5: Send Portfolio Notifications
            LOGGER.info(f"{LOGGER_PREFIX} Phase 5: Sending portfolio notifications...")
            notification_start = datetime.now()
            notification_result = (
                await PortfolioNotificationService.send_daily_system_portfolio()
            )
            notification_duration = (
                datetime.now() - notification_start
            ).total_seconds()

            pipeline_results["steps"]["notification_send"] = {
                # "result": notification_result,
                "duration_seconds": notification_duration,
                "success": notification_result,
            }

            if not notification_result:
                pipeline_results["success"] = False
                LOGGER.error(f"{LOGGER_PREFIX} Notification sending failed")

            # Calculate total duration
            end_time = datetime.now()
            pipeline_results["end_time"] = end_time.isoformat()
            pipeline_results["total_duration"] = (end_time - start_time).total_seconds()

            # Send summary notification
            await cls.send_pipeline_summary(pipeline_results)

            LOGGER.info(
                f"{LOGGER_PREFIX} Daily pipeline completed in {pipeline_results['total_duration']:.2f} seconds"
            )
            return pipeline_results

        except Exception as e:
            LOGGER.error(f"{LOGGER_PREFIX} Fatal error in daily pipeline: {e}")
            await notify_error(
                "DAILY PIPELINE FATAL ERROR",
                f"Daily data pipeline failed with fatal error: {str(e)}",
            )

            pipeline_results["success"] = False
            pipeline_results["error"] = str(e)
            pipeline_results["total_duration"] = (
                datetime.now() - start_time
            ).total_seconds()

            return pipeline_results

    @classmethod
    async def send_pipeline_summary(cls, results: Dict[str, Any]) -> None:
        """Send pipeline summary notification"""
        try:
            success = results.get("success", False)
            total_duration = results.get("total_duration", 0)
            steps = results.get("steps", {})

            # Count successful steps
            successful_steps = sum(
                1 for step in steps.values() if step.get("success", False)
            )
            total_steps = len(steps)

            # Create summary message
            status_emoji = "✅" if success else "❌"
            title = f"{status_emoji} Daily Pipeline Summary"

            message_lines = [
                f"<b>{title}</b>",
                f"",
                f"📊 <b>Overall Status:</b> {'SUCCESS' if success else 'FAILED'}",
                f"⏱️ <b>Total Duration:</b> {total_duration:.2f} seconds",
                f"✅ <b>Successful Steps:</b> {successful_steps}/{total_steps}",
                f"",
            ]

            # Add step details
            for step_name, step_data in steps.items():
                step_success = step_data.get("success", False)
                step_duration = step_data.get("duration_seconds", 0)
                step_emoji = "✅" if step_success else "❌"

                step_title = step_name.replace("_", " ").title()
                message_lines.append(
                    f"{step_emoji} <b>{step_title}:</b> {step_duration:.2f}s"
                )

                # Add specific results for each step
                result = step_data.get("result", {})
                if step_name == "balance_update" and result:
                    updated = result.get("updated_accounts", 0)
                    failed = result.get("failed_accounts", 0)
                    message_lines.append(
                        f"   💰 Updated: {updated} accounts, Failed: {failed}"
                    )

                elif step_name == "deals_update" and result:
                    updated = result.get("updated_accounts", 0)
                    total_deals = result.get("total_deals", 0)
                    message_lines.append(
                        f"   📈 Updated: {updated} accounts, Total deals: {total_deals}"
                    )

                elif step_name == "universe_update" and result:
                    updated = result.get("updated_symbols", 0)
                    message_lines.append(f"   🌍 Updated symbols: {updated}")

                elif step_name == "weights_update" and result:
                    updated = result.get("updated_weights", 0)
                    message_lines.append(f"   ⚖️ Updated weights: {updated}")

                elif step_name == "notification_send" and result:
                    sent = result.get("sent_notifications", 0)
                    message_lines.append(f"   📱 Notifications sent: {sent}")

            message_lines.append("")
            message_lines.append(
                f"🕰️ <b>Pipeline Time:</b> {results.get('start_time', '')}"
            )

            message = "\n".join(message_lines)

            if success:
                await notify_success("Daily Pipeline Completed", message)
            else:
                await notify_error("Daily Pipeline Issues", message)

        except Exception as e:
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

    @classmethod
    async def schedule_daily_run(cls) -> None:
        """Schedule the pipeline to run daily at 7PM"""
        LOGGER.info(f"{LOGGER_PREFIX} Starting daily pipeline scheduler...")

        LOGGER.info(f"{LOGGER_PREFIX} PRODUCTION MODE: Pipeline will run daily at {cls.PIPELINE_TIME}")

        while True:
            try:
                current_time = TimeUtils.get_current_vn_time()

                # Production mode: run daily at specified time
                target_time = current_time.replace(
                    hour=cls.PIPELINE_TIME.hour,
                    minute=cls.PIPELINE_TIME.minute,
                    second=0,
                    microsecond=0,
                )

                # If target time has passed today, schedule for tomorrow
                if current_time >= target_time:
                    target_time = target_time + timedelta(days=1)

                # Calculate seconds until next run
                time_until_run = (target_time - current_time).total_seconds()

                LOGGER.info(
                    f"{LOGGER_PREFIX} Next pipeline run scheduled for: {target_time.isoformat()}"
                )
                LOGGER.info(f"{LOGGER_PREFIX} Waiting {time_until_run:.0f} seconds...")

                # Break long waits into smaller chunks with health checks
                if time_until_run > 3600:  # If waiting more than 1 hour
                    await cls.wait_with_health_checks(time_until_run)
                else:
                    await asyncio.sleep(time_until_run)

                # Run the pipeline
                LOGGER.info(f"{LOGGER_PREFIX} Executing scheduled daily pipeline...")
                await cls.run_pipeline()

                # Sleep for a minute to avoid running multiple times
                await asyncio.sleep(60)

            except Exception as e:
                LOGGER.error(f"Error in pipeline scheduler: {e}")
                await notify_error(
                    "PIPELINE SCHEDULER ERROR",
                    f"Daily pipeline scheduler encountered an error: {str(e)}",
                )
                # Wait 5 minutes before retrying
                await asyncio.sleep(300)

    @classmethod
    async def wait_with_health_checks(cls, total_seconds: float) -> None:
        """Wait for a long duration with periodic health checks"""
        check_interval = 3600  # Check every hour
        elapsed = 0

        while elapsed < total_seconds:
            LOGGER.info(f"{LOGGER_PREFIX} Running health checks every {check_interval} seconds...")
            remaining = total_seconds - elapsed
            sleep_time = min(check_interval, remaining)

            elapsed += sleep_time

            # Health check every hour
            if elapsed % check_interval == 0 and remaining > 0:
                hours_remaining = remaining / 3600
                LOGGER.info(f"{LOGGER_PREFIX} Pipeline scheduler health check: {hours_remaining:.1f} hours remaining")

                if hours_remaining <= 2:  # Only notify when close to execution time
                    await notify_success(
                        "Pipeline Scheduler Health Check",
                        f"Pipeline will run in {hours_remaining:.1f} hours",
                    )

            await asyncio.sleep(sleep_time)

    @classmethod
    async def run_manual(cls) -> Dict[str, Any]:
        """Run the pipeline manually (for testing or emergency updates)"""
        LOGGER.info(f"{LOGGER_PREFIX} Running daily pipeline manually...")
        return await cls.run_pipeline()
