import os

import pandas as pd
import typer
from floodns.external.schemas.routing import Routing
from conf import FLOODNS_ROOT

app = typer.Typer()

NUM_FAILED_CORES = [0, 1, 4, 8]
RING_SIZES = [2, 4, 8]


@app.command()
def basic_sim(experiment_dir: str):
    convert_to_human_readable_helper(logs_floodns_dir=os.path.join(experiment_dir, "logs_floodns"))


@app.command()
def different_ring_sizes(num_concurrent_jobs: int, seed: int):
    assert num_concurrent_jobs > 1, "num_concurrent_jobs must be greater than 1"
    for routing in Routing:
        for core_failures in NUM_FAILED_CORES:
            folder = os.path.join(
                FLOODNS_ROOT,
                "runs",
                f"seed_{seed}",
                f"concurrent_jobs_{num_concurrent_jobs}",
                f"{core_failures}_core_failures",
                "different_ring_sizes",
                routing.value,
                "logs_floodns",
            )
            if not os.path.exists(folder):
                print(f"logs_floodns does not exist for {folder}.")
                return
            convert_to_human_readable_helper(logs_floodns_dir=folder)
            print(
                f"done for routing {routing}, different ring sizes, {core_failures} core failures"
            )
            print("-" * 100)


@app.command()
def concurrent_jobs(num_concurrent_jobs: int, seed: int):
    for core_failures in NUM_FAILED_CORES:
        for ring_size in RING_SIZES:
            for routing in Routing:
                if num_concurrent_jobs == 1:
                    for model_name in ["GPT_3", "BLOOM", "LLAMA2_70B"]:
                        single_job(
                            num_concurrent_jobs=num_concurrent_jobs,
                            seed=seed,
                            core_failures=core_failures,
                            ring_size=ring_size,
                            routing=routing,
                            model_name=model_name,
                        )
                        print(
                            f"done for routing {routing}, model {model_name}, ring size {ring_size}, {core_failures} core failures"
                        )
                    print("-" * 100)
                else:
                    multiple_jobs(
                        num_concurrent_jobs=num_concurrent_jobs,
                        seed=seed,
                        core_failures=core_failures,
                        ring_size=ring_size,
                        routing=routing,
                    )
                    print(
                        f"done for routing {routing}, ring size {ring_size}, {core_failures} core failures"
                    )
                    print("-" * 100)


def single_job(
    num_concurrent_jobs: int,
    seed: int,
    core_failures: int,
    ring_size: int,
    routing: Routing,
    model_name: str,
):
    folder = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_concurrent_jobs}",
        f"{core_failures}_core_failures",
        f"ring_size_{ring_size}",
        model_name,
        routing.value,
    )
    if not os.path.exists(os.path.join(folder, "logs_floodns")):
        print(f"logs_floodns does not exist for {os.path.join(folder, 'logs_floodns')}.")
        return
    convert_to_human_readable_helper(logs_floodns_dir=os.path.join(folder, "logs_floodns"))


def multiple_jobs(
    num_concurrent_jobs: int, seed: int, core_failures: int, ring_size: int, routing: Routing
):
    folder = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_concurrent_jobs}",
        f"{core_failures}_core_failures",
        f"ring_size_{ring_size}",
        routing.value,
    )
    if not os.path.exists(os.path.join(folder, "logs_floodns")):
        print(f"logs_floodns does not exist for {os.path.join(folder, 'logs_floodns')}.")
        return
    convert_to_human_readable_helper(logs_floodns_dir=os.path.join(folder, "logs_floodns"))


def convert_to_human_readable_helper(logs_floodns_dir: str):
    convert_job_info_to_human_readable(logs_floodns_dir=logs_floodns_dir)
    convert_connection_info_to_human_readable(logs_floodns_dir=logs_floodns_dir)
    convert_flow_info_to_human_readable(logs_floodns_dir=logs_floodns_dir)


def convert_connection_info_to_human_readable(logs_floodns_dir: str):
    csv_file = os.path.join(logs_floodns_dir, "connection_info.csv")
    if not os.path.exists(csv_file):
        print(f"{csv_file} does not exist.")
        return
    connection_info = pd.read_csv(csv_file, header=None)
    if connection_info.empty:
        print("No connections found.")
        return
    csv_file = os.path.join(FLOODNS_ROOT, "runs", "headers", "connection_info.header")
    connection_info.columns = pd.read_csv(csv_file).columns
    connection_info.sort_values(by=["start_time", "connection_id"], inplace=True)
    with open(logs_floodns_dir + "/connection_info.txt", "w+") as f:
        # Header
        f.write(
            "Job ID  Epoch  Stage  Conn. ID   Source   Target   Size           Sent           Flows' IDs     Start time         "
            "End time           Duration         Progress     Avg. rate        Finished?     Metadata\n"
        )

        for i, row in connection_info.iterrows():
            # check if row["metadata"] is NaN
            if row["metadata"] != row["metadata"]:
                row["metadata"] = ""
            f.write(
                "%-7d %-6d %-6d %-10d %-8d %-8d %-14s %-14s %-14s %-18s %-18s %-16s %-12s %-16s %-14s %s\n"
                % (
                    row["job_id"],  # Job ID
                    row["epoch"],  # Epoch
                    row["stage_index"],  # Stage
                    row["connection_id"],  # Connection ID
                    row["source_node_id"],  # Source
                    row["dest_node_id"],  # Target
                    "%.2f Gbit" % (float(row["total_size"]) / 1_000_000_000.0),  # Size
                    "%.2f Gbit" % (float(row["amount_sent"]) / 1_000_000_000.0),  # Sent
                    row["FLOW_LIST"],  # Flows' IDs
                    "%.2f s" % (float(row["start_time"]) / 1_000_000_000.0),  # Start time
                    "%.2f s" % (float(row["end_time"]) / 1_000_000_000.0),  # End time
                    "%.2f s" % (float(row["duration"]) / 1_000_000_000.0),  # Duration
                    "%.2f %%"
                    % (float(row["amount_sent"]) / float(row["total_size"]) * 100.0),  # Progress
                    "%.2f Gbit/s" % (float(row["average_bandwidth"])),  # Avg. rate
                    row["COMPLETED"],  # Finished? ["Y", "N"]
                    row["metadata"].strip(),  # Metadata
                )
            )


