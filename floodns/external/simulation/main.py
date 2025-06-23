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
import logging

# Set up logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Typer()

def handle_pytorch_path_error():
    """
    Patch to handle the PyTorch __path__._path error by attempting to import PyTorch 
    in a try-except block before running simulations.
    """
    try:
        import torch
        # Avoid the specific error by accessing the module directly
        if hasattr(torch, 'classes') and hasattr(torch.classes, '__path__'):
            # Replace the problematic attribute with a normal list if needed
            if not isinstance(torch.classes.__path__, list):
                torch.classes.__path__ = []
        return True
    except Exception as e:
        return False
    

@app.command()
# if number of jobs is 1
def local_run_single_job(seed: int, n_core_failures: int, ring_size: int | str, model: str, alg: Routing):

    # Try to handle PyTorch error before running simulation
    handle_pytorch_path_error()

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

    jar_path = Path(FLOODNS_ROOT, "floodns-basic-sim.jar")

    # Run java -jar
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    # Return the process code (or you can return the proc itself)
    return proc


@app.command()
# if number of jobs > 1 but ring size is 2, 4, 8
def local_run_multiple_jobs(
    seed: int, n_jobs: int, ring_size: int | str, alg: Routing, n_core_failures: int
) -> Popen:
    assert n_jobs > 1
    assert isinstance(ring_size, int), "local_run_multiple_jobs expects an integer ring_size"

    # Try to handle PyTorch error before running simulation
    handle_pytorch_path_error()

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

    # Run java -jar and wait for it to complete
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    return proc


@app.command()
def local_run_multiple_jobs_different_ring_size(
    seed: int, n_jobs: int, n_core_failures: int, alg: Routing
) -> Popen:
    assert n_jobs > 1

    # Try to handle PyTorch error before running simulation
    handle_pytorch_path_error()

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

    # Run java -jar and wait for it to complete
    proc = Popen(["java", "-jar", str(jar_path), str(run_dir)], stdout=PIPE, stderr=PIPE)
    stdout_data, stderr_data = proc.communicate()

    return proc


if __name__ == "__main__":
    app()