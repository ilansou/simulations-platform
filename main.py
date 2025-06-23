import os
import json
from pathlib import Path
from conf import FLOODNS_ROOT
from floodns.external.simulation.main import local_run_single_job, local_run_multiple_jobs, local_run_multiple_jobs_different_ring_size
from floodns.external.schemas.routing import Routing

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
    
    return configurations

def run_experiment(num_jobs, seed, n_core_failures, ring_size: int | str, model, routing):
    """
    Run experiment based on configuration parameters.
    
    Args:
        num_jobs (int): Number of jobs
        n_core_failures (int): Number of core failures
        ring_size (int or str): Ring size 
        routing (str): Routing algorithm
        seed (int): Random seed
        model (str or None): Model name for single job
    """
    success = True
    try:
        routing_enum = Routing[routing]
    except KeyError:
        return False

    # Ensure we're using the correct FLOODNS_ROOT

    if num_jobs == 1:
        try:
            proc = local_run_single_job(
                seed=seed,
                n_core_failures=n_core_failures,
                ring_size=ring_size,
                model=model,
                alg=routing_enum
            )
            stdout, stderr = proc.communicate()
            
            if proc.returncode != 0:
                success = False 
                
        except Exception as e:
            success = False

    if num_jobs > 1 and ring_size == "different":
        try:
            proc = local_run_multiple_jobs_different_ring_size(
                seed=seed,
                n_jobs=num_jobs,
                n_core_failures=n_core_failures,
                alg=routing_enum
            )
            stdout, stderr = proc.communicate()
            
            if proc.returncode != 0:
                success = False

        except Exception as e:
            success = False

    if num_jobs > 1 and ring_size != "different":
        try:
            proc = local_run_multiple_jobs(
                seed=seed,
                n_jobs=num_jobs,
                ring_size=ring_size,
                n_core_failures=n_core_failures,
                alg=routing_enum
            )
            stdout, stderr = proc.communicate()
            
            if proc.returncode != 0:
                success = False
                
        except Exception as e:
            success = False

    return success

def main():
    try:
        configurations = load_configurations()
    except Exception as e:
        return

    successful_runs = 0
    failed_runs = 0
    # max_runs = 5

    actual_configurations = configurations[50:351]
    for i, config in enumerate(actual_configurations):
        
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
        else:
            failed_runs += 1

if __name__ == "__main__":
    main()