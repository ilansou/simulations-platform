import os
import json
from pathlib import Path
from floodns.external.schemas.routing import Routing

def generate_configurations():
    """
    Generate all valid configurations based on the rules:
    - Number of jobs [1-5]
    - Number of core failures [0, 1, 4, 8]
    - Ring sizes [2, 4, 8] (with constraints based on number of JYIobs)
    - Routing algorithms [ecmp, ilp_solver, simulated_annealing, edge_coloring, mcvlc]
    - Seeds [0, 42, 200, 404, 1234]
    - Model [BLOOM, GPT_3, LLAMA2_70B] (only for single job)
    
    Rules:
    - For jobs 1-3: ring sizes => [2, 8] or different ring sizes
    - For jobs 4-5: ring sizes => [2, 4] or different ring sizes
    - For single job: model => [BLOOM, GPT_3, LLAMA2_70B], otherwise no model needed
    """
    configurations = []
    
    # Number of jobs
    job_counts = [1, 2, 3, 4, 5]
    
    # Core failures
    core_failures = [0, 1, 4, 8]
    
    # Ring sizes
    ring_sizes = {
        1: [2, 8, "different"],
        2: [2, 8, "different"],
        3: [2, 8, "different"],
        4: [2, 4, "different"],
        5: [2, 4, "different"]
    }
    
    # Routing algorithms
    routing_algorithms = [
        Routing.ecmp,  
        Routing.simulated_annealing, 
        Routing.edge_coloring, 
        Routing.mcvlc
    ]
    
    # Seeds
    seeds = [0, 42, 200, 404, 1234]
    
    # Models (only for single job)
    models = ["BLOOM", "GPT_3", "LLAMA2_70B"]
    
    for num_jobs in job_counts:
        for n_cores in core_failures:
            for routing in routing_algorithms:
                for seed in seeds:
                    # Handle ring size based on job count
                    for ring_size in ring_sizes[num_jobs]:
                        if ring_size == "different":
                            # Special case for different ring size
                            if num_jobs == 1:
                                # For single job with different models
                                for model in models:
                                    configurations.append({
                                        "num_jobs": num_jobs,
                                        "n_core_failures": n_cores,
                                        "ring_size": "different",
                                        "routing": routing.value,
                                        "seed": seed,
                                        "model": model
                                    })
                            else:
                                # For multiple jobs, no model specified
                                configurations.append({
                                    "num_jobs": num_jobs,
                                    "n_core_failures": n_cores,
                                    "ring_size": "different",
                                    "routing": routing.value,
                                    "seed": seed,
                                    "model": None
                                })
                        else:
                            # Regular ring size
                            if num_jobs == 1:
                                # For single job with different models
                                for model in models:
                                    configurations.append({
                                        "num_jobs": num_jobs,
                                        "n_core_failures": n_cores,
                                        "ring_size": ring_size,
                                        "routing": routing.value,
                                        "seed": seed,
                                        "model": model
                                    })
                            else:
                                # For multiple jobs, no model specified
                                configurations.append({
                                    "num_jobs": num_jobs,
                                    "n_core_failures": n_cores,
                                    "ring_size": ring_size,
                                    "routing": routing.value,
                                    "seed": seed,
                                    "model": None
                                })
    
    return configurations

def save_configurations_to_json(configurations, output_file="configurations.json"):
    """
    Save the list of configurations to a JSON file.
    
    Args:
        configurations (list): List of configuration dictionaries
        output_file (str): Path to the output JSON file
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(configurations, f, indent=4)

def main():
    # Generate all valid configurations
    configurations = generate_configurations()
    
    # Save configurations to JSON file
    save_configurations_to_json(configurations)

if __name__ == "__main__":
    main()