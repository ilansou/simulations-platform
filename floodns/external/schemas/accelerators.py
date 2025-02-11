from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Accelerator:
    machine: str  # machine name
    memory: int  # memory in GB
    flops: float  # TeraFLOPS


class Accelerators(Enum):
    TPU_V4 = Accelerator(machine="TPU-v4", memory=32, flops=260.0)
    A100 = Accelerator(machine="A100", memory=80, flops=312.0)
    H100 = Accelerator(machine="H100", memory=80, flops=1979.0)
    AWS_TRAINIUM_V1 = Accelerator(machine="AWS-Trainium-v1", memory=512, flops=3400.0)
    AWS_TRAINIUM_V2 = Accelerator(machine="AWS-Trainium-v2", memory=512, flops=3400.0)
    ASCEND_910 = Accelerator(machine="Ascend-910", memory=32, flops=320.0)


accelerators = [a.name for a in Accelerators]
