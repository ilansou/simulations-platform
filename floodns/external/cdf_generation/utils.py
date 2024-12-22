import os
from os import makedirs

import numpy as np
import pandas as pd
from floodns.external.analysis.routing_strategy_comparison import compare_routing_strategies
from floodns.external.schemas.routing import Routing
from conf import FLOODNS_ROOT

# CDF interpolation x-values
plot_x_vals: list = []
plot_x_vals.extend(np.arange(1e-8, 1e-7, 1e-10))
plot_x_vals.extend(np.arange(1e-7, 1e-6, 1e-9))
plot_x_vals.extend(np.arange(1e-6, 1e-5, 1e-8))
plot_x_vals.extend(np.arange(1e-5, 1e-4, 1e-7))
plot_x_vals.extend(np.arange(1e-4, 1e-3, 1e-6))
plot_x_vals.extend(np.arange(1e-3, 1e-2, 1e-5))
plot_x_vals.extend(np.arange(1e-2, 1e-1, 1e-4))
plot_x_vals.extend(np.arange(1e-1, 1e0, 1e-3))
plot_x_vals.extend(np.arange(1e0, 1e1, 1e-2))
plot_x_vals.extend(np.arange(1e1, 1e2, 1e-1))
plot_x_vals.extend(np.arange(1e2, 1e3, 1e0))
plot_x_vals.extend(np.arange(1e3, 1e4, 1e1))
plot_x_vals.extend(np.arange(1e4, 1e5, 1e2))
plot_x_vals.extend(np.arange(1e5, 1e6, 1e3))
plot_x_vals.extend(np.arange(1e6, 1e7, 1e4))
plot_x_vals.extend(np.arange(1e7, 1e8, 1e5))
plot_x_vals.extend(np.arange(1e8, 1e9, 1e6))
plot_x_vals.extend(np.arange(1e9, 1e10, 1e7))
plot_x_vals.extend(np.arange(1e10, 1e11, 1e8))
plot_x_vals.extend(np.arange(1e11, 1e12, 1e9))
plot_x_vals.extend(np.arange(1e12, 1e13, 1e10))

BASE_CDF_FOLDER = os.path.join(FLOODNS_ROOT, "cdfs")


def load_job_info_df(filename: str):
    df = pd.read_csv(
        filename,
        names=[
            "job_id",
            "epoch",
            "stage",
            "start_time",
            "end_time",
            "duration",
            "finished",
            "total_flows",
            "flow_size_bytes",
            "conn_ids",
            "Unnamed: 10",
        ],
    )
    df.sort_values(by=["job_id", "start_time"], inplace=True)
    df.drop(columns=["Unnamed: 10"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def load_connection_info_df(filename: str) -> pd.DataFrame:
    if not os.path.exists(filename):
        return None
    connection_info = pd.read_csv(
        filename,
        names=[
            "job_id",
            "epoch",
            "stage_index",
            "conn_id",
            "src_id",
            "dst_id",
            "size",
            "sent",
            "flow_ids",
            "start_time",
            "end_time",
            "duration",
            "avg_rate",
            "finished",
            "metadata",
        ],
    )
    connection_info.sort_values(by=["conn_id", "start_time"], inplace=True)
    return connection_info


def load_job_ids(
    job_ids_folder: str, num_concurrent_jobs: int, num_core_failures: int, ring_size: int
):
    if not os.path.exists(os.path.join(job_ids_folder, "successful_jobs.csv")):
        print(f"Generating file {os.path.join(job_ids_folder, 'successful_jobs.csv')}")
        compare_routing_strategies(
            num_concurrent_jobs=num_concurrent_jobs,
            num_core_failures=num_core_failures,
            ring_size=ring_size,
        )
    jobs = pd.read_csv(os.path.join(job_ids_folder, "successful_jobs.csv"))
    return jobs


def save_data_parallelism_time_cdf(
    df: pd.DataFrame, routing: Routing, num_jobs: int, num_cores: int, ring_size: int, job_id: int
):
    folder = os.path.join(
        BASE_CDF_FOLDER,
        "data_parallelism_time",
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        f"job_{job_id}",
    )
    makedirs(folder, exist_ok=True)

    filename = f"{routing.value}-data_parallelism_time.cdf"
    cdf_file = os.path.join(folder, filename)
    save_cdf(data=df["duration"] / 1e9, cdf_file=cdf_file)


def save_fct_cdf(
    df: pd.DataFrame, routing: Routing, num_jobs: int, num_cores: int, ring_size: int, job_id: int
):
    folder = os.path.join(
        BASE_CDF_FOLDER,
        "flow_completion_time",
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        f"job_{job_id}",
    )
    makedirs(folder, exist_ok=True)

    filename = f"{routing.value}-flow_completion_time.cdf"
    cdf_file = os.path.join(folder, filename)
    save_cdf(data=df["duration"] / 1e9, cdf_file=cdf_file)


def save_throughput_cdf(
    df: pd.DataFrame, routing: Routing, num_jobs: int, num_cores: int, ring_size: int, job_id: int
):
    folder = os.path.join(
        BASE_CDF_FOLDER,
        "throughput",
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
        f"job_{job_id}",
    )
    makedirs(folder, exist_ok=True)

    filename = f"{routing.value}-throughput.cdf"
    cdf_file = os.path.join(folder, filename)
    save_cdf(data=df["sent"] / df["duration"], cdf_file=cdf_file)


def save_controller_computation_time_cdf(
    df: pd.DataFrame, routing: Routing, num_jobs: int, num_cores: int, ring_size: int
):
    folder = os.path.join(
        BASE_CDF_FOLDER,
        "controller_computation",
        f"concurrent_jobs_{num_jobs}",
        f"{num_cores}_core_failures",
        f"ring_size_{ring_size}",
    )
    makedirs(folder, exist_ok=True)

    cdf_file = os.path.join(folder, f"{routing}-controller_computation.cdf")
    save_cdf(data=df["computation"], cdf_file=cdf_file)


def save_cdf(data: pd.Series, cdf_file: str):
    sorted_fct = np.sort(data)
    if len(sorted_fct) == 1:
        with open(cdf_file, "w+") as outfile:
            outfile.write(str(sorted_fct[0]) + "\t" + str(1) + "\n")
        return
    cdf_y_vals = np.arange(len(sorted_fct)) / float(len(sorted_fct) - 1)
    plot_y_vals = np.interp(plot_x_vals, sorted_fct, cdf_y_vals)
    with open(cdf_file, "w+") as outfile:
        for k in range(0, len(plot_x_vals)):
            if k == len(plot_x_vals) - 1 or plot_y_vals[k + 1] != 0:
                outfile.write(str(plot_x_vals[k]) + "\t" + str(plot_y_vals[k]) + "\n")
            if plot_y_vals[k] == 1 and plot_y_vals[k + 1] == 1:
                break
