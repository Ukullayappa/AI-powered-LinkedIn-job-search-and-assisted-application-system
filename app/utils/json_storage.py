import json
import os
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class JsonStorage:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.lock = threading.RLock()

    def get_path(self, filename: str) -> Path:
        safe_filename = Path(filename).name

        if not safe_filename.endswith(".json"):
            safe_filename = f"{safe_filename}.json"

        return (
            self.settings.data_directory
            / safe_filename
        )

    def read(
        self,
        filename: str,
        default: Any,
    ) -> Any:
        path = self.get_path(filename)

        with self.lock:
            if not path.exists():
                self.write(filename, default)
                return deepcopy(default)

            try:
                content = path.read_text(
                    encoding="utf-8"
                )

                return json.loads(content)

            except (
                json.JSONDecodeError,
                OSError,
            ):
                self.write(filename, default)
                return deepcopy(default)

    def write(
        self,
        filename: str,
        data: Any,
    ) -> None:
        path = self.get_path(filename)

        temporary_path = path.with_suffix(
            path.suffix + ".tmp"
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_content = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        with self.lock:
            temporary_path.write_text(
                json_content,
                encoding="utf-8",
            )

            os.replace(
                temporary_path,
                path,
            )


storage = JsonStorage()