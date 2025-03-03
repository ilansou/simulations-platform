import os
from pathlib import Path
import pandas as pd
import typer
from floodns.external.cdf_generation.utils import save_controller_computation_time_cdf
from floodns.external.schemas.routing import Routing
from conf import FLOODNS_ROOT

app = typer.Typer()

NUM_FAILED_CORES = [0, 1, 4, 8]
NUM_CONCURRENT_JOBS = [1, 2, 3, 4, 5]
RING_SIZES = [2, 4, 8]
BASE_PATH = Path(FLOODNS_ROOT, "runs")


@app.command()
def generate_controller_computation_cdf(routing: Routing):
    # avg_computation_ms keys are the number of concurrent jobs
    # in each dict, the keys are the number of failed cores
    # for concurrent jobs == 1, in the dict of failed cores there is another dict where the keys are ring sizes
    for num_jobs in NUM_CONCURRENT_JOBS:
        for num_cores in NUM_FAILED_CORES:
            for ring_size in RING_SIZES:
                if num_jobs in {4, 5} and ring_size == 8:
                    print(f"Skipping concurrent_jobs_{num_jobs} with ring_size_{ring_size}")
                    continue
                handle_controller_computation(
                    routing=routing,
                    num_jobs=num_jobs,
                    num_cores=num_cores,
                    ring_size=ring_size,
                )


def handle_controller_computation(
    routing: Routing,
    num_jobs: int,
    num_cores: int,
    ring_size: int,
):
    concurrent_jobs_path = Path(
        BASE_PATH,
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        routing.value,
        "logs_floodns",
    )
    filename = Path(concurrent_jobs_path, "assignments_duration.csv")
    if not os.path.exists(filename):
        print(f"File {filename} does not exist")
        return
    df = pd.read_csv(filename, names=["computation", "num_assignments", "Unnamed: 2"])
    if df.empty:
        print(f"File {filename} is empty")
        return
    df.drop(columns=["Unnamed: 2"], inplace=True)
    save_controller_computation_time_cdf(
        df=df,
        routing=routing.value,
        num_jobs=num_jobs,
        num_cores=num_cores,
        ring_size=ring_size,
    )


if __name__ == "__main__":
    app()
