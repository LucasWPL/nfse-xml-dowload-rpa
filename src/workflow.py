from datetime import date
from threading import Event

from .cancellation import ensure_not_cancelled
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
    stop_event: Event | None = None,
) -> int:
    ensure_not_cancelled(stop_event)
    logger.info(
        f"Consultando período {start_date.strftime(PORTAL_DATE_FORMAT)} "
        f"até {end_date.strftime(PORTAL_DATE_FORMAT)}"
    )

    portal.navigate_to_notas_emitidas()
    portal.apply_date_filter(start_date, end_date)
    entries = portal.collect_download_entries()

    if not entries:
        logger.info("Nenhum download encontrado neste período.")
        return 0

    logger.info(f"{len(entries)} arquivo(s) encontrado(s) neste período.")
    downloaded_count = 0
    skipped_count = 0

    for entry in entries:
        ensure_not_cancelled(stop_event)
        saved_path, skipped = downloads.download_entry(
            portal.driver,
            entry,
            start_date,
            stop_event=stop_event,
        )
        if skipped:
            skipped_count += 1
            logger.info(f"Arquivo já existe, pulando: {saved_path}")
            continue

        downloaded_count += 1
        logger.info(f"Arquivo salvo em: {saved_path}")

    if skipped_count:
        logger.info(f"{skipped_count} arquivo(s) já existiam neste período.")

    return downloaded_count
