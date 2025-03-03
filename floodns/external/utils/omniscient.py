import os
from os import listdir
from pathlib import Path
import pandas as pd
from floodns.external.schemas.distributed_training import DistributedTraining
from conf import FLOODNS_ROOT


def get_job_ids(jobs_dir: str) -> list:
    job_ids = []
    for subdir in listdir(jobs_dir):
        if not subdir.startswith("job_"):
            continue
        job_id = int(subdir.split("_")[1])
        job_ids.append(job_id)
    return sorted(job_ids)


def load_jobs(
    level: int, n_tors: int, bw: int, load: float, parallel: DistributedTraining, job_ids: list
):
    jobs_dir = Path(
        FLOODNS_ROOT,
        "traffic_pairs",
        f"{level}_level",
        f"{n_tors}_tors",
        parallel.value,
        f"load_{load}",
    )

    jobs = {}
    for dirname in listdir(jobs_dir):
        if not dirname.startswith("job_"):
            continue
        job_id = int(dirname.split("_")[1])
        if job_id not in job_ids:
            continue
        filename = Path(jobs_dir, dirname, "data_parallelism.txt")
        df = pd.read_csv(filename, delimiter=" ", header=0)
        df.rename(columns={"#src": "src"}, inplace=True)
        start_time = df["start_time"].min()
        flow_size = df["flow_size"].min()
        opt_flow_duration = round((8 * flow_size) / bw)
        jobs[job_id] = {
            "virtual_links": df[df["src_tor"] != df["dst_tor"]][["src", "dst"]].values.tolist(),
            "tors": set(df["src_tor"].unique().tolist()),
            "start_time": start_time,
            "flow_size": flow_size,
            "opt_end_time": start_time + opt_flow_duration,
        }

    return dict(sorted(jobs.items(), key=lambda item: item[1]["start_time"]))


def group_jobs(jobs: dict):
    def intersects(t1, t2):
        """Check if t1 and t2 intersect."""
        return max(t1[0], t2[0]) < min(t1[1], t2[1])

    # Sort tuples by their first element
    data = {k: (v["start_time"], v["opt_end_time"]) for k, v in jobs.items()}
    sorted_items = sorted(data.items(), key=lambda x: x[1][0])

    groups = []
    for key1, val1 in sorted_items:
        job_ids = set()
        for key2, val2 in sorted_items:
            if key1 != key2 and intersects(val1, val2):
                job_ids.add(key2)
        group = {}
        for job_id in job_ids:
            group[job_id] = jobs[job_id]
        groups.append(group)

    return groups


def fetch_failed_links(failure_file: str) -> set:
    with open(failure_file, "r") as f:
        lines = f.readlines()

    failed_links = set()
    for line in lines:
        failed_links.add(tuple(map(int, line.split())))

    return failed_links
