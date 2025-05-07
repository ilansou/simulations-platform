import math
import random

from floodns.external.schemas.accelerators import Accelerator
from floodns.external.schemas.job import DataParallel, Job
from floodns.external.schemas.models import LlmModels, Model
from floodns.external.utils.units import BILLION

LOWER_BOUND = 1_000_000_000  # 1s
UPPER_BOUND = 10 * LOWER_BOUND  # 10s
NUM_NICS_PER_HOST = 8


def create_jobs_similar_dp_dim(
    tor_to_nics: dict,
    accelerator: Accelerator,
    radix: int,
    data_parallelism_dim: int,
    seed: int,
    jobs_order: list,
):
    random.seed(seed)
    jobs: list = []
    job_id, jobs_total_nics = 0, 0
    for model_name in jobs_order:
        model = LlmModels[model_name].value
        num_gpus = model.full_copy * data_parallelism_dim
        job = build_ddp_job(
            model=model,
            accelerator=accelerator,
            job_id=job_id,
            radix=radix,
            tor_to_nics=tor_to_nics,
            data_parallelism_dim=data_parallelism_dim,
        )
        jobs.append(job)
        job_id += 1
        jobs_total_nics += num_gpus

    return jobs


def create_jobs_different_dp_dim(
    num_concurrent_jobs: int,
    tor_to_nics: dict,
    accelerator: Accelerator,
    radix: int,
    seed: int,
):
    random.seed(seed)
    jobs: list = []
    job_id, jobs_total_nics = 0, 0
    while job_id < num_concurrent_jobs:
        model = random.choice(list(LlmModels)).value
        data_parallelism_dim = random.choice([2, 4, 8])
        num_gpus = model.full_copy * data_parallelism_dim
        job = build_ddp_job(
            model=model,
            accelerator=accelerator,
            job_id=job_id,
            radix=radix,
            tor_to_nics=tor_to_nics,
            data_parallelism_dim=data_parallelism_dim,
        )
        jobs.append(job)
        job_id += 1
        jobs_total_nics += num_gpus

    return jobs


def build_ddp_job(
    model: Model,
    accelerator: Accelerator,
    job_id: int,
    radix: int,
    tor_to_nics: dict,
    data_parallelism_dim: int | str,
):
    if data_parallelism_dim == "different":
        print(f"Warning: build_ddp_job called with data_parallelism_dim='different'. Defaulting to 2.")
        actual_dp_dim = 2 
    elif isinstance(data_parallelism_dim, int):
        actual_dp_dim = data_parallelism_dim
    else:
        raise TypeError(f"Unexpected type for data_parallelism_dim: {type(data_parallelism_dim)}")

    full_copies = []
    for i in range(actual_dp_dim):
        full_copy = model.full_copy
        nics = []
        total_nics_to_schedule = NUM_NICS_PER_HOST * math.ceil(full_copy / NUM_NICS_PER_HOST)
        while total_nics_to_schedule > 0:
            tor_id = random.choice(list(tor_to_nics.keys()))
            tor_nics = tor_to_nics[tor_id]
            if total_nics_to_schedule < radix:
                assert (radix - total_nics_to_schedule) % NUM_NICS_PER_HOST == 0
                remaining_tor_nics = list(tor_nics)[:total_nics_to_schedule]
                nics.extend(remaining_tor_nics)
                tor_to_nics[tor_id] = set(list(tor_nics)[total_nics_to_schedule:])
            else:
                nics.extend(list(tor_nics))
                tor_to_nics.pop(tor_id)
            total_nics_to_schedule = total_nics_to_schedule - len(tor_nics)

        if len(nics) > full_copy:
            nics = nics[:full_copy]
        full_copies.append(nics)

    data_parallels = []
    for i in range(model.full_copy):
        ring_nics = [full_copies[j][i] for j in range(actual_dp_dim)]
        flow_size = math.ceil(
            math.ceil(BILLION * model.weights / model.full_copy) / actual_dp_dim
        )
        data_parallels.append(DataParallel(nics=ring_nics, flow_size=flow_size))

    compute_time = model.get_compute_time(accelerator=accelerator)
    return Job(
        job_id=job_id,
        model=model,
        pipelines=[],
        data_parallels=data_parallels,
        start_time=random.randint(LOWER_BOUND, UPPER_BOUND) + compute_time,
        compute_time=compute_time,
        mini_batch_size=0,
    )
