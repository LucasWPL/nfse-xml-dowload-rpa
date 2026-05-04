import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE_VALUES = dotenv_values()

DATE_FORMAT = "%Y-%m-%d"
PORTAL_DATE_FORMAT = "%d/%m/%Y"


def get_env(name: str, legacy_name: str | None = None, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    file_value = ENV_FILE_VALUES.get(name)
    if file_value:
        return str(file_value)
    if legacy_name:
        legacy_file_value = ENV_FILE_VALUES.get(legacy_name)
        if legacy_file_value:
            return str(legacy_file_value)
        legacy_value = os.getenv(legacy_name)
        if legacy_value:
            return legacy_value
    return default


def get_raw_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    file_value = ENV_FILE_VALUES.get(name)
    if file_value:
        return str(file_value)
    return default


def env_bool(name: str, default: bool = False) -> bool:
    value = get_raw_env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


@dataclass(frozen=True)
class Settings:
    nfse_username: str
    nfse_password: str
    download_path: Path
    start_date_input: str
    end_date_input: str
    months_back: int
    max_period_days: int
    wait_timeout: int
    headless: bool
    debug: bool


def load_settings() -> Settings:
    return Settings(
        nfse_username=get_env("NFSE_USERNAME", "USERNAME", "") or "",
        nfse_password=get_env("NFSE_PASSWORD", "PASSWORD", "") or "",
        download_path=Path(get_raw_env("DOWNLOAD_PATH", "./downloads") or "./downloads").expanduser().resolve(),
        start_date_input=(get_raw_env("START_DATE", "") or "").strip(),
        end_date_input=(get_raw_env("END_DATE", "") or "").strip(),
        months_back=int(get_raw_env("MONTHS_BACK", "12") or "12"),
        max_period_days=int(get_raw_env("MAX_PERIOD_DAYS", "30") or "30"),
        wait_timeout=int(get_raw_env("WAIT_TIMEOUT", "20") or "20"),
        headless=env_bool("HEADLESS", False),
        debug=env_bool("DEBUG", False),
    )


def parse_iso_date(raw_value: str, field_name: str) -> date:
    try:
        return datetime.strptime(raw_value, DATE_FORMAT).date()
    except ValueError as exc:
        raise RuntimeError(
            f"{field_name} invalida. Use o formato YYYY-MM-DD. Valor recebido: {raw_value}"
        ) from exc


def resolve_period(settings: Settings) -> tuple[date, date]:
    end_date = parse_iso_date(settings.end_date_input, "END_DATE") if settings.end_date_input else date.today()

    if settings.start_date_input:
        start_date = parse_iso_date(settings.start_date_input, "START_DATE")
    else:
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        for _ in range(max(settings.months_back - 1, 0)):
            start_date = (start_date - timedelta(days=1)).replace(day=1)

    if start_date > end_date:
        raise RuntimeError("START_DATE nao pode ser maior que END_DATE.")

    if settings.max_period_days < 1 or settings.max_period_days > 30:
        raise RuntimeError("MAX_PERIOD_DAYS deve estar entre 1 e 30.")

    return start_date, end_date


def iter_period_windows(start_date: date, end_date: date, max_period_days: int):
    current = start_date
    while current <= end_date:
        month_end = (
            (current.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        )
        chunk_end = min(current + timedelta(days=max_period_days - 1), month_end, end_date)
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)
