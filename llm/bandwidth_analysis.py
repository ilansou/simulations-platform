from calculate_avg_bandwidth import get_bandwidth_stats
import os
import glob

def analyze_bandwidth_for_chat(run_dir=None, query=None):
    """
    Analyzes bandwidth data for a simulation run directory.
    
    Args:
        run_dir: The simulation run directory
        query: Optional query string to parse additional parameters
        
    Returns:
        A formatted response string for the chat
    """
    if not run_dir:
        return "No simulation run directory provided. Please specify a valid simulation."
    
    # Convert relative path to absolute if needed
    if not os.path.isabs(run_dir):
        try:
            from conf import FLOODNS_ROOT
            absolute_run_dir = os.path.join(FLOODNS_ROOT, run_dir)
        except ImportError:
            return "Error: FLOODNS_ROOT is not defined. Cannot resolve relative path."
    else:
        absolute_run_dir = run_dir
    
    # Check if run_dir points to a specific simulation or a parent directory
    flow_bandwidth_path = os.path.join(absolute_run_dir, "flow_bandwidth.csv")
    logs_flow_bandwidth_path = os.path.join(absolute_run_dir, "logs_floodns", "flow_bandwidth.csv")
    
    # If we don't find the file directly, we might be at a higher level directory
    if not os.path.exists(flow_bandwidth_path) and not os.path.exists(logs_flow_bandwidth_path):
        # Try to find any flow_bandwidth.csv files in subdirectories
        pattern = os.path.join(absolute_run_dir, "**", "flow_bandwidth.csv")
        bandwidth_files = glob.glob(pattern, recursive=True)
        
        if bandwidth_files:
            # Use the first found directory containing flow_bandwidth.csv
            parent_dir = os.path.dirname(bandwidth_files[0])
            if "logs_floodns" in parent_dir:
                absolute_run_dir = os.path.dirname(parent_dir)
            else:
                absolute_run_dir = parent_dir
        else:
            return f"Error: No flow_bandwidth.csv files found in {absolute_run_dir} or its subdirectories"

    stats = get_bandwidth_stats(run_dir=absolute_run_dir)
    
    if "error" in stats:
        return f"Error: {stats['error']}"
    
    if not stats.get("individual_files"):
        return "No bandwidth data found in the simulation files."
    
    # Get stats from the first (and typically only) file
    file_stats = stats["individual_files"][0]
    
    # Format basic stats
    average = file_stats['avg']
    median = file_stats['median']
    minimum = file_stats['min']
    maximum = file_stats['max']
    count = file_stats['count']

    query_lower = query.lower() if query else "" 

    # Determine what the user is asking for 
    if "median" in query_lower: 
        result = f"Median bandwidth: {median:.2f}" 
    elif "minimum" in query_lower or "min" in query_lower: 
        result = f"Minimum bandwidth: {minimum:.2f}" 
    elif "maximum" in query_lower or "max" in query_lower: 
        result = f"Maximum bandwidth: {maximum:.2f}" 
    elif "count" in query_lower or "how many" in query_lower: 
        result = f"Total number of flows: {count}" 
    else: 
        # Default to average if not specified 
        result = f"Average bandwidth: {average:.2f}" 

    # Always include the reasoning section
    reasoning = f"""

--- Reasoning ---
- Used file: `flow_bandwidth.csv`
- Extracted numerical values from the 4th column (index 3)
- Calculated statistics using Python
- Full stats: 
• Average: {average:.2f} 
• Median: {median:.2f} 
• Min: {minimum:.2f} 
• Max: {maximum:.2f} 
• Flow count: {count}
"""

    return f"{result}{reasoning}" 