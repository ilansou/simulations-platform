from typing import Dict

from floodns.external.ipc.shared_memory import SharedMemoryWrapper


class SharedMemoryPool(object):
    _instances: Dict[int, SharedMemoryWrapper] = dict()

    @classmethod
    def len(cls):
        return len(cls._instances)

    @classmethod
    def keys(cls):
        return cls._instances.keys()

    @classmethod
    def values(cls):
        return cls._instances.values()

    @classmethod
    def items(cls):
        return cls._instances.items()

    @classmethod
    def get(cls, seed: int, run_dir: str) -> SharedMemoryWrapper:
        if seed not in cls.keys():
            cls._instances[seed] = SharedMemoryWrapper(folder=run_dir, seed=seed)
        return cls._instances[seed]

    @classmethod
    def close_and_remove(cls, seed: int):
        if seed in cls._instances:
            cls._instances[seed].close()
            del cls._instances[seed]

    @classmethod
    def close_and_remove_all(cls):
        seeds = list(cls.keys())
        for seed in seeds:
            cls.close_and_remove(seed)
