from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DownloadEntry:
    href: str
    text: str
    note_date: date | None
    download_key: str | None
