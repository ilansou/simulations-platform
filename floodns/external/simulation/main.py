import os
from subprocess import Popen, run, PIPE

from floodns.external.runs_generator.main import create_run_dir, create_run_dir_single_job
from floodns.external.schemas.distributed_training import DistributedTraining
from floodns.external.schemas.oversubscription import HostOversubscription
from floodns.external.schemas.routing import Routing
from typer import Typer
from conf import FLOODNS_ROOT

app = Typer()

@app.command()
def local_run_single_job(
    seed: int, n_core_failures: int, ring_size: int, model: str, alg: Routing
) -> Popen:
    os.chdir(FLOODNS_ROOT)

    os.makedirs(os.path.join(FLOODNS_ROOT, "runs"), exist_ok=True)
    run_dir = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_1",
        f"{n_core_failures}_core_failures",
        f"ring_size_{ring_size}",
        model,
        alg.value,
    )
    os.makedirs(os.path.dirname(run_dir), exist_ok=True)
    if not os.path.exists(run_dir):
        create_run_dir_single_job(
            num_tors=64,
            core_failures=n_core_failures,
            ring_size=ring_size,
            model_name=model,
            seed=seed,
        )
    jar_path = os.path.join(FLOODNS_ROOT, "floodns-basic-sim.jar")
    proc = Popen(["java", "-jar", jar_path, run_dir], stdout=PIPE, stderr=PIPE)
    return proc


@app.command()
def local_run_multiple_jobs(
    seed: int, n_jobs: int, ring_size: int, alg: Routing, n_core_failures: int
) -> Popen:
    assert n_jobs > 1
    os.chdir(FLOODNS_ROOT)

    os.makedirs(os.path.join(FLOODNS_ROOT, "runs"), exist_ok=True)
    run_dir = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{n_jobs}",
        f"{n_core_failures}_core_failures",
        f"ring_size_{ring_size}",
        alg.value,
    )
    os.makedirs(os.path.dirname(run_dir), exist_ok=True)
    if not os.path.exists(run_dir):
        create_run_dir(
            num_tors=64,
            num_jobs=n_jobs,
            core_failures=n_core_failures,
            ring_size=ring_size,
            routing=alg,
            seed=seed,
        )
    jar_path = os.path.join(FLOODNS_ROOT, "floodns-basic-sim.jar")
    proc = Popen(["java", "-jar", jar_path, run_dir], stdout=PIPE, stderr=PIPE)
    return proc


@app.command()
def local_run_multiple_jobs_different_ring_sizes(
    seed: int, n_jobs: int, n_core_failures: int, alg: Routing
) -> Popen:
    assert n_jobs > 1
    os.chdir(FLOODNS_ROOT)

    os.makedirs(os.path.join(FLOODNS_ROOT, "runs"), exist_ok=True)
    run_dir = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{n_jobs}",
        f"{n_core_failures}_core_failures",
        f"different_ring_sizes",
        alg.value,
    )
    os.makedirs(os.path.dirname(run_dir), exist_ok=True)
    if not os.path.exists(run_dir):
        create_run_dir(
            num_tors=64,
            num_jobs=n_jobs,
            core_failures=n_core_failures,
            routing=alg,
            seed=seed,
        )
    jar_path = os.path.join(FLOODNS_ROOT, "floodns-basic-sim.jar")
    proc = Popen(["java", "-jar", jar_path, run_dir], stdout=PIPE, stderr=PIPE)
    return proc


@app.command()
def local_run(
    seed: int, n_jobs: int, n_core_failures: int, ring_size: int, model: str, alg: Routing
) -> Popen:
    # single job
    # java -jar floodns-basic-sim.jar ./runs/seed_$(seed)/concurrent_jobs_1/$(core_failure)_core_failures/ring_size_$(ring_size)/$(model)/$(alg)
    # different ring sizes
    # java -jar floodns-basic-sim.jar ./runs/seed_$(seed)/concurrent_jobs_$(job)/$(core_failure)_core_failures/different_ring_sizes/$(alg)
    """
    :param seed: seed for the run
    :param n_jobs: number of concurrent jobs
    :param n_core_failures: number of core failures
    :param ring_size: ring size
    :param model: model to run (BLOOM, GPT_3, LLAMA2_70B)
    :param alg: routing algorithm (ecmp, mcvlc, edge_coloring, simulated_annealing, ilp_solver)
    """
    run_dir = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{n_jobs}",
        f"{n_core_failures}_core_failures",
    )
    if not os.path.exists(run_dir):
        create_run_dir(
            num_tors=num_tors,
            num_jobs=num_jobs,
            core_failures=n_cores,
            ring_size=ring_size,
            routing=routing,
            seed=seed,
        )
    jar_path = os.path.join(FLOODNS_ROOT, "floodns-basic-sim.jar")
    proc = Popen(["java", "-jar", jar_path, run_dir])
    return proc


if __name__ == "__main__":
    app()
