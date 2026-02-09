"""Background thread to check for updates via GitHub Releases API."""

import json
import urllib.request
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

GITHUB_API_URL = (
    "https://api.github.com/repos/zzjoey/DownXV/releases/latest"
)


@dataclass
class UpdateResult:
    latest_version: str
    download_url: str
    is_newer: bool


def _compare_versions(current: str, latest: str) -> bool:
    """Return True if *latest* is strictly newer than *current*."""

    def _parts(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.lstrip("vV").split("."))

    try:
        return _parts(latest) > _parts(current)
    except (ValueError, AttributeError):
        return False


class UpdateChecker(QThread):
    """Fetches the latest GitHub release and compares versions."""

    result = Signal(object)  # UpdateResult
    error = Signal(str)

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self._current = current_version

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            tag = data.get("tag_name", "")
            html_url = data.get("html_url", "")

            self.result.emit(
                UpdateResult(
                    latest_version=tag.lstrip("vV"),
                    download_url=html_url,
                    is_newer=_compare_versions(self._current, tag),
                )
            )
        except Exception as e:
            self.error.emit(str(e))
