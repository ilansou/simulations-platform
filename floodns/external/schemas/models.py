import math
from dataclasses import dataclass
from enum import Enum

from floodns.external.schemas.accelerators import Accelerator
from floodns.external.utils.units import BILLION, FLOAT32, TRILLION

NUM_ACCELERATORS_PER_HOST = 8
MICRO_BATCH_SIZE = 16

"""
Model Papers:
    - GPT-3: https://arxiv.org/pdf/2005.14165.pdf
    - OPT-175B: https://arxiv.org/pdf/2205.01068.pdf
    - PaLM: https://arxiv.org/pdf/2204.02311.pdf
    - LLaMA2-70B: https://arxiv.org/pdf/2307.09288.pdf
    - Gopher: https://arxiv.org/pdf/2112.11446.pdf
    - MT-NLG: https://arxiv.org/pdf/2201.11990.pdf
    - PanGu-Sigma: https://arxiv.org/pdf/2303.10845.pdf
"""


@dataclass
class Model:
    name: str  # model name
    size: int  # model size (parameters) in billions
    num_layers: int
    global_batch_size: int  # number of tokens
    context_window: int
    num_tokens: float  # number of tokens (for language models)
    hidden_dim: int
    tensor_dim: int  # tensor parallelism dimension (GPU)
    pipeline_depth: int  # pipeline parallelism depth (GPU)

    def get_compute_time(self, accelerator: Accelerator) -> int:
        """
        Compute time in nanoseconds
        :param accelerator: accelerator to run the model on
        :return:  compute time in nanoseconds
        """
        return math.ceil(1e6 * self.flops / accelerator.flops)

    @property
    def full_copy(self) -> int:
        """
        Number of GPUs required for a full copy of the model
        :return: number of GPUs
        """
        return self.tensor_dim * self.pipeline_depth

    @property
    def weights(self) -> int:
        """
        Model weights: 4 bytes per parameter (float32)
        :return: model weights size (bytes)
        """
        return FLOAT32 * self.size

    @property
    def gradients(self) -> int:
        """
        Gradients: 4 bytes per parameter (float32)
        :return: gradients size (bytes)
        """
        return FLOAT32 * self.size

    @property
    def optimizer_state(self) -> int:
        """
        Optimizer state: 12 bytes per parameter (3 * float32)
        :return: optimizer state size (bytes)
        """
        return 3 * FLOAT32 * self.size

    @property
    def model_size(self) -> int:
        """
        Model weights: 4 bytes per parameter (float32)
        Gradients: 4 bytes per parameter (float32)
        Optimizer state: 12 bytes per parameter (3 * float32)
        :return: model size (parameters), which is the sum of the above
        """
        return self.weights + self.gradients + self.optimizer_state

    @property
    def forward_activations_size(self) -> int:
        """
        micro_batch_size * context_window * hidden_dim
        :return: forward activations size (parameters)
        """
        return math.ceil(MICRO_BATCH_SIZE * self.context_window * self.hidden_dim)

    @property
    def pipeline_flow_size(self) -> int:
        """
        :return: pipeline flow size (parameters)
        """
        return math.ceil(self.forward_activations_size / self.num_layers)

    @property
    def flops(self) -> int:
        return math.ceil(6 * self.size * self.num_tokens / BILLION)

    @property
    def layer_flops(self) -> int:
        return math.ceil(self.flops / self.num_layers)

    @property
    def mini_batch_size(self) -> int:
        return self.global_batch_size // self.context_window


class LlmModels(Enum):
    GPT_3 = Model(
        name="GPT_3",
        size=175,
        num_tokens=300 * BILLION,
        num_layers=96,
        global_batch_size=3_200_000,
        context_window=2048,
        hidden_dim=12288,
        tensor_dim=8,
        pipeline_depth=8,
    )
    BLOOM = Model(
        name="BLOOM",
        size=176,
        num_tokens=366 * BILLION,
        num_layers=70,
        global_batch_size=2048 * 2048,
        context_window=2048,
        hidden_dim=14336,
        tensor_dim=4,
        pipeline_depth=12,
    )
    LLAMA2_70B = Model(
        name="LLaMA2_70B",
        size=70,
        num_tokens=2 * TRILLION,
        num_layers=80,
        global_batch_size=2048 * 1024,
        context_window=4096,
        hidden_dim=8192,
        tensor_dim=8,
        pipeline_depth=16,
    )
    # OPT_175B = Model(
    #     name="OPT_175B",
    #     size=175,
    #     num_tokens=300 * BILLION,
    #     num_layers=96,
    #     global_batch_size=2_000_000,
    #     context_window=2048,
    #     hidden_dim=12288,
    #     tensor_dim=4,
    #     pipeline_depth=31,
    # )
    # GOPHER = Model(
    #     name="GOPHER",
    #     size=280,
    #     num_tokens=300 * BILLION,
    #     num_layers=80,
    #     global_batch_size=6_000_000,
    #     context_window=2048,
    #     hidden_dim=16384,
    #     tensor_dim=8,
    #     pipeline_depth=32,
    # )
    # MT_NLG = Model(
    #     name="MT_NLG",
    #     size=530,
    #     num_tokens=300 * BILLION,
    #     num_layers=105,
    #     global_batch_size=4480 * 1920,
    #     context_window=2048,
    #     hidden_dim=20480,
    #     tensor_dim=8,
    #     pipeline_depth=35,
    # )
    # PaLM = Model(
    #     name="PaLM",
    #     size=540,
    #     num_tokens=780 * BILLION,
    #     num_layers=118,
    #     global_batch_size=2048 * 2240,
    #     context_window=2048,
    #     hidden_dim=18432,
    #     tensor_dim=8,
    #     pipeline_depth=12,
    # )
    # PANGU_SIGMA = Model(
    #     name="PANGU_SIGMA",
    #     size=1000,
    #     num_tokens=329 * BILLION,
    #     num_layers=96,
    #     global_batch_size=512 * 512,
    #     context_window=1024,
    #     hidden_dim=5120,
    # )
