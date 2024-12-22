import json
import os.path as osp
import time
from os import remove
from typing import Dict


class SharedMemoryWrapper(object):
    def __init__(self, folder: str, seed: int):
        self.shared_memory_python_path = osp.join(folder, "shared_memory_python.json").replace(
            "\n", ""
        )
        self.shared_memory_java_path = osp.join(folder, "shared_memory_java.json").replace("\n", "")
        self._max_retries = 5
        self._retry_count = 0

    def read(self) -> Dict[str, str]:
        while not osp.exists(self.shared_memory_java_path):
            time.sleep(0.01)

        with open(self.shared_memory_java_path, "r") as f:
            try:
                return json.load(f)
            except Exception as e:
                while self._retry_count < self._max_retries:
                    self._retry_count += 1
                    return json.load(f)
                raise e
        return {}

    def write(self, message: dict):
        with open(self.shared_memory_python_path, "w") as f:
            json.dump(message, f)

    def close(self):
        if osp.exists(self.shared_memory_java_path):
            remove(self.shared_memory_java_path)
