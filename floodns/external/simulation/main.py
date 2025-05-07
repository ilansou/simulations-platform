import os
from subprocess import Popen, run, PIPE
from pathlib import Path
from floodns.external.runs_generator.main import create_run_dir, create_run_dir_single_job
from floodns.external.jobs_generator.main import (
    gen_ddp_pairs,
    gen_single_job_ddp_pairs,
    gen_ddp_pairs_different_sizes,
)
from floodns.external.schemas.accelerators import Accelerators
from floodns.external.schemas.distributed_training import DistributedTraining
from floodns.external.schemas.oversubscription import HostOversubscription
from floodns.external.schemas.routing import Routing
from typer import Typer
from conf import FLOODNS_ROOT

app = Typer()


@app.command()
# if number of jobs is 1
def local_run_single_job(seed: int, n_core_failures: int, ring_size: int | str, model: str, alg: Routing):

    print(
        f"=== local_run_single_job called with seed={seed}, n_core_failures={n_core_failures}, "
        f"ring_size={ring_size}, model={model}, alg={alg}"
    )

    # Generate the necessary files
    create_run_dir_single_job(
        num_tors=64,
        core_failures=n_core_failures,
        ring_size=ring_size,
        model_name=model,
        seed=seed,
    )
    gen_single_job_ddp_pairs(
        accelerator_name=Accelerators.A100.name,
        model_name=model,
        n_tors=64,
        data_parallelism_dim=ring_size,
        seed=seed,
    )

    # Determine the ring size part of the path
    ring_size_path_part = "different_ring_size" if ring_size == "different" else f"ring_size_{ring_size}"

    run_dir = Path(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        "concurrent_jobs_1",
        f"{n_core_failures}_core_failures",
        ring_size_path_part,  # Use the determined path part
        model,
        alg.value,
    )

    print(f"Run directory: {run_dir}")

    jar_path = Path(FLOODNS_ROOT, "floodns-basic-sim.jar")
    if not jar_path.exists():
        print(f"!!! JAR file not found at {jar_path}")
    else:
        print(f"JAR file found at {jar_path}")

    # Run java -jar
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    print("=== local_run_single_job STDOUT ===")
    print(stdout_data.decode("utf-8", errors="replace"))
    print("=== local_run_single_job STDERR ===")
    print(stderr_data.decode("utf-8", errors="replace"))
    print(f"=== local_run_single_job return code: {proc.returncode}")

    # Return the process code (or you can return the proc itself)
    return proc


@app.command()
# if number of jobs > 1 but ring size is 2, 4, 8
def local_run_multiple_jobs(
    seed: int, n_jobs: int, ring_size: int | str, alg: Routing, n_core_failures: int
) -> Popen:
    assert n_jobs > 1
    assert isinstance(ring_size, int), "local_run_multiple_jobs expects an integer ring_size"

    print(
        f"=== local_run_multiple_jobs called with seed={seed}, n_jobs={n_jobs}, "
        f"ring_size={ring_size}, alg={alg}, n_core_failures={n_core_failures}"
    )

    create_run_dir(
        num_tors=64,
        num_jobs=n_jobs,
        core_failures=n_core_failures,
        ring_size=ring_size,
        routing=alg,
        seed=seed,
    )
    gen_ddp_pairs(
        accelerator_name=Accelerators.A100.name,
        n_tors=64,
        num_concurrent_jobs=n_jobs,
        data_parallelism_dim=ring_size,
        seed=seed,
    )

    run_dir = Path(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{n_jobs}",
        f"{n_core_failures}_core_failures",
        f"ring_size_{ring_size}",
        alg.value,
    )

    jar_path = Path(FLOODNS_ROOT, "floodns-basic-sim.jar")
    if not jar_path.exists():
        print(f"!!! JAR file not found at {jar_path}")
    else:
        print(f"JAR file found at {jar_path}")

    # Run java -jar and wait for it to complete
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    print("=== local_run_multiple_jobs STDOUT ===")
    print(stdout_data.decode("utf-8", errors="replace"))
    print("=== local_run_multiple_jobs STDERR ===")
    print(stderr_data.decode("utf-8", errors="replace"))
    print(f"=== local_run_multiple_jobs return code: {proc.returncode}")

    return proc


@app.command()
def local_run_multiple_jobs_different_ring_size(
    seed: int, n_jobs: int, n_core_failures: int, alg: Routing
) -> Popen:
    assert n_jobs > 1

    print(
        f"=== local_run_multiple_jobs_different_ring_size called with seed={seed}, "
        f"n_jobs={n_jobs}, n_core_failures={n_core_failures}, alg={alg}"
    )

    create_run_dir(
        num_tors=64,
        num_jobs=n_jobs,
        core_failures=n_core_failures,
        routing=alg,
        seed=seed,
        ring_size="different"
    )
    gen_ddp_pairs_different_sizes(
        accelerator_name=Accelerators.A100.name,
        n_tors=64,
        num_concurrent_jobs=n_jobs,
        seed=seed,
    )
    # Define the run_dir properly
    run_dir = Path(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{n_jobs}",
        f"{n_core_failures}_core_failures",
        "different_ring_size",
        alg.value,
    )

    jar_path = Path(FLOODNS_ROOT, "floodns-basic-sim.jar")
    if not jar_path.exists():
        print(f"!!! JAR file not found at {jar_path}")
    else:
        print(f"JAR file found at {jar_path}")

    # Run java -jar and wait for it to complete
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    print("=== local_run_multiple_jobs_different_ring_size STDOUT ===")
    print(stdout_data.decode("utf-8", errors="replace"))
    print("=== local_run_multiple_jobs_different_ring_size STDERR ===")
    print(stderr_data.decode("utf-8", errors="replace"))
    print(f"=== local_run_multiple_jobs_different_ring_size return code: {proc.returncode}")

    return proc


if __name__ == "__main__":
    app()