from typing import Dict

import pandas as pd


def filter_jobs(dfs: Dict[str, pd.DataFrame]):
    job_ids = set(dfs["ecmp"]["job_id"].unique()).intersection(set(dfs["mcvlc"]["job_id"].unique()))
    successful_jobs = {}
    failed_jobs = {}
    for job_id in job_ids:
        # Get number of stages
        ecmp_num_stages = int(dfs["ecmp"]["stage"].unique().max()) + 1
        mcvlc_num_stages = int(dfs["mcvlc"]["stage"].unique().max()) + 1
        assert ecmp_num_stages == mcvlc_num_stages
        # Get number of epochs
        ecmp_num_epochs = int(dfs["ecmp"]["epoch"].unique().max())
        mcvlc_num_epochs = int(dfs["mcvlc"]["epoch"].unique().max())
        num_epochs = min(ecmp_num_epochs, mcvlc_num_epochs)

        ecmp_durations = []
        mcvlc_durations = []
        for i in range(1, num_epochs + 1):
            # ECMP average epoch time
            ecmp_slowest_stage = dfs["ecmp"][dfs["ecmp"]["epoch"] == i]["duration"].max()
            ecmp_slowest_stage = round(ecmp_slowest_stage / 1e9, 2)
            ecmp_durations.append(ecmp_slowest_stage)

            # Greedy average epoch time
            mcvlc_slowest_stage = dfs["mcvlc"][dfs["mcvlc"]["epoch"] == i]["duration"].max()
            mcvlc_slowest_stage = round(mcvlc_slowest_stage / 1e9, 2)
            mcvlc_durations.append(mcvlc_slowest_stage)

        mcvlc_outperforms_ecmp = [
            mcvlc_stage <= ecmp_stage
            for mcvlc_stage, ecmp_stage in zip(mcvlc_durations, ecmp_durations)
        ]
        selected_epochs = [i for i, x in enumerate(mcvlc_outperforms_ecmp) if x]

        # Keep only jobs that have similar average epoch time (within 0.5 seconds)
        successful = len(selected_epochs) > 0

        insert_job(
            jobs=successful_jobs if successful else failed_jobs,
            job_id=job_id,
            ecmp=dfs["ecmp"][dfs["ecmp"]["job_id"] == job_id],
            mcvlc=dfs["mcvlc"][dfs["mcvlc"]["job_id"] == job_id],
            edge_coloring=dfs["edge_coloring"][dfs["edge_coloring"]["job_id"] == job_id],
            simulated_annealing=dfs["simulated_annealing"][
                dfs["simulated_annealing"]["job_id"] == job_id
            ],
            ilp_solver=dfs["ilp_solver"][dfs["ilp_solver"]["job_id"] == job_id],
            selected_epochs=selected_epochs,
        )

    return successful_jobs, failed_jobs


def insert_job(
    jobs: dict,
    job_id: int,
    ecmp: pd.Series,
    mcvlc: pd.Series,
    edge_coloring: pd.Series,
    simulated_annealing: pd.Series,
    ilp_solver: pd.Series,
    selected_epochs: list,
):
    jobs[job_id] = {
        "ecmp": {},
        "mcvlc": {},
        "edge_coloring": {},
        "simulated_annealing": {},
        "ilp_solver": {},
    }
    for epoch in selected_epochs:
        jobs[job_id]["ecmp"][epoch] = [
            [int(conn_id) for conn_id in conn_ids.split(";")]
            for conn_ids in ecmp[ecmp["epoch"] == epoch]["conn_ids"].tolist()
        ]

        jobs[job_id]["mcvlc"][epoch] = [
            [int(conn_id) for conn_id in conn_ids.split(";")]
            for conn_ids in mcvlc[mcvlc["epoch"] == epoch]["conn_ids"].tolist()
        ]

        jobs[job_id]["edge_coloring"][epoch] = [
            [int(conn_id) for conn_id in conn_ids.split(";")]
            for conn_ids in edge_coloring[edge_coloring["epoch"] == epoch]["conn_ids"].tolist()
        ]

        jobs[job_id]["simulated_annealing"][epoch] = [
            [int(conn_id) for conn_id in conn_ids.split(";")]
            for conn_ids in simulated_annealing[simulated_annealing["epoch"] == epoch][
                "conn_ids"
            ].tolist()
        ]

        jobs[job_id]["ilp_solver"][epoch] = [
            [int(conn_id) for conn_id in conn_ids.split(";")]
            for conn_ids in ilp_solver[ilp_solver["epoch"] == epoch]["conn_ids"].tolist()
        ]
