import os
<<<<<<< HEAD

=======
from pathlib import Path
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
import pandas as pd
import typer
from conf import FLOODNS_ROOT
from floodns.external.cdf_generation.utils import (
    load_job_ids,
    load_job_info_df,
    save_data_parallelism_time_cdf,
)
from floodns.external.schemas.routing import Routing

app = typer.Typer()

NUM_FAILED_CORES = [0, 1, 4, 8]
NUM_CONCURRENT_JOBS = [1, 2, 3, 4, 5]
RING_SIZES = [2, 4, 8]
BASE_PATH = Path(FLOODNS_ROOT, "runs")


@app.command()
def generate_data_parallelism_time_cdf(routing: Routing):
    handle_data_parallelism_time(
        routing=routing,
        num_jobs=5,
        num_cores=8,
        ring_size=2,
    )
    for num_jobs in NUM_CONCURRENT_JOBS:
        for num_cores in NUM_FAILED_CORES:
            for ring_size in RING_SIZES:
                if num_jobs in {4, 5} and ring_size == 8:
                    print(
                        f"Skipping concurrent_jobs_{num_jobs} with ring_size_{ring_size} for {routing.value}"
                    )
                    continue
                handle_data_parallelism_time(
                    routing=routing,
                    num_jobs=num_jobs,
                    num_cores=num_cores,
                    ring_size=ring_size,
                )


def handle_data_parallelism_time(num_jobs: int, num_cores: int, routing: Routing, ring_size: int):
    concurrent_jobs_path = Path(
        BASE_PATH,
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        routing.value,
        "logs_floodns",
    )
    filename = Path(concurrent_jobs_path, "job_info.csv")
    if not os.path.exists(filename):
        print(f"File {filename} does not exist")
        return

    job_ids_folder = Path(
        BASE_PATH,
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
    )
    jobs = load_job_ids(
        job_ids_folder=job_ids_folder,
        num_concurrent_jobs=num_jobs,
        num_core_failures=num_cores,
        ring_size=ring_size,
    )

    for job_id in jobs["job_id"].unique().tolist():
        epochs = jobs[jobs["job_id"] == job_id]["epoch"].unique().tolist()
        df = load_job_info_df(filename=filename)
        if df.empty:
            print(f"File {filename} is empty")
            return
        df = df[df["job_id"] == job_id & df["epoch"].isin(epochs)]
        if df.empty:
            print(f"File {filename} is empty")
            return
        data = {
            "epoch": [],
            "duration": [],
        }
        for epoch in epochs:
            data["epoch"].append(epoch)
            slowest_stage = df[df["epoch"] == epoch]["duration"].max()
            data["duration"].append(slowest_stage)
        slowest_stage_df = pd.DataFrame(data)
        save_data_parallelism_time_cdf(
            df=slowest_stage_df,
            routing=routing,
            num_jobs=num_jobs,
            num_cores=num_cores,
            ring_size=ring_size,
            job_id=job_id,
        )


if __name__ == "__main__":
    app()
