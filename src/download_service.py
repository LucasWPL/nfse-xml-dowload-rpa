import re
import shutil
import time
from datetime import date
from pathlib import Path

from selenium import webdriver

from .logger import AppLogger
from .models import DownloadEntry


class DownloadService:
    def __init__(self, download_dir: Path, logger: AppLogger) -> None:
        self.download_dir = download_dir
        self.logger = logger

    def wait_for_download(self, known_files: set[str], timeout: int = 120) -> Path:
        end_time = time.time() + timeout
        while time.time() < end_time:
            current_files = {path.name for path in self.download_dir.iterdir() if path.is_file()}
            new_names = current_files - known_files

            for name in sorted(new_names):
                if name.endswith(".crdownload"):
                    continue

                candidate = self.download_dir / name
                if self.is_temporary_download_file(candidate):
                    continue

                partial = self.download_dir / f"{name}.crdownload"
                if candidate.exists() and not partial.exists():
                    return candidate

            time.sleep(1)

        raise RuntimeError("Timeout aguardando o download finalizar.")

    def ensure_unique_destination(self, destination: Path, download_key: str | None) -> Path:
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        if download_key:
            keyed_destination = destination.with_name(f"{stem}-{download_key[:12]}{suffix}")
            if not keyed_destination.exists():
                return keyed_destination

        index = 1
        while True:
            candidate = destination.with_name(f"{stem}-{index}{suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def is_temporary_download_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        if name.endswith(".crdownload") or name.endswith(".tmp"):
            return True
        if name.startswith(".com.google.chrome") or name.startswith(".org.chromium.chromium"):
            return True
        return False

    def infer_file_type(self, entry: DownloadEntry, file_path: Path | None = None) -> str:
        if file_path and file_path.suffix:
            extension = file_path.suffix.lower().lstrip(".")
            if extension:
                return extension

        haystack = " ".join([entry.href, entry.text]).lower()
        if "pdf" in haystack or "danfse" in haystack:
            return "pdf"
        if "xml" in haystack or "nfse" in haystack:
            return "xml"
        return "outros"

    def slugify_text(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-")
        return slug.lower()

    def find_existing_download(
        self,
        note_date: date | None,
        window_start: date,
        entry: DownloadEntry,
    ) -> Path | None:
        target_date = note_date or window_start
        file_type = self.infer_file_type(entry)
        target_dir = self.download_dir / str(target_date.year) / file_type

        if not target_dir.exists():
            return None

        download_key = (entry.download_key or "").strip()
        if download_key:
            for candidate in target_dir.iterdir():
                if candidate.is_file() and download_key in candidate.name:
                    return candidate

        text_slug = self.slugify_text(entry.text)
        if text_slug:
            for candidate in target_dir.iterdir():
                if candidate.is_file() and text_slug in self.slugify_text(candidate.stem):
                    return candidate

        return None

    def build_destination_filename(
        self,
        file_path: Path,
        entry: DownloadEntry,
        download_key: str | None,
        file_type: str,
    ) -> str:
        if file_path.name and not self.is_temporary_download_file(file_path):
            if file_path.suffix:
                return file_path.name
            return f"{file_path.name}.{file_type}"

        base_name = download_key or re.sub(r"\W+", "-", entry.text.strip()).strip("-")
        if not base_name:
            base_name = f"download-{int(time.time())}"

        return f"{base_name}.{file_type}"

    def move_downloaded_file(
        self,
        file_path: Path,
        note_date: date | None,
        window_start: date,
        download_key: str | None,
        entry: DownloadEntry,
    ) -> Path:
        target_date = note_date or window_start
        file_type = self.infer_file_type(entry, file_path)
        target_dir = self.download_dir / str(target_date.year) / file_type
        target_dir.mkdir(parents=True, exist_ok=True)

        target_name = self.build_destination_filename(file_path, entry, download_key, file_type)
        destination = self.ensure_unique_destination(target_dir / target_name, download_key)
        shutil.move(str(file_path), destination)
        return destination

    def download_entry(
        self,
        driver: webdriver.Chrome,
        entry: DownloadEntry,
        window_start: date,
    ) -> tuple[Path, bool]:
        existing_file = self.find_existing_download(
            note_date=entry.note_date,
            window_start=window_start,
            entry=entry,
        )
        if existing_file:
            return existing_file, True

        before = {path.name for path in self.download_dir.iterdir() if path.is_file()}
        driver.get(entry.href)
        downloaded_file = self.wait_for_download(before)

        saved_path = self.move_downloaded_file(
            file_path=downloaded_file,
            note_date=entry.note_date,
            window_start=window_start,
            download_key=entry.download_key,
            entry=entry,
        )
        return saved_path, False
