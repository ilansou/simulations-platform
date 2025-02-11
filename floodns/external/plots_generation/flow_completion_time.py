import os
from os import makedirs
<<<<<<< HEAD

=======
from pathlib import Path
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
import matplotlib.pyplot as plt
import pandas as pd
from floodns.external.plots_generation.utils import (
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
<<<<<<< HEAD
BASE_PATH = os.path.join(FLOODNS_ROOT, "cdfs")
=======
BASE_PATH = Path(FLOODNS_ROOT, "cdfs")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5

percentiles = ["Average", "Median", "25th", "75th", "90th", "95th", "99th"]


@app.command()
def concurrent_job_x_fct(num_cores: int, ring_size: int, job_id: int):
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
<<<<<<< HEAD
        num_jobs: os.path.join(
=======
        num_jobs: Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            "flow_completion_time",
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
<<<<<<< HEAD
            filename = os.path.join(folder, f"{routing.value}-flow_completion_time.cdf")
=======
            filename = Path(folder, f"{routing.value}-flow_completion_time.cdf")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            if not os.path.exists(filename):
                print(f"File {filename} does not exist. Skipping...")
                continue
            df = pd.read_csv(filename, delimiter="\t", names=["fct", "cdf"])
            if df.empty:
                print(f"File {filename} is empty. Skipping...")
                continue
            cdfs[routing.value].append(
                get_metric_percentile(df=df, percentile="Average", metric="fct")
            )

    fig, ax = plt.subplots()
    for routing, cdf in cdfs.items():
        ax.plot(
            num_concurrent_jobs,
            cdf,
            "--o",
            label=get_title(routing),
            color=get_routing_color(routing),
        )

    ax.set_xlabel("Number of Concurrent Jobs", fontsize=14)
    ax.set_ylabel("Flow Completion Time (sec)", fontsize=14)
    ax.set_xticks(num_concurrent_jobs)
    ax.legend()

<<<<<<< HEAD
    folder = os.path.join(
=======
    folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        BASE_PATH,
        "flow_completion_time",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        f"job_{job_id}",
    ).replace("cdfs", "plots")
    makedirs(folder, exist_ok=True)
    plt.savefig(
<<<<<<< HEAD
        os.path.join(
=======
        Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            folder,
            "concurrent_job_x_fct.png",
        )
    )


if __name__ == "__main__":
    app()
