from dataclasses import dataclass
from typing import List, Optional

from floodns.external.schemas.models import Model


@dataclass(frozen=True)
class Pipeline:
    hosts: list
    flow_size: int
    compute_time: int


@dataclass(frozen=True)
class DataParallel:
    nics: list
    flow_size: int


@dataclass(frozen=True)
class Job:
    job_id: int
    model: Optional[Model]
    pipelines: List[Pipeline]
    data_parallels: List[DataParallel]
    start_time: int
    compute_time: int
    mini_batch_size: int
