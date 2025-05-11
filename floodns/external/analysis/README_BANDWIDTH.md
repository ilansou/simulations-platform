# FloodNS Bandwidth Analysis Tool

This tool provides comprehensive bandwidth analysis for FloodNS simulation outputs. It calculates, verifies, and summarizes bandwidth metrics from simulation results.

## Features

- **Detailed Metrics**: Calculate total bandwidth, mean/min/max throughput, link utilization, and more
- **Routing Strategy Comparison**: Compare bandwidth metrics across different routing algorithms
- **Flexible Input**: Support for single run analysis or multi-strategy comparison
- **Verification**: Built-in checks to validate simulation results
- **Command-Line Interface**: Easy-to-use command-line tool with intuitive options

## Installation

The bandwidth analysis tool is integrated into the FloodNS codebase. No additional installation is required.

Dependencies:
- Python 3.6+
- NumPy
- Pandas

## Usage

### Command-Line Interface

The simplest way to use the tool is through the command-line interface:

```bash
# Analyze a single simulation run
python analyze_bandwidth.py path/to/logs_floodns/

# Compare different routing strategies
python analyze_bandwidth.py path/to/experiment_directory/ --compare

# Include incomplete connections in the analysis
python analyze_bandwidth.py path/to/logs_floodns/ --all-connections

# Include inactive links in the analysis
python analyze_bandwidth.py path/to/logs_floodns/ --include-inactive

# Compare specific routing strategies
python analyze_bandwidth.py path/to/experiment_directory/ --compare --strategies ecmp mcvlc edge_coloring
```

### Command-Line Options

```
positional arguments:
  path                  Path to a logs_floodns directory, a routing strategy directory, or an experiment directory

Analysis Options:
  --single              Analyze a single simulation run (default if path points to logs_floodns)
  --compare             Compare different routing strategies (default if path contains multiple strategy directories)

Filtering Options:
  --include-inactive    Include inactive links in the analysis
  --all-connections     Include incomplete connections in the analysis
  --strategies STRATEGIES [STRATEGIES ...]
                        Specific routing strategies to analyze (for --compare mode)

Output Options:
  --output OUTPUT       Custom output file path (default: bandwidth_results.statistics in the run directory)
  --verbose             Enable verbose output
  --quiet               Suppress all output except errors
```

### Programmatic Usage

You can also use the analysis functionality in your own Python code:

```python
from floodns.external.analysis.analysis_bandwidth import analyze_run, compare_routing_strategies

# Analyze a single run
stats = analyze_run(
    run_dir="path/to/logs_floodns/",
    filter_inactive=True,     # Filter out inactive links
    completed_only=False      # Include incomplete connections
)

# Compare routing strategies
results = compare_routing_strategies(
    experiment_folder="path/to/experiment_directory/",
    strategies=["ecmp", "mcvlc", "edge_coloring"]  # Optional: specific strategies to analyze
)
```

## Output Format

### Single Run Analysis

The analysis produces a detailed statistics file with the following sections:

```
# Bandwidth Analysis Results
# =======================

## Flow Statistics
flow_count=<value>
flow_total_bandwidth=<value>
flow_throughput_mean=<value>
...

## Connection Statistics
connection_count=<value>
connection_total_bandwidth=<value>
...

## Link Statistics
link_count=<value>
link_utilization_mean=<value>
...

## Verification Results
verif_link_capacity_valid=<True/False>
verif_flow_bandwidth_valid=<True/False>
...
```

### Strategy Comparison

The comparison analysis produces a tabular report showing key metrics for each routing strategy:

```
# Routing Strategy Comparison
# =========================

Metric                           ecmp           mcvlc          edge_coloring   ilp_solver     
--------------------------------------------------------------------------------------------
flow_throughput_mean             10.500         12.300         13.700          15.200         
flow_total_bandwidth             100.000        120.000        140.000         160.000        
...
```

## Chain of Thought Documentation

For a complete explanation of the bandwidth analysis process, including the chain of thought for all calculations, refer to the `CHAIN_OF_THOUGHT.md` file.

## Examples

### Analyzing a Single Job

```bash
# Navigate to the analysis directory
cd floodns/external/analysis/

# Analyze a single job with ECMP routing
python analyze_bandwidth.py ../../runs/seed_42/concurrent_jobs_1/1_core_failures/ring_size_4/BLOOM/ecmp/logs_floodns/
```

Example output:
```
Total Bandwidth: 120.845 Gbit/s
Throughput: Mean=5.345 Min=1.023 Max=12.789 Gbit/s
Average Link Utilization: 73.2%
Connection Completion Rate: 92.5%

Detailed results written to: .../logs_floodns/bandwidth_results.statistics
```

### Comparing Routing Strategies

```bash
# Navigate to the analysis directory
cd floodns/external/analysis/

# Compare all routing strategies for a specific experiment
python analyze_bandwidth.py ../../runs/seed_42/concurrent_jobs_1/1_core_failures/ring_size_4/BLOOM/ --compare
```

Example output:
```
Routing Strategy Comparison
==========================

Metric                         ecmp           mcvlc          edge_coloring  ilp_solver     
----------------------------------------------------------------------------------------
flow_total_bandwidth           120.845        135.234        142.567        149.890        
flow_throughput_mean           5.345          6.123          6.789          7.234          
flow_throughput_max            12.789         13.456         14.234         15.234         
link_utilization_mean          0.732          0.789          0.845          0.879          
connection_completion_rate     0.925          0.967          0.989          0.995          

Detailed comparison written to: .../BLOOM/routing_comparison.txt
```

## Troubleshooting

If you encounter issues:

1. Use the `--verbose` flag for more detailed output
2. Check that the simulation output files exist in the expected location
3. Verify that the CSV files follow the expected format
4. Ensure you have the latest version of NumPy and Pandas installed

## Contributing

Contributions to improve the bandwidth analysis tool are welcome. Please follow these steps:

1. Run the test suite (`python test_bandwidth.py`) to ensure your changes don't break existing functionality
2. Update documentation as needed
3. Submit a pull request with a clear explanation of your changes

## License

This tool is part of the FloodNS project and is subject to the same license terms. 