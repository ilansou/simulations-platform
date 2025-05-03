import os
import json
from pathlib import Path
from conf import FLOODNS_ROOT
from floodns.external.simulation.main import local_run_single_job, local_run_multiple_jobs, local_run_multiple_jobs_different_ring_sizes
from floodns.external.schemas.routing import Routing

print("In main.py - FLOODNS_ROOT:", FLOODNS_ROOT)
print("FLOODNS_ROOT exists:", os.path.exists(FLOODNS_ROOT))

def load_configurations(config_file="configurations.json"):
    """
    Load configurations from a JSON file.
    
    Args:
        config_file (str): Path to the JSON file containing configurations
    
    Returns:
        list: List of configuration dictionaries
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        configurations = json.load(f)
    
    print(f"Loaded {len(configurations)} configurations from {config_path}")
    return configurations

def run_experiment(num_jobs, seed, n_core_failures, ring_size, model, routing):
    """
    Run experiment based on configuration parameters.
    
    Args:
        num_jobs (int): Number of jobs
        n_core_failures (int): Number of core failures
        ring_size (int): Ring size (-1 for different ring sizes)
        routing (str): Routing algorithm
        seed (int): Random seed
        model (str or None): Model name for single job
    """
    success = True
    try:
        routing_enum = Routing[routing]
    except KeyError:
        print(f"Invalid routing algorithm: {routing}")
        return False

    # Ensure we're using the correct FLOODNS_ROOT
    print(f"FLOODNS_ROOT in run_experiment: {FLOODNS_ROOT}")

    if num_jobs == 1:
        try:
            print(f"Running single job experiment: jobs={num_jobs}, cores={n_core_failures}, ring_size={ring_size}, routing={routing}, seed={seed}, model={model}")
            proc = local_run_single_job(
                seed=seed,
                n_core_failures=n_core_failures,
                ring_size=ring_size,
                model=model,
                alg=routing_enum
            )
            print(f"Single job simulation started with PID: {proc.pid}")
            stdout, stderr = proc.communicate()
            print("stdout:")
            print(stdout.decode("utf-8") if stdout else "No stdout")
            print("stderr:")
            print(stderr.decode("utf-8") if stderr else "No stderr")
            
            if proc.returncode != 0:
                print(f"Single job experiment failed with return code {proc.returncode}")
                success = False 
                
        except Exception as e:
            print(f"Error running single job experiment: {str(e)}")
            success = False

    if num_jobs > 1 and ring_size == -1:
        try:
            print(f"Running multiple jobs experiment (different ring sizes): jobs={num_jobs}, cores={n_core_failures}, routing={routing}, seed={seed}")
            proc = local_run_multiple_jobs_different_ring_sizes(
                seed=seed,
                n_jobs=num_jobs,
                n_core_failures=n_core_failures,
                alg=routing_enum
            )
            print(f"Multiple jobs (different ring sizes) simulation started with PID: {proc.pid}")
            stdout, stderr = proc.communicate()
            print("stdout:")
            print(stdout.decode("utf-8") if stdout else "No stdout")
            print("stderr:")
            print(stderr.decode("utf-8") if stderr else "No stderr")
            
            if proc.returncode != 0:
                print(f"Multiple jobs (different ring sizes) experiment failed with return code {proc.returncode}")
                success = False

        except Exception as e:
            print(f"Error running multiple jobs (different ring sizes) experiment: {str(e)}")
            success = False

    if num_jobs > 1 and ring_size != -1:
        try:
            print(f"Running multiple jobs experiment (same ring size): jobs={num_jobs}, cores={n_core_failures}, ring_size={ring_size}, routing={routing}, seed={seed}")
            proc = local_run_multiple_jobs(
                seed=seed,
                n_jobs=num_jobs,
                ring_size=ring_size,
                n_core_failures=n_core_failures,
                alg=routing_enum
            )
            print(f"Multiple jobs (same ring size) simulation started with PID: {proc.pid}")
            stdout, stderr = proc.communicate()
            print("stdout:")
            print(stdout.decode("utf-8") if stdout else "No stdout")
            print("stderr:")
            print(stderr.decode("utf-8") if stderr else "No stderr")
            
            if proc.returncode != 0:
                print(f"Multiple jobs (same ring size) experiment failed with return code {proc.returncode}")
                success = False
                
        except Exception as e:
            print(f"Error running multiple jobs (same ring size) experiment: {str(e)}")
            success = False

    return success

def main():
    try:
        configurations = load_configurations()
    except Exception as e:
        print(f"Failed to load configurations: {str(e)}")
        return

    successful_runs = 0
    failed_runs = 0
    max_runs = 5
    actual_configurations = configurations[:max_runs]
    
    for i, config in enumerate(actual_configurations):
        print(f"\nRunning experiment {i+1}/{len(actual_configurations)}")
        ring_size_str = "different ring sizes" if config["ring_size"] == -1 else f"ring size {config['ring_size']}"
        model_str = f", model: {config['model']}" if config["model"] else ""
        print(f"Config: {config['num_jobs']} jobs, {config['n_core_failures']} core failures, {ring_size_str}, {config['routing']}, seed {config['seed']}{model_str}")
        
        success = run_experiment(
            num_jobs=config["num_jobs"],
            n_core_failures=config["n_core_failures"],
            ring_size=config["ring_size"],
            routing=config["routing"],
            seed=config["seed"],
            model=config["model"]
        )
        
        if success:
            successful_runs += 1
            print(f"Experiment {i+1} completed successfully")
        else:
            failed_runs += 1
            print(f"Experiment {i+1} failed")
    
    print(f"\nExperiment Summary:")
    print(f"Total experiments run: {len(actual_configurations)}")
    print(f"Successful runs: {successful_runs}")
    print(f"Failed runs: {failed_runs}")

if __name__ == "__main__":
    main()