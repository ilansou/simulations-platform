import os
from os import makedirs

import matplotlib.pyplot as plt
import pandas as pd
from floodns.external.plots_generation.utils import (
    get_header,
    get_metric_percentile,
    get_routing_color,
    get_title,
)
from floodns.external.schemas.routing import Routing
from typer import Typer
from conf import FLOODNS_ROOT
app = Typer()

NUM_FAILED_CORES = [0, 1, 4, 8]
NUM_CONCURRENT_JOBS = [1, 2, 3, 4, 5]
RING_SIZES = [2, 4, 8]
BASE_PATH = os.path.join(FLOODNS_ROOT, "cdfs")

percentiles = ["Average", "Median", "25th", "75th", "90th", "95th", "99th"]


@app.command()
def concurrent_job_x_data_parallelism_time(num_cores: int, ring_size: int, job_id: int):
    num_concurrent_jobs = NUM_CONCURRENT_JOBS
    if ring_size == 8:
        if job_id == 0:
            num_concurrent_jobs = [1, 2, 3]
        elif job_id == 1:
            num_concurrent_jobs = [2, 3]
    elif job_id == 1:
        num_concurrent_jobs = [2, 3, 4, 5]
    elif job_id == 2:
        num_concurrent_jobs = [3, 4, 5]
    elif job_id == 3:
        num_concurrent_jobs = [4, 5]
    elif job_id == 4:
        num_concurrent_jobs = [5]
    folders = {
        num_jobs: os.path.join(
            BASE_PATH,
            "data_parallelism_time",
            f"concurrent_jobs_{num_jobs}",
            f"{num_cores}_core_failures",
            f"ring_size_{ring_size}",
            f"job_{job_id}",
        )
        for num_jobs in num_concurrent_jobs
    }
    cdfs = {routing.value: [] for routing in Routing}

    for routing in Routing:
        for folder in folders.values():
            filename = os.path.join(folder, f"{routing.value}-data_parallelism_time.cdf")
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["data_parallelism_time", "cdf"])
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="data_parallelism_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="data_parallelism_time")
    ax.set_xlabel("Number Concurrent Jobs", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(num_concurrent_jobs)

    for routing in Routing:
        ax.plot(
            num_concurrent_jobs,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing),
        )
    ax.legend()

    folder = os.path.join(
        BASE_PATH,
        "data_parallelism_time",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        f"job_{job_id}",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
    plt.savefig(
        os.path.join(
            folder,
            "concurrent_job_x_data_parallelism_time.png",
        )
    )


@app.command()
def ring_size_x_data_parallelism_time(num_cores: int, num_jobs: int, job_id: int):
    ring_sizes = RING_SIZES
    if num_jobs in {4, 5}:
        ring_sizes = [2, 4]
    folders = {
        ring_size: os.path.join(
            BASE_PATH,
            "data_parallelism_time",
            f"concurrent_jobs_{num_jobs}",
            f"{num_cores}_core_failures",
            f"ring_size_{ring_size}",
            f"job_{job_id}",
        )
        for ring_size in ring_sizes
    }

    cdfs = {routing.value: [] for routing in Routing}

    for routing in Routing:
        for folder in folders.values():
            filename = os.path.join(folder, f"{routing.value}-data_parallelism_time.cdf")
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["data_parallelism_time", "cdf"])
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="data_parallelism_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="data_parallelism_time")
    ax.set_xlabel("Ring Size", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(ring_sizes)

    for routing in Routing:
        ax.plot(
            ring_sizes,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing),
        )
    ax.legend()

    folder = os.path.join(
        BASE_PATH,
        "data_parallelism_time",
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"job_{job_id}",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
    plt.savefig(
        os.path.join(
            folder,
            "ring_size_x_data_parallelism_time.png",
        )
    )


if __name__ == "__main__":
    app()
