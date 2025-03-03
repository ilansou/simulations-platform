import os
import random
from os import makedirs
from pathlib import Path
from floodns.external.jobs_generator.job_generator import (
    build_ddp_job,
    create_jobs_different_dp_dim,
    create_jobs_similar_dp_dim,
)
from floodns.external.jobs_generator.writer import write_ddp_file
from floodns.external.schemas.accelerators import Accelerators
from floodns.external.schemas.models import LlmModels
from floodns.external.utils.graph import get_tor_to_hosts
from typer import Typer
from conf import FLOODNS_ROOT
app = Typer()
jobs_order = {
    2: {
        2: ["BLOOM", "LLAMA2_70B"],
        4: ["BLOOM", "LLAMA2_70B"],
        8: ["BLOOM", "GPT_3"],
    },
    3: {
        2: ["BLOOM", "LLAMA2_70B", "LLAMA2_70B"],
        4: ["BLOOM", "LLAMA2_70B", "GPT_3"],
        8: ["BLOOM", "GPT_3", "LLAMA2_70B"],
    },
    4: {
        2: ["BLOOM", "LLAMA2_70B", "LLAMA2_70B", "BLOOM"],
        4: ["BLOOM", "LLAMA2_70B", "GPT_3", "LLAMA2_70B"],
    },
    5: {
        2: ["BLOOM", "LLAMA2_70B", "LLAMA2_70B", "BLOOM", "GPT_3"],
        4: ["BLOOM", "LLAMA2_70B", "GPT_3", "LLAMA2_70B", "GPT_3"],
    },
}


@app.command()
def gen_single_job_ddp_pairs(
    accelerator_name: str,
    model_name: str,
    n_tors: int,
    data_parallelism_dim: int,
    seed: int,
):
    random.seed(seed)
    radix = n_tors // 2
    accelerator = Accelerators[accelerator_name].value
    model = LlmModels[model_name].value
    tor_to_nics = get_tor_to_hosts(n_tors=n_tors)
    job = build_ddp_job(
        model=model,
        accelerator=accelerator,
        job_id=0,
        radix=radix,
        tor_to_nics=tor_to_nics,
        data_parallelism_dim=data_parallelism_dim,
    )

    traffic_pairs_dir = Path(
        FLOODNS_ROOT,
        "traffic_pairs",
        f"seed_{seed}",
        "concurrent_jobs_1",
        f"ring_size_{data_parallelism_dim}",
        model_name,
    )
    save_jobs(traffic_pairs_dir, [job], n_tors)


@app.command()
def gen_ddp_pairs(
    accelerator_name: str,
    n_tors: int,
    num_concurrent_jobs: int,
    data_parallelism_dim: int,
    seed: int,
):
    assert num_concurrent_jobs > 1, "Number of concurrent jobs must be greater than 1"
    if num_concurrent_jobs in {4, 5} and data_parallelism_dim == 8:
        print("data_parallelism_dim cannot be 8 for num_concurrent_jobs in {4,5}")
        return
    radix = n_tors // 2
    accelerator = Accelerators[accelerator_name].value
    tor_to_nics = get_tor_to_hosts(n_tors=n_tors)
    jobs = create_jobs_similar_dp_dim(
        tor_to_nics=tor_to_nics,
        accelerator=accelerator,
        radix=radix,
        data_parallelism_dim=data_parallelism_dim,
        seed=seed,
        jobs_order=jobs_order[num_concurrent_jobs][data_parallelism_dim],
    )

    if len(jobs) == 0:
        print("No jobs generated")
        return

    traffic_pairs_dir = Path(
        FLOODNS_ROOT,
        "traffic_pairs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_concurrent_jobs}",
        f"ring_size_{data_parallelism_dim}",
    )
    save_jobs(traffic_pairs_dir, jobs, n_tors)


@app.command()
def gen_ddp_pairs_different_sizes(
    accelerator_name: str,
    n_tors: int,
    num_concurrent_jobs: int,
    seed: int,
):
    assert num_concurrent_jobs > 1, "Number of concurrent jobs must be greater than 1"
    radix = n_tors // 2
    accelerator = Accelerators[accelerator_name].value
    tor_to_nics = get_tor_to_hosts(n_tors=n_tors)
    jobs = create_jobs_different_dp_dim(
        num_concurrent_jobs=num_concurrent_jobs,
        tor_to_nics=tor_to_nics,
        accelerator=accelerator,
        radix=radix,
        seed=seed,
    )

    if len(jobs) == 0:
        print("No jobs generated")
        return

    traffic_pairs_dir = Path(
        FLOODNS_ROOT,
        "traffic_pairs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_concurrent_jobs}",
        "different_ring_sizes",
    )
    save_jobs(traffic_pairs_dir, jobs, n_tors)


def save_jobs(traffic_pairs_dir: str, jobs: list, n_tors: int):
    makedirs(traffic_pairs_dir, exist_ok=True)

    for job in jobs:
        ddp_filename = Path(traffic_pairs_dir, f"job_{job.job_id}-{job.model.name}.txt")
        write_ddp_file(n_tors=n_tors, filename=ddp_filename, job=job)


if __name__ == "__main__":
    app()
