import os
import json
from abc import ABC
from typing import Optional

from job_cd.core.interfaces import CacheStrategy


class LocalCache(CacheStrategy):
    """
    Stores key-value pairs in a local JSON file.
    """
    def __init__(self, filename: str = 'contacts.json') -> None:
        self.filepath = os.path.join(os.getcwd(), ".cache", filename)

        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump({}, f)

    def get(self, key: str) -> Optional[dict]:
        with open(self.filepath, 'r') as f:
            data = json.load(f)
        return data.get(key)

    def set(self, key: str, value: dict) -> None:
        with open(self.filepath, 'r') as f:
            data = json.load(f)

        data[key] = value
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=4)