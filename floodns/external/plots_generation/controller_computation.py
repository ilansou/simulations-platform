import os
from os import makedirs
<<<<<<< HEAD

=======
from pathlib import Path
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
import matplotlib.pyplot as plt
import pandas as pd
from floodns.external.plots_generation.utils import (
    get_header,
    get_metric_percentile,
    get_routing_color,
    get_title,
)
from floodns.external.schemas.routing import CentralizedControllerRouting
from typer import Typer
from conf import FLOODNS_ROOT
app = Typer()

NUM_FAILED_CORES = [0, 1, 4, 8]
NUM_CONCURRENT_JOBS = [1, 2, 3, 4, 5]
RING_SIZES = [2, 4, 8]
<<<<<<< HEAD
BASE_PATH = os.path.join(FLOODNS_ROOT, "cdfs")
=======
BASE_PATH = Path(FLOODNS_ROOT, "cdfs")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5

percentiles = ["Average", "Median", "25th", "75th", "90th", "95th", "99th"]


@app.command()
def ring_size_x_core_failures(ring_size: int, num_concurrent_jobs: int):
    if num_concurrent_jobs in {4, 5} and ring_size == 8:
        print(f"Skipping concurrent_jobs_{num_concurrent_jobs} and ring_size_{ring_size}")
        return

    folders = {
<<<<<<< HEAD
        core: os.path.join(
=======
        core: Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            "controller_computation",
            f"concurrent_jobs_{num_concurrent_jobs}",
            f"{core}_core_failures",
            f"ring_size_{ring_size}",
        )
        for core in NUM_FAILED_CORES
    }
    cdfs = {routing.value: [] for routing in CentralizedControllerRouting}

    for routing in CentralizedControllerRouting:
        for num_cores, folder in folders.items():
<<<<<<< HEAD
            filename = os.path.join(folder, f"{routing.value}-controller_computation.cdf")
=======
            filename = Path(folder, f"{routing.value}-controller_computation.cdf")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["computation_time", "cdf"])
            df["computation_time"] = df["computation_time"] / 1000  # Convert to seconds
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="computation_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="computation_time")
    ax.set_xlabel("Number Core Failures", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(NUM_FAILED_CORES)

    for routing in CentralizedControllerRouting:
        ax.plot(
            NUM_FAILED_CORES,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing.value),
        )
    ax.legend()

<<<<<<< HEAD
    folder = os.path.join(
=======
    folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        BASE_PATH,
        "controller_computation",
        f"concurrent_jobs_{num_concurrent_jobs}",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
<<<<<<< HEAD
    plt.savefig(os.path.join(folder, f"ring_size_{ring_size}_x_core_failures.png"))
=======
    plt.savefig(Path(folder, f"ring_size_{ring_size}_x_core_failures.png"))
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5


@app.command()
def core_failures_x_ring_size(num_cores: int, num_concurrent_jobs: int):
    ring_sizes = RING_SIZES
    if num_concurrent_jobs in {4, 5}:
        ring_sizes = [2, 4]

    folders = {
<<<<<<< HEAD
        ring_size: os.path.join(
=======
        ring_size: Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            "controller_computation",
            f"concurrent_jobs_{num_concurrent_jobs}",
            f"{num_cores}_core_failures",
            f"ring_size_{ring_size}",
        )
        for ring_size in ring_sizes
    }
    cdfs = {routing.value: [] for routing in CentralizedControllerRouting}

    for routing in CentralizedControllerRouting:
        for ring_size, folder in folders.items():
<<<<<<< HEAD
            filename = os.path.join(folder, f"{routing.value}-controller_computation.cdf")
=======
            filename = Path(folder, f"{routing.value}-controller_computation.cdf")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["computation_time", "cdf"])
            df["computation_time"] = df["computation_time"] / 1000  # Convert to seconds
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="computation_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="computation_time")
    ax.set_xlabel("Ring Size", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(ring_sizes)

    for routing in CentralizedControllerRouting:
        ax.plot(
            ring_sizes,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing),
        )
    ax.legend()

