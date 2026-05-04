import time

from src.browser import setup_driver
from src.config import iter_period_windows, load_settings, resolve_period
from src.download_service import DownloadService
from src.logger import AppLogger
from src.portal_client import PortalClient
from src.workflow import process_window


def main() -> None:
    settings = load_settings()
    logger = AppLogger(settings.debug)
    driver, download_dir = setup_driver(settings)
    portal = PortalClient(driver, settings, logger)
    downloads = DownloadService(download_dir, logger)

    try:
        start_date, end_date = resolve_period(settings)
        total_downloads = 0

        portal.login()

        for window_start, window_end in iter_period_windows(
            start_date=start_date,
            end_date=end_date,
            max_period_days=settings.max_period_days,
        ):
            total_downloads += process_window(
                portal=portal,
                downloads=downloads,
                logger=logger,
                start_date=window_start,
                end_date=window_end,
            )

        logger.info(f"Processo finalizado com {total_downloads} arquivo(s) baixado(s).")
    except Exception as exc:
        logger.info(f"Erro no processo geral: {exc}")
    finally:
        time.sleep(2)
        driver.quit()


if __name__ == "__main__":
    main()
