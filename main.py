import os
import sys
import subprocess
from conf import FLOODNS_ROOT

# Add the floodns directory to the Python path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'floodns')))

from floodns.external.simulation.main import local_run_single_job, local_run_multiple_jobs, local_run_multiple_jobs_different_ring_sizes
from floodns.external.schemas.routing import Routing

def run_experiment():
    # Define the parameters for the experiment
    num_jobs = 1
    num_tors = 64
    n_cores = 0
    ring_size = 2
    routing = Routing.ECMP  # Use the appropriate routing algorithm
    seed = 0
    model = "BLOOM" # or "GPT_3" or "LLAMA2_70B"

    # Run the experiment (single job)
    proc = local_run_single_job(
        seed=seed,
        n_core_failures=n_cores,
        ring_size=ring_size,
        model=model,
        alg=routing
    )
    print(f"Simulation started with PID: {proc.pid}")
    proc.wait()
    print("stdout:")
    print(proc.stdout.read().decode("utf-8"))
    print("stderr:")
    print(proc.stderr.read().decode("utf-8"))

    num_jobs = 2
    # Run the experiment (multiple jobs, different ring sizes)
    proc = local_run_multiple_jobs_different_ring_sizes(
        seed=seed,
        n_jobs=num_jobs,
        n_core_failures=n_cores,
        alg=routing
    )
    proc.wait()
    print("stdout:")
    print(proc.stdout.read().decode("utf-8"))
    print("stderr:")
    print(proc.stderr.read().decode("utf-8"))

    num_jobs = 2
    # Run the experiment (multiple jobs, same ring size)
    print(f"Starting multiple jobs simulation with routing={routing}")
    expected_dir = os.path.join(
        FLOODNS_ROOT,
        "runs",
        f"seed_{seed}",
        f"concurrent_jobs_{num_jobs}",
        f"{n_cores}_core_failures",
        f"ring_size_{ring_size}",
        routing.value.lower()
    )
    expected_dir = os.path.abspath(expected_dir)
    print(f"Checking if directory exists: {expected_dir}")
    print(f"Directory exists: {os.path.exists(expected_dir)}")
    proc = local_run_multiple_jobs(
        seed=seed,
        n_jobs=num_jobs,
        ring_size=ring_size,
        n_core_failures=n_cores,
        alg=routing
    )
    print(f"Process started with PID: {proc.pid}")
    proc.wait()
    print("stdout:")
    print(proc.stdout.read().decode("utf-8"))
    print("stderr:")
    print(proc.stderr.read().decode("utf-8"))
    

if __name__ == "__main__":
    run_experiment()