def convert_job_info_to_human_readable(logs_floodns_dir: str):
    csv_file = os.path.join(logs_floodns_dir, "job_info.csv")
    if not os.path.exists(csv_file):
        print(f"{csv_file} does not exist.")
        return
    job_info = pd.read_csv(csv_file, header=None)
    if job_info.empty:
        print("No jobs found.")
        return
    csv_file = os.path.join(FLOODNS_ROOT, "runs", "headers", "job_info.header")
    job_info.columns = pd.read_csv(csv_file).columns
    job_info.sort_values(by=["start_time", "job_id"], inplace=True)
    job_info.drop(columns=["Unnamed: 10"], inplace=True)
    with open(logs_floodns_dir + "/job_info.txt", "w+") as f:
        # Header
        f.write(
            "Job ID    Epoch    Stage Index     Start time         End time           Duration         "
            "Finished    Total Flows      Flow Size         Connections' IDs\n"
        )

        for i, row in job_info.iterrows():
            f.write(
                "%-9d %-8d %-15d %-18s %-18s %-16s %-11s %-16d %-17s %s\n"
                % (
                    row["job_id"],  # Job ID
                    row["epoch"],  # Epoch
                    row["stage"],  # Stage Index
                    f"{(float(row['start_time']) / 1_000_000_000.):.2f} s",  # Start time (seconds)
                    f"{(float(row['end_time']) / 1_000_000_000.0):.2f} s",  # End time (seconds)
                    f"{float(row['duration'] / 1_000_000_000.0):.2f} s",
                    row["finished"],  # Finished? ["Y", "N"]
                    row["total_flows"],  # Total Flows
                    "%.2f Gbit" % (float(row["flow_size"]) / 1_000_000_000.0),  # Flow Size
                    row["conn_ids"],  # Connections' IDs
                )
            )


def convert_flow_info_to_human_readable(logs_floodns_dir: str):
    csv_file = os.path.join(logs_floodns_dir, "flow_info.csv")
    if not os.path.exists(csv_file):
        print(f"{csv_file} does not exist.")
        return
    flow_info = pd.read_csv(csv_file, header=None)
    if flow_info.empty:
        print("No flows found.")
        return
    csv_file = os.path.join(FLOODNS_ROOT, "runs", "headers", "flow_info.header")
    flow_info.columns = pd.read_csv(csv_file).columns
    flow_info.sort_values(by=["flow_id", "start_time"], inplace=True)
    with open(logs_floodns_dir + "/flow_info.txt", "w+") as f:
        # Header
        f.write(
            "Flow ID    Source   Target   Path                  Start time         End time           Duration         "
            "Amount sent     Avg. bandwidth   Metadata\n"
        )

        for i, row in flow_info.iterrows():
            # check if row["metadata"] is NaN
            if row["metadata"] != row["metadata"]:
                row["metadata"] = ""
            f.write(
                "%-10d %-8d %-8d %-21s %-18s %-18s %-16s %-15s %-17s %s\n"
                % (
                    row["flow_id"],  # Flow ID
                    row["source_node_id"],  # Source
                    row["dest_node_id"],  # Target
                    print_path(row["PATH"]),  # Path
                    "%.2f s" % (float(row["start_time"]) / 1_000_000_000.0),  # Start time
                    "%.2f s" % (float(row["end_time"]) / 1_000_000_000.0),  # End time
                    "%.2f s" % (float(row["duration"]) / 1_000_000_000.0),  # Duration
                    "%.2f Gbit" % (float(row["amount_sent"]) / 1_000_000_000.0),  # Amount sent
                    "%.2f Gbit/s" % (float(row["average_bandwidth"])),  # Average bandwidth
                    row["metadata"].strip(),  # Metadata
                )
            )


def print_path(path: str) -> str:
    """
    :param path: e.g. "node1_id-[link1_id]->node2_id-[link2_id]->...-last_link_id->[last_node_id]"
    :return: e.g. "node1_id, node2_id, ..., last_node_id"
    """
    path = path.split("->")
    path = [node.split("-")[0] for node in path]
    return ",".join(path)


if __name__ == "__main__":
    app()
