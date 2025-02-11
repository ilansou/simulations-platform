from enum import Enum


class DistributedTraining(str, Enum):
    DATA_PARALLEL = "data_parallel"
    TENSOR_PARALLEL = "tensor_parallel"
    PIPELINE_PARALLEL = "pipeline_parallel"
    HYBRID_PARALLEL = "hybrid_parallel"
