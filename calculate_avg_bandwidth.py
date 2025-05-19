import csv
import statistics
import os
import argparse
from glob import glob
import sys
import re
import json

# Increase CSV field size limit to handle large fields
# Use a more cautious approach to avoid overflow on different platforms
max_int = sys.maxsize
while True:
    # Decrease the max_int value by factor 10 
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int/10)

def analyze_bandwidth_file(file_path):
    """Analyze a single flow_bandwidth.csv file and return statistics."""
    bandwidths = []
    
    try:
        # Read the CSV file
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                # The fourth column (index 3) contains bandwidth values
                if len(row) >= 4:
                    try:
                        bandwidth = float(row[3])
                        bandwidths.append(bandwidth)
                    except (ValueError, IndexError):
                        # Skip rows with invalid data
                        continue
    except csv.Error:
        # If standard CSV reader fails, try a manual approach with line splitting
        print("  Standard CSV reader failed, trying alternative approach...")
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    # Split by comma and parse fourth value
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        bandwidth = float(parts[3])
                        bandwidths.append(bandwidth)
                except (ValueError, IndexError):
                    # Skip invalid lines
                    continue
    
    if bandwidths:
        stats = {
            'avg': statistics.mean(bandwidths),
            'median': statistics.median(bandwidths),
            'min': min(bandwidths),
            'max': max(bandwidths),
            'count': len(bandwidths),
            'file_path': file_path
        }
        return stats
    return None

def find_bandwidth_files(base_dir="floodns/runs", **filters):
    """
    Find flow_bandwidth.csv files that match specified filters.
    
    Filters can include:
    - seed: Random seed number
    - concurrent_jobs: Number of concurrent jobs
    - core_failures: Number of core failures
    - ring_size: Size of the ring
    - model: Model name (e.g., LLAMA2_70B, GPT_3)
    - algorithm: Algorithm name (e.g., ecmp, simulated_annealing)
    """
    pattern = os.path.join(base_dir, "**", "logs_floodns", "flow_bandwidth.csv")
    all_files = glob(pattern, recursive=True)
    
    if not filters:
        return all_files
    
    # Regular expressions for extracting components from path
    patterns = {
        'seed': r'seed_(\d+)',
        'concurrent_jobs': r'concurrent_jobs_(\d+)',
        'core_failures': r'(\d+)_core_failures',
        'ring_size': r'ring_size_(\d+)',
        'model': r'ring_size_\d+/([\w\d_]+)/',
        'algorithm': r'/([\w_]+)/logs_floodns'
    }
    
    filtered_files = []
    for file_path in all_files:
        match = True
        for key, value in filters.items():
            if key in patterns:
                regex = patterns[key]
                match_result = re.search(regex, file_path)
                if not match_result or str(match_result.group(1)) != str(value):
                    match = False
                    break
        
        if match:
            filtered_files.append(file_path)
    
    return filtered_files

def find_specific_file(run_dir, filename="flow_bandwidth.csv"):
    """Find a specific file in the run directory."""
    # If the path directly points to logs_floodns directory
    direct_path = os.path.join(run_dir, filename)
    if os.path.exists(direct_path):
        return direct_path
    
    # Try to find in logs_floodns subdirectory
    logs_path = os.path.join(run_dir, "logs_floodns", filename)
    if os.path.exists(logs_path):
        return logs_path
    
    # Try to find the file anywhere within the run_dir
    pattern = os.path.join(run_dir, "**", filename)
    matches = glob(pattern, recursive=True)
    if matches:
        return matches[0]
    
    return None

def get_bandwidth_stats(run_dir=None, file_path=None, filters=None):
    """
    Get bandwidth statistics from a specific run_dir, file_path, or using filters.
    Returns a dictionary with statistics that can be used by the chat system.
    """
    files_to_analyze = []
    
    # Priority 1: Specific file_path
    if file_path and os.path.exists(file_path):
        files_to_analyze = [file_path]
    
    # Priority 2: run_dir - look for flow_bandwidth.csv in this directory
    elif run_dir:
        specific_file = find_specific_file(run_dir)
        if specific_file:
            files_to_analyze = [specific_file]
    
    # Priority 3: Use filters to find matching files
    elif filters:
        files_to_analyze = find_bandwidth_files(**filters)
    
    # No valid source specified
    if not files_to_analyze:
        return {"error": "No flow_bandwidth.csv files found"}
    
    # Analyze files
    results = []
    for file_path in files_to_analyze:
        try:
            stats = analyze_bandwidth_file(file_path)
            if stats:
                results.append(stats)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Aggregate results
    if not results:
        return {"error": "No valid bandwidth data found in files"}
    
    # Calculate overall statistics
    all_bandwidths = []
    for stat in results:
        # Weight by the number of flows
        all_bandwidths.extend([stat["avg"]] * stat["count"])
    
    # Return a structured result for the chat system
    return {
        "overall_avg": statistics.mean(all_bandwidths) if all_bandwidths else None,
        "overall_count": len(all_bandwidths),
        "individual_files": [{
            "file_path": stat["file_path"],
            "avg": stat["avg"],
            "median": stat["median"],
            "min": stat["min"],
            "max": stat["max"],
            "count": stat["count"]
        } for stat in results],
        "file_count": len(results)
    }