<<<<<<< HEAD
    folder = os.path.join(
=======
    folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        BASE_PATH,
        "controller_computation",
        f"concurrent_jobs_{num_concurrent_jobs}",
        f"{num_cores}_core_failures",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
<<<<<<< HEAD
    plt.savefig(os.path.join(folder, f"{num_cores}_core_failures_x_ring_size.png"))
=======
    plt.savefig(Path(folder, f"{num_cores}_core_failures_x_ring_size.png"))
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5


@app.command()
def concurrent_jobs_x_core_failures(num_jobs: int, ring_size: int):
    if num_jobs in {4, 5} and ring_size == 8:
        print(f"Skipping concurrent_jobs_{num_jobs} and ring_size_{ring_size}")
        return

    folders = {
<<<<<<< HEAD
        core: os.path.join(
=======
        core: Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            "controller_computation",
            f"concurrent_jobs_{num_jobs}",
            f"{core}_core_failures",
            f"ring_size_{ring_size}",
        )
        for core in NUM_FAILED_CORES
    }
    cdfs = {routing.value: [] for routing in CentralizedControllerRouting}

    for routing in CentralizedControllerRouting:
        for num_cores, folder in folders.items():
<<<<<<< HEAD
            filename = os.path.join(folder, f"{routing.value}-controller_computation.cdf")
=======
            filename = Path(folder, f"{routing.value}-controller_computation.cdf")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["computation_time", "cdf"])
            df["computation_time"] = df["computation_time"] / 1000  # Convert to seconds
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="computation_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="computation_time")
    ax.set_xlabel("Number Core Failures", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(NUM_FAILED_CORES)

    for routing in CentralizedControllerRouting:
        ax.plot(
            NUM_FAILED_CORES,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing),
        )
    ax.legend()

<<<<<<< HEAD
    folder = os.path.join(
=======
    folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        BASE_PATH,
        "controller_computation",
        f"concurrent_jobs_{num_jobs}",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
<<<<<<< HEAD
    plt.savefig(os.path.join(folder, f"concurrent_jobs_{num_jobs}_x_num_core_failures.png"))
=======
    plt.savefig(Path(folder, f"concurrent_jobs_{num_jobs}_x_num_core_failures.png"))
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5


@app.command()
def core_failures_x_concurrent_jobs(num_cores: int, ring_size: int):
    folders = {
<<<<<<< HEAD
        num_jobs: os.path.join(
=======
        num_jobs: Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            "controller_computation",
            f"concurrent_jobs_{num_jobs}",
            f"{num_cores}_core_failures",
            f"ring_size_{ring_size}",
        )
        for num_jobs in NUM_CONCURRENT_JOBS
    }
    cdfs = {routing.value: [] for routing in CentralizedControllerRouting}

    for routing in CentralizedControllerRouting:
        for num_jobs, folder in folders.items():
<<<<<<< HEAD
            filename = os.path.join(folder, f"{routing.value}-controller_computation.cdf")
=======
            filename = Path(folder, f"{routing.value}-controller_computation.cdf")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["computation_time", "cdf"])
            df["computation_time"] = df["computation_time"] / 1000  # Convert to seconds
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="computation_time")
            )

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    header = get_header(metric="computation_time")
    ax.set_xlabel("Number Concurrent Jobs", fontsize=14)
    ax.set_ylabel(header, fontsize=14)
    ax.set_xticks(NUM_CONCURRENT_JOBS)
    min_value = min([min(cdfs[routing.value]) for routing in CentralizedControllerRouting])
    max_value = max([max(cdfs[routing.value]) for routing in CentralizedControllerRouting])
    values = [
        min_value,
        round(max_value / 4, 1),
        round(max_value / 2, 1),
        round(max_value / 2, 1) + round(max_value / 4, 1),
        int(max_value),
    ]
    ax.set_yticks(values)

    for routing in CentralizedControllerRouting:
        ax.plot(
            NUM_CONCURRENT_JOBS,
            cdfs[routing.value],
            "--o",
            label=get_title(routing.value),
            color=get_routing_color(routing.value),
        )
    ax.legend()

<<<<<<< HEAD
    folder = os.path.join(BASE_PATH, "controller_computation").replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
    plt.savefig(os.path.join(folder, f"{num_cores}_core_failures_x_concurrent_jobs.png"))
=======
    folder = Path(BASE_PATH, "controller_computation").replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
    plt.savefig(Path(folder, f"{num_cores}_core_failures_x_concurrent_jobs.png"))
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5


if __name__ == "__main__":
    app()
