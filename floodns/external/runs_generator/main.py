import os
from os import makedirs
from pathlib import Path
from floodns.external.schemas.routing import Routing
from typer import Typer
from conf import FLOODNS_ROOT
app = Typer()

NUM_CORE_FAILURES = [0, 1, 4, 8]
RING_SIZES = [2, 4, 8]

@app.command()
def create_run_dir(
    num_tors: int,
    num_jobs: int,
    core_failures: int,
    routing: Routing,
    seed: int,
    ring_size: int | None = None,
):
    """
    Create a directory for a run with the given parameters
    :param num_tors: Number of ToR switches
    :param num_jobs: Number of concurrent jobs to run
    :param core_failures: Number of failed cores
    :param ring_size: Ring size of data parallelism
    :param routing: Routing algorithm
    :param seed: Seed for random
    """
    job_dir = Path(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_jobs}",
        f"{core_failures}_core_failures",
    )
    traffic_pairs_dir = Path(
        FLOODNS_ROOT,
        "traffic_pairs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_jobs}",
    )
    print("job_dir", job_dir)
    print ("traffic_pairs_dir", traffic_pairs_dir)
    if ring_size is None:
        job_dir = Path(job_dir, "different_ring_sizes")
        traffic_pairs_dir = Path(traffic_pairs_dir, "different_ring_sizes")
    else:
        job_dir = Path(job_dir, f"ring_size_{ring_size}")
        traffic_pairs_dir = Path(traffic_pairs_dir, f"ring_size_{ring_size}")

    job_dir = Path(job_dir, routing.value)
    if not os.path.exists(job_dir):
        makedirs(job_dir, exist_ok=True)

    create_files(
        runs_dir=job_dir,
        routing=routing,
        core_failures=core_failures,
        traffic_pairs_dir=traffic_pairs_dir,
        num_tors=num_tors,
    )


@app.command()
def create_run_dir_single_job(
    num_tors: int, core_failures: int, ring_size: int, model_name: str, seed: int
):
    """
    Create a directory for a run with the given parameters
    :param num_tors: Number of ToR switches
    :param core_failures: Number of failed cores
    :param ring_size: Ring size of data parallelism
    :param model_name: LLM model
    :param seed: Seed for random
    """
    for routing in Routing:
        job_dir = Path(
            FLOODNS_ROOT,
            "runs",
            f"seed_{seed}",
            "concurrent_jobs_1",
            f"{core_failures}_core_failures",
            f"ring_size_{ring_size}",
            model_name,
            routing.value,
        )
        if not os.path.exists(job_dir):
            makedirs(job_dir, exist_ok=True)
        traffic_pairs_dir = Path(
            FLOODNS_ROOT,
            "traffic_pairs",
            f"seed_{seed}",
            "concurrent_jobs_1",
            f"ring_size_{ring_size}",
            model_name,
        )
        create_files(
            runs_dir=job_dir,
            routing=routing,
            core_failures=core_failures,
            traffic_pairs_dir=traffic_pairs_dir,
            num_tors=num_tors,
        )


@app.command()
def create_concurrent_jobs_dir(num_tors: int, num_concurrent_jobs: int, seed: int):
    for routing in Routing:
        for core_failures in NUM_CORE_FAILURES:
            for ring_size in RING_SIZES:
                if num_concurrent_jobs == 1:
                    for model_name in ["GPT_3", "BLOOM", "LLAMA2_70B"]:
                        create_run_dir_single_job(
                            num_tors=num_tors,
                            core_failures=core_failures,
                            ring_size=ring_size,
                            model_name=model_name,
                            seed=seed,
                        )
                else:
                    create_run_dir(
                        num_tors=num_tors,
                        num_jobs=num_concurrent_jobs,
                        core_failures=core_failures,
                        ring_size=ring_size,
                        routing=routing,
                        seed=seed,
                    )


@app.command()
def create_concurrent_jobs_different_ring_sizes(num_tors: int, num_concurrent_jobs: int, seed: int):
    for routing in Routing:
        for core_failures in NUM_CORE_FAILURES:
            create_run_dir(
                num_tors=num_tors,
                num_jobs=num_concurrent_jobs,
                core_failures=core_failures,
                routing=routing,
                seed=seed,
            )


def create_files(
    runs_dir: str,
    routing: Routing,
    core_failures: int,
    traffic_pairs_dir: str,
    num_tors: int,
):
    create_config_floodns(
        root=runs_dir,
        routing=routing,
        core_failures=core_failures,
        traffic_pairs_dir=traffic_pairs_dir,
    )
    create_2_layer_topology(root=runs_dir, num_tors=num_tors)
    if os.path.exists(Path(runs_dir, "schedule.csv")):
        return
    with open(Path(runs_dir, "schedule.csv"), "w") as f:
        f.write("0,5,8,100000000,0,,\n")


def create_config_floodns(
    root: dir,
    routing: Routing,
    core_failures: int,
    traffic_pairs_dir: str,
):
    config_file = Path(root, "config.properties")
    with open(config_file, "w") as f:
        f.write("simulation_end_time_ns=604800000000000\n")
        f.write("simulation_seed=1234\n")
        f.write("filename_topology=topology.properties\n")
        f.write("filename_schedule=schedule.csv\n")
        f.write(f"job_base_dir_schedule={traffic_pairs_dir}\n")
        f.write(f"routing_strategy={routing.value}\n")
        f.write(f"num_failed_nodes={core_failures}\n")
        

def create_2_layer_topology(root: dir, num_tors: int):
    topology_file = Path(root, "topology.properties")
    radix = num_tors // 2
    num_cores = radix
    num_hosts_under_tor = radix
    num_hosts = num_tors * num_hosts_under_tor
    num_switches = num_tors + num_cores
    num_nodes = num_switches + num_hosts
    num_edges = num_tors * (num_cores + num_hosts_under_tor)
    undirected_edges = build_2_layer_undirected_edges(
        num_tors=num_tors, num_cores=num_cores, num_hosts=num_hosts, radix=radix
    )

    with open(topology_file, "w") as f:
        f.write(f"num_nodes={num_nodes}\n")
        f.write(f"num_undirected_edges={num_edges}\n")
        f.write(f"switches=incl_range(0,{num_switches - 1})\n")
        f.write(f"switches_which_are_tors=incl_range(0,{num_tors - 1})\n")
        f.write(f"cores=incl_range({num_tors},{num_switches - 1})\n")
        f.write(f"servers=incl_range({num_switches},{num_switches + num_hosts - 1})\n")
        f.write(f"undirected_edges=incl_range({undirected_edges})\n")
        f.write("link_data_rate_bit_per_ns=100\n")


def build_2_layer_undirected_edges(num_tors: int, num_cores: int, num_hosts: int, radix: int):
    start_tor, end_tor = 0, num_tors - 1
    start_core, end_core = num_tors, num_tors + num_cores - 1
    start_server, end_server = num_tors + num_cores, num_tors + num_cores + num_hosts - 1
    tor_core_edges = f"{start_tor}:{end_tor}-{start_core}:{end_core}"
    server_tor_edges = []
    tor = start_tor
    for server in range(start_server, end_server + 1, radix):
        server_tor_edges.append(f"{server}:{server + radix - 1}-{tor}")
        tor += 1
    return f"{tor_core_edges},{','.join(server_tor_edges)}"


if __name__ == "__main__":
    app()