def extract_simulation_params_from_path(path):
    """Extract simulation parameters from a file path to help with identification."""
    patterns = {
        'seed': r'seed_(\d+)',
        'concurrent_jobs': r'concurrent_jobs_(\d+)',
        'core_failures': r'(\d+)_core_failures',
        'ring_size': r'ring_size_(\d+)',
        'model': r'/(BLOOM|GPT_3|LLAMA2_70B)/',
        'algorithm': r'/(ecmp|ilp_solver|simulated_annealing|edge_coloring|mcvlc)/logs_floodns'
    }
    
    params = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, path)
        if match:
            params[key] = match.group(1)
    
    return params

def format_bandwidth_response(stats):
    """Format bandwidth statistics into a human-readable response for the chat."""
    if "error" in stats:
        return f"Error: {stats['error']}"
    
    if not stats.get("individual_files"):
        return "No bandwidth data found in the simulation files."
    
    if len(stats["individual_files"]) == 1:
        # Single file response
        file_stats = stats["individual_files"][0]
        response = f"I analyzed the bandwidth data from {os.path.basename(file_stats['file_path'])}.\n\n"
        response += f"Average bandwidth: {file_stats['avg']:.2f}\n"
        response += f"Median bandwidth: {file_stats['median']:.2f}\n"
        response += f"Minimum bandwidth: {file_stats['min']:.2f}\n"
        response += f"Maximum bandwidth: {file_stats['max']:.2f}\n"
        response += f"Total flow count: {file_stats['count']}"
        
        # Add simulation details if available
        params = extract_simulation_params_from_path(file_stats['file_path'])
        if params:
            response += "\n\nThis data is from a simulation with the following parameters:\n"
            for key, value in params.items():
                response += f"- {key}: {value}\n"
    else:
        # Multiple files response
        response = f"I analyzed bandwidth data from {stats['file_count']} files.\n\n"
        response += f"Overall average bandwidth across all flows: {stats['overall_avg']:.2f}\n"
        response += f"Total flow count: {stats['overall_count']}\n\n"
        
        # Add details for each file
        response += "Individual file statistics:\n"
        for i, file_stats in enumerate(stats["individual_files"], 1):
            params = extract_simulation_params_from_path(file_stats['file_path'])
            file_desc = ", ".join([f"{k}: {v}" for k, v in params.items()]) if params else os.path.basename(file_stats['file_path'])
            response += f"\n{i}. {file_desc}\n"
            response += f"   Average: {file_stats['avg']:.2f}, Median: {file_stats['median']:.2f}, "
            response += f"Min: {file_stats['min']:.2f}, Max: {file_stats['max']:.2f}, "
            response += f"Flows: {file_stats['count']}"
    
    return response

def main():
    parser = argparse.ArgumentParser(description='Calculate bandwidth statistics from flow_bandwidth.csv files')
    parser.add_argument('--dir', default="floodns/runs", help='Base directory to search for flow_bandwidth.csv files')
    parser.add_argument('--file', help='Specific flow_bandwidth.csv file to analyze')
    parser.add_argument('--run-dir', dest='run_dir', help='Specific run directory containing flow_bandwidth.csv')
    parser.add_argument('--output-json', action='store_true', help='Output results as JSON')
    
    # Add filter arguments
    parser.add_argument('--seed', help='Filter by seed number')
    parser.add_argument('--concurrent-jobs', dest='concurrent_jobs', help='Filter by number of concurrent jobs')
    parser.add_argument('--core-failures', dest='core_failures', help='Filter by number of core failures')
    parser.add_argument('--ring-size', dest='ring_size', help='Filter by ring size')
    parser.add_argument('--model', help='Filter by model name (e.g., LLAMA2_70B, GPT_3)')
    parser.add_argument('--algorithm', help='Filter by algorithm name (e.g., ecmp, simulated_annealing)')
    
    args = parser.parse_args()
    
    # Build filters dictionary from args
    filters = {}
    for filter_name in ['seed', 'concurrent_jobs', 'core_failures', 'ring_size', 'model', 'algorithm']:
        if getattr(args, filter_name):
            filters[filter_name] = getattr(args, filter_name)
    
    # Get stats based on provided arguments
    if args.file:
        stats = get_bandwidth_stats(file_path=args.file)
    elif args.run_dir:
        stats = get_bandwidth_stats(run_dir=args.run_dir)
    elif filters:
        stats = get_bandwidth_stats(filters=filters)
    else:
        stats = get_bandwidth_stats(filters={})
    
    # Output results
    if args.output_json:
        print(json.dumps(stats, indent=2))
    else:
        if "error" in stats:
            print(f"Error: {stats['error']}")
            return
        
        print(f"Found {stats['file_count']} flow_bandwidth.csv files")
        
        # Print individual file statistics
        for i, file_stats in enumerate(stats["individual_files"], 1):
            print(f"\n{i}. Analyzing: {file_stats['file_path']}")
            print(f"  Average Bandwidth: {file_stats['avg']}")
            print(f"  Median Bandwidth: {file_stats['median']}")
            print(f"  Min Bandwidth: {file_stats['min']}")
            print(f"  Max Bandwidth: {file_stats['max']}")
            print(f"  Total Flow Count: {file_stats['count']}")
        
        # Print overall statistics
        print("\nOVERALL STATISTICS:")
        print(f"Total analyzed flows: {stats['overall_count']}")
        print(f"Overall average bandwidth: {stats['overall_avg']}")

if __name__ == "__main__":
    main() 