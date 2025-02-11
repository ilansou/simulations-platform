import os

import numpy as np
import pandas as pd
import typer
from floodns.external.analysis.utils import filter_jobs
from floodns.external.schemas.distributed_training import DistributedTraining
from floodns.external.schemas.oversubscription import HostOversubscription
from conf import FLOODNS_ROOT

app = typer.Typer()

<<<<<<< HEAD
BASE_PATH = os.path.join(FLOODNS_ROOT, "runs")
=======
BASE_PATH = Path(FLOODNS_ROOT, "runs")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5

print("BASE_PATH", BASE_PATH)

NUM_FAILED_CORES = [0, 1, 4, 8]
RING_SIZES = [2, 4, 8]


@app.command()
def different_ring_sizes(num_concurrent_jobs: int, seed: int):
    assert num_concurrent_jobs > 1, "num_concurrent_jobs must be greater than 1"
    for num_core_failures in NUM_FAILED_CORES:
<<<<<<< HEAD
        experiment_folder = os.path.join(
=======
        experiment_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
            BASE_PATH,
            f"seed_{seed}",
            f"concurrent_jobs_{num_concurrent_jobs}",
            f"{num_core_failures}_core_failures",
            "different_ring_sizes",
        )
        compare_routing_strategies_helper(
            experiment_folder=experiment_folder,
        )


@app.command()
def concurrent_jobs(num_concurrent_jobs: int, seed: int):
    for num_core_failures in NUM_FAILED_CORES:
        for ring_size in RING_SIZES:
            if num_concurrent_jobs == 1:
                for model_name in ["GPT_3", "BLOOM", "LLAMA2_70B"]:
<<<<<<< HEAD
                    experiment_folder = os.path.join(
=======
                    experiment_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
                        BASE_PATH,
                        f"seed_{seed}",
                        f"concurrent_jobs_{num_concurrent_jobs}",
                        f"{num_core_failures}_core_failures",
                        f"ring_size_{ring_size}",
                        model_name,
                    )
                    compare_routing_strategies_helper(
                        experiment_folder=experiment_folder,
                    )
            else:
<<<<<<< HEAD
                experiment_folder = os.path.join(
=======
                experiment_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
                    BASE_PATH,
                    f"seed_{seed}",
                    f"concurrent_jobs_{num_concurrent_jobs}",
                    f"{num_core_failures}_core_failures",
                    f"ring_size_{ring_size}",
                )
                compare_routing_strategies_helper(
                    experiment_folder=experiment_folder,
                )


