from src.config import load_settings
from src.logger import AppLogger
from src.runner import run_job


def main() -> None:
    settings = load_settings()
    logger = AppLogger(settings.debug)

    try:
        run_job(settings, logger)
    except Exception as exc:
        logger.info(f"Erro no processo geral: {exc}")


if __name__ == "__main__":
    main()
