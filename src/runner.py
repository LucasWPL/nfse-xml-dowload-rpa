from threading import Event

from .browser import setup_driver
from .cancellation import ensure_not_cancelled
from .config import Settings, iter_period_windows, resolve_period
from .download_service import DownloadService
from .logger import AppLogger
from .portal_client import PortalClient
from .workflow import process_window


def run_job(settings: Settings, logger: AppLogger, stop_event: Event | None = None) -> int:
    driver, download_dir = setup_driver(settings)
    portal = PortalClient(driver, settings, logger)
    downloads = DownloadService(download_dir, logger)

    try:
        ensure_not_cancelled(stop_event)
        start_date, end_date = resolve_period(settings)
        total_downloads = 0

        portal.login()

        for window_start, window_end in iter_period_windows(
            start_date=start_date,
            end_date=end_date,
            max_period_days=settings.max_period_days,
        ):
            ensure_not_cancelled(stop_event)
            total_downloads += process_window(
                portal=portal,
                downloads=downloads,
                logger=logger,
                start_date=window_start,
                end_date=window_end,
                stop_event=stop_event,
            )

        logger.info(f"Processo finalizado com {total_downloads} arquivo(s) baixado(s).")
        return total_downloads
    finally:
        driver.quit()
