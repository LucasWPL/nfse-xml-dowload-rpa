from datetime import date

from .config import PORTAL_DATE_FORMAT
from .download_service import DownloadService
from .logger import AppLogger
from .portal_client import PortalClient


def process_window(
    portal: PortalClient,
    downloads: DownloadService,
    logger: AppLogger,
    start_date: date,
    end_date: date,
) -> int:
    logger.info(
        f"Consultando periodo {start_date.strftime(PORTAL_DATE_FORMAT)} "
        f"ate {end_date.strftime(PORTAL_DATE_FORMAT)}"
    )

    portal.navigate_to_notas_emitidas()
    portal.apply_date_filter(start_date, end_date)
    entries = portal.collect_download_entries()

    if not entries:
        logger.info("Nenhum download encontrado neste periodo.")
        return 0

    logger.info(f"{len(entries)} arquivo(s) encontrado(s) neste periodo.")
    downloaded_count = 0
    skipped_count = 0

    for entry in entries:
        saved_path, skipped = downloads.download_entry(portal.driver, entry, start_date)
        if skipped:
            skipped_count += 1
            logger.info(f"Arquivo ja existe, pulando: {saved_path}")
            continue

        downloaded_count += 1
        logger.info(f"Arquivo salvo em: {saved_path}")

    if skipped_count:
        logger.info(f"{skipped_count} arquivo(s) ja existiam neste periodo.")

    return downloaded_count