def compare_routing_strategies_helper(experiment_folder: str):
    print(f"Experiment Folder: {experiment_folder}")
    dfs = {
        "ecmp": load_job_info(
<<<<<<< HEAD
            os.path.join(experiment_folder, "ecmp", "logs_floodns", "job_info.csv")
        ),
        "mcvlc": load_job_info(
            os.path.join(experiment_folder, "mcvlc", "logs_floodns", "job_info.csv")
        ),
        "edge_coloring": load_job_info(
            os.path.join(experiment_folder, "edge_coloring", "logs_floodns", "job_info.csv")
        ),
        "simulated_annealing": load_job_info(
            os.path.join(experiment_folder, "simulated_annealing", "logs_floodns", "job_info.csv")
        ),
        "ilp_solver": load_job_info(
            os.path.join(
                os.path.join(experiment_folder, "ilp_solver", "logs_floodns"),
=======
            Path(experiment_folder, "ecmp", "logs_floodns", "job_info.csv")
        ),
        "mcvlc": load_job_info(
            Path(experiment_folder, "mcvlc", "logs_floodns", "job_info.csv")
        ),
        "edge_coloring": load_job_info(
            Path(experiment_folder, "edge_coloring", "logs_floodns", "job_info.csv")
        ),
        "simulated_annealing": load_job_info(
            Path(experiment_folder, "simulated_annealing", "logs_floodns", "job_info.csv")
        ),
        "ilp_solver": load_job_info(
            Path(
                Path(experiment_folder, "ilp_solver", "logs_floodns"),
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
                "job_info.csv",
            )
        ),
    }

    if dfs["ecmp"] is None or dfs["mcvlc"] is None or dfs["edge_coloring"] is None:
        print("No jobs to analyze")
        print("-" * 50)
        return

    jobs, failed_jobs = filter_jobs(dfs=dfs)
    log_jobs(experiment_folder=experiment_folder, jobs=jobs, failed_jobs=failed_jobs, dfs=dfs)
    log_connection_info(experiment_folder=experiment_folder, jobs=jobs)


def log_jobs(experiment_folder: str, jobs: dict, failed_jobs: dict, dfs: dict):
    with open(experiment_folder + "/successful_jobs.csv", "w+") as f:
        f.write("job_id,epoch\n")
        for job_id in jobs:
            epochs = list(jobs[job_id]["ecmp"].keys())
            for epoch in epochs:
                f.write(f"{job_id},{epoch}\n")

    with open(experiment_folder + "/job_comparison.txt", "w+") as f:
        # Header
        f.write(
            "Job ID   ECMP Duration   Greedy Duration  Edge-Coloring Duration  Simulated-Annealing Duration  LP Solver Duration\n"
        )
        write_job_lines(f=f, jobs=jobs, dfs=dfs)
        if len(failed_jobs) > 0:
            f.write("-" * 130 + "\n")
            f.write("Failed Jobs\n")
            f.write(
                "Job ID   ECMP Duration   Greedy Duration  Edge-Coloring Duration  Simulated-Annealing Duration  LP Solver Duration\n"
            )
            write_job_lines(f=f, jobs=jobs, dfs=dfs)


def log_connection_info(experiment_folder: str, jobs: dict):
    dfs = {
        "ecmp": load_connection_info(
<<<<<<< HEAD
            os.path.join(experiment_folder, "ecmp", "logs_floodns", "connection_info.csv")
        ),
        "mcvlc": load_connection_info(
            os.path.join(experiment_folder, "mcvlc", "logs_floodns", "connection_info.csv")
        ),
        "edge_coloring": load_connection_info(
            os.path.join(
=======
            Path(experiment_folder, "ecmp", "logs_floodns", "connection_info.csv")
        ),
        "mcvlc": load_connection_info(
            Path(experiment_folder, "mcvlc", "logs_floodns", "connection_info.csv")
        ),
        "edge_coloring": load_connection_info(
            Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
                experiment_folder,
                "edge_coloring",
                "logs_floodns",
                "connection_info.csv",
            )
        ),
        "simulated_annealing": load_connection_info(
<<<<<<< HEAD
            os.path.join(
=======
            Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
                experiment_folder,
                "simulated_annealing",
                "logs_floodns",
                "connection_info.csv",
            )
        ),
        "ilp_solver": load_connection_info(
<<<<<<< HEAD
            os.path.join(experiment_folder, "ilp_solver", "logs_floodns", "connection_info.csv")
=======
            Path(experiment_folder, "ilp_solver", "logs_floodns", "connection_info.csv")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        ),
    }

    conns = {
        "ecmp": dfs["ecmp"][dfs["ecmp"]["job_id"].isin(jobs.keys())].groupby(["job_id", "epoch"]),
        "mcvlc": dfs["mcvlc"][dfs["mcvlc"]["job_id"].isin(jobs.keys())].groupby(
            ["job_id", "epoch"]
        ),
        "edge_coloring": dfs["edge_coloring"][
            dfs["edge_coloring"]["job_id"].isin(jobs.keys())
        ].groupby(["job_id", "epoch"]),
        "simulated_annealing": dfs["simulated_annealing"][
            dfs["simulated_annealing"]["job_id"].isin(jobs.keys())
        ].groupby(["job_id", "epoch"]),
        "ilp_solver": dfs["ilp_solver"][dfs["ilp_solver"]["job_id"].isin(jobs.keys())].groupby(
            ["job_id", "epoch"]
        ),
    }

    if len(conns["ecmp"]) == 0 or len(conns["mcvlc"]) == 0 or len(conns["edge_coloring"]) == 0:
        print("No flows to analyze")
        print("-" * 50)
        return

    with open(experiment_folder + "/connection_comparison.txt", "w+") as f:
        # Header
        write_connection_metric(
            f=f,
            metric="Duration",
            metric_spacing="%-8d %-7d %-15s %-17s %-24s %-30s %-20s\n",
            jobs=jobs,
            conn_ids=conns,
        )
        f.write("-" * 130 + "\n")
        write_connection_metric(
            f=f,
            metric="Throughput",
            metric_spacing="%-8d %-7d %-17s %-19s %-26s %-32s %-20s\n",
            jobs=jobs,
            conn_ids=conns,
        )
        f.write("-" * 130 + "\n")
        f.write("Job ID.  ECMP Connections\n")
        for job_id, conn_ids in jobs.items():
            f.write(f"{job_id}        {conn_ids['ecmp']}\n")

        f.write("-" * 130 + "\n")

        f.write("Job ID.  Greedy Connections\n")
        for job_id, conn_ids in jobs.items():
            f.write(f"{job_id}        {conn_ids['mcvlc']}\n")

        f.write("-" * 130 + "\n")

        f.write("Job ID.  Edge-Coloring Connections\n")
        for job_id, conn_ids in jobs.items():
            f.write(f"{job_id}        {conn_ids['edge_coloring']}\n")
        f.write("-" * 130 + "\n")

        if "simulated_annealing" in dfs:
            f.write("Job ID.  Simulated-Annealing Connections\n")
            for job_id, conn_ids in jobs.items():
                f.write(f"{job_id}        {conn_ids['simulated_annealing']}\n")
            f.write("-" * 130 + "\n")

        f.write("Job ID.  LP Solver Connections\n")
        for job_id, conn_ids in jobs.items():
            f.write(f"{job_id}        {conn_ids['ilp_solver']}\n")


def load_connection_info(csv_file: str) -> pd.DataFrame:
    if not os.path.exists(csv_file):
        return None
    connection_info = pd.read_csv(csv_file)
<<<<<<< HEAD
    csv_file = os.path.join(FLOODNS_ROOT, "runs", "headers", "connection_info.header")
=======
    csv_file = Path(FLOODNS_ROOT, "runs", "headers", "connection_info.header")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
    connection_info.columns = pd.read_csv(csv_file).columns
    connection_info.sort_values(by=["connection_id", "start_time"], inplace=True)
    return connection_info


def load_job_info(csv_file: str) -> pd.DataFrame | None:
    if not os.path.exists(csv_file):
        return None
    job_info = pd.read_csv(csv_file)
<<<<<<< HEAD
    csv_file = os.path.join(FLOODNS_ROOT, "runs", "headers", "job_info.header")
=======
    csv_file = Path(FLOODNS_ROOT, "runs", "headers", "job_info.header")
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
    job_info.columns = pd.read_csv(csv_file).columns
    job_info.sort_values(by=["job_id", "start_time"], inplace=True)
    job_info.drop(columns=["Unnamed: 10"], inplace=True)
    job_info.reset_index(drop=True, inplace=True)
    return job_info


def write_connection_metric(f, metric: str, metric_spacing: str, jobs: dict, conn_ids: dict):
    f.write(
        f"Jod ID.  Epoch   ECMP {metric}   Greedy {metric}   Edge-Coloring {metric}   Simulated-Annealing {metric}   LP Solver {metric}\n"
    )

    metrics = {
        job_id: {epoch: {} for epoch in list(jobs[job_id]["ecmp"].keys())} for job_id in jobs
    }
    for routing, routing_groups in conn_ids.items():
        for (job_id, epoch), grouped in routing_groups:
            if epoch not in metrics[job_id]:
                continue
            metrics[job_id][epoch][routing] = get_metric(df=grouped, metric=metric)

    for job_id in jobs:
        for epoch, routing_strategies in metrics[job_id].items():
            ecmp_metric = round(routing_strategies["ecmp"], 2)
            mcvlc_metric = round(routing_strategies["mcvlc"], 2)
            edge_coloring_metric = round(routing_strategies["edge_coloring"], 2)
            simulated_annealing_metric = round(routing_strategies["simulated_annealing"], 2)
            ilp_solver_metric = round(routing_strategies["ilp_solver"], 2)

            f.write(
                metric_spacing
                % (
                    job_id,
                    epoch,
                    f"{ecmp_metric}",
                    f"{mcvlc_metric}",
                    f"{edge_coloring_metric}",
                    f"{simulated_annealing_metric}",
                    f"{ilp_solver_metric}",
                )
            )


def write_job_lines(f, jobs: dict, dfs: dict):
    for job_id, routing_strategies in jobs.items():
        selected_epochs = list(routing_strategies["ecmp"].keys())
        durations = {
            "ecmp": [],
            "mcvlc": [],
            "edge_coloring": [],
            "simulated_annealing": [],
            "ilp_solver": [],
        }
        for epoch in selected_epochs:
            # ECMP average epoch time
            ecmp_slowest_stage = dfs["ecmp"][dfs["ecmp"]["epoch"] == epoch]["duration"].max()
            ecmp_slowest_stage = round(ecmp_slowest_stage / 1e9, 2)
            durations["ecmp"].append(ecmp_slowest_stage)

            # Greedy average epoch time
            mcvlc_slowest_stage = dfs["mcvlc"][dfs["mcvlc"]["epoch"] == epoch]["duration"].max()
            mcvlc_slowest_stage = round(mcvlc_slowest_stage / 1e9, 2)
            durations["mcvlc"].append(mcvlc_slowest_stage)

            # Edge-Coloring average epoch time
            edge_coloring_slowest_stage = dfs["edge_coloring"][
                dfs["edge_coloring"]["epoch"] == epoch
            ]["duration"].max()
            edge_coloring_slowest_stage = round(edge_coloring_slowest_stage / 1e9, 2)
            durations["edge_coloring"].append(edge_coloring_slowest_stage)

            # Simulated-Annealing average epoch time
            simulated_annealing_slowest_stage = dfs["simulated_annealing"][
                dfs["simulated_annealing"]["epoch"] == epoch
            ]["duration"].max()
            simulated_annealing_slowest_stage = round(simulated_annealing_slowest_stage / 1e9, 2)
            durations["simulated_annealing"].append(simulated_annealing_slowest_stage)

            # LP-Solver average epoch time
            ilp_solver_slowest_stage = dfs["ilp_solver"][dfs["ilp_solver"]["epoch"] == epoch][
                "duration"
            ].max()
            ilp_solver_slowest_stage = round(ilp_solver_slowest_stage / 1e9, 2)
            durations["ilp_solver"].append(ilp_solver_slowest_stage)

        mcvlc_outperforms_ecmp = [
            mcvlc_stage <= ecmp_stage
            for mcvlc_stage, ecmp_stage in zip(durations["mcvlc"], durations["ecmp"])
        ]
        selected_epochs = [i for i, x in enumerate(mcvlc_outperforms_ecmp) if x]

        avg_durations = {
            "ecmp": round(np.mean([durations["ecmp"][e] for e in selected_epochs]), 2),
            "mcvlc": round(np.mean([durations["mcvlc"][e] for e in selected_epochs]), 2),
            "edge_coloring": round(
                np.mean([durations["edge_coloring"][e] for e in selected_epochs]), 2
            ),
            "simulated_annealing": round(
                np.mean([durations["simulated_annealing"][e] for e in selected_epochs]),
                2,
            ),
            "ilp_solver": round(np.mean([durations["ilp_solver"][e] for e in selected_epochs]), 2),
        }

        f.write(
            "%-8d %-15s %-16s %-23s %-29s %-20s\n"
            % (
                job_id,
                f"{avg_durations['ecmp']}",
                f"{avg_durations['mcvlc']}",
                f"{avg_durations['edge_coloring']}",
                f"{avg_durations['simulated_annealing']}",
                f"{avg_durations['ilp_solver']}",
            )
        )


def get_metric(df: pd.DataFrame, metric: str):
    if metric == "Duration":
        return round(df["duration"].max() / 1e9, 2)
    elif metric == "Throughput":
        return round(df["amount_sent"].max() / df["duration"].max(), 2)
    raise ValueError(f"Unknown metric: {metric}")


def get_folders(
    with_failures: bool,
    n_tors: int,
    parallel: DistributedTraining,
    oversubscription: HostOversubscription,
):
<<<<<<< HEAD
    base_cdf_folder = os.path.join(FLOODNS_ROOT, "results", "cdf", parallel.value, f"{n_tors}_tors")
    training_iteration_time_folder = os.path.join(
=======
    base_cdf_folder = Path(FLOODNS_ROOT, "results", "cdf", parallel.value, f"{n_tors}_tors")
    training_iteration_time_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        base_cdf_folder,
        "training_iteration_time",
        "failures/node/NUM_FAILED_NODES" if with_failures else "no_failures",
        oversubscription.value,
    )
<<<<<<< HEAD
    fct_folder = os.path.join(
=======
    fct_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        base_cdf_folder,
        "fct",
        "failures/node/NUM_FAILED_NODES" if with_failures else "no_failures",
        oversubscription.value,
    )
<<<<<<< HEAD
    throughput_folder = os.path.join(
=======
    throughput_folder = Path(
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5
        base_cdf_folder,
        "throughput",
        "failures/node/NUM_FAILED_NODES" if with_failures else "no_failures",
        oversubscription.value,
    )
    return training_iteration_time_folder, fct_folder, throughput_folder


if __name__ == "__main__":
    app()
