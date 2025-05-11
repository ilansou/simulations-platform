#!/usr/bin/env python3
"""
Bandwidth Analysis Tool for FloodNS Simulations

This script provides a user-friendly command-line interface for analyzing
bandwidth metrics from FloodNS simulation outputs.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from time import time
from analysis_bandwidth import analyze_run, compare_routing_strategies

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the bandwidth analysis tool."""
    parser = argparse.ArgumentParser(
        description="Analyze bandwidth metrics from FloodNS simulation outputs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Main arguments
    parser.add_argument(
        "path", 
        help="Path to a logs_floodns directory, a routing strategy directory, or an experiment directory"
    )
    
    # Analysis type
    analysis_group = parser.add_argument_group("Analysis Options")
    analysis_type = analysis_group.add_mutually_exclusive_group()
    analysis_type.add_argument(
        "--single", 
        action="store_true", 
        help="Analyze a single simulation run (default if path points to logs_floodns)"
    )
    analysis_type.add_argument(
        "--compare", 
        action="store_true", 
        help="Compare different routing strategies (default if path contains multiple strategy directories)"
    )
    
    # Filtering options
    filter_group = parser.add_argument_group("Filtering Options")
    filter_group.add_argument(
        "--include-inactive", 
        action="store_true", 
        help="Include inactive links in the analysis"
    )
    filter_group.add_argument(
        "--all-connections", 
        action="store_true", 
        help="Include incomplete connections in the analysis"
    )
    filter_group.add_argument(
        "--strategies", 
        nargs="+", 
        help="Specific routing strategies to analyze (for --compare mode)"
    )
    
    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output", 
        help="Custom output file path (default: bandwidth_results.statistics in the run directory)"
    )
    output_group.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    output_group.add_argument(
        "--quiet", 
        action="store_true", 
        help="Suppress all output except errors"
    )
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Path validation
    path = Path(args.path).resolve()
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return 1
    
    # Auto-detect analysis type if not specified
    if not (args.single or args.compare):
        if path.name == "logs_floodns" or any(f.name.endswith('.csv') for f in path.glob('*.csv')):
            logger.info(f"Auto-detected single analysis mode for {path}")
            args.single = True
        else:
            # Check if this is an experiment directory with multiple routing strategies
            routing_dirs = [
                d for d in path.glob("*") 
                if d.is_dir() and (d / "logs_floodns").exists()
            ]
            if len(routing_dirs) > 1:
                logger.info(f"Auto-detected comparison mode with {len(routing_dirs)} routing strategies")
                args.compare = True
            elif len(routing_dirs) == 1:
                # Single routing strategy with logs_floodns inside
                path = routing_dirs[0]
                logger.info(f"Auto-detected single analysis mode for {path}")
                args.single = True
            elif (path / "logs_floodns").exists():
                # Path is a routing strategy directory with logs_floodns inside
                logger.info(f"Auto-detected single analysis mode for {path}/logs_floodns")
                args.single = True
                path = path / "logs_floodns"
            else:
                logger.error(f"Could not determine analysis type for {path}. Please specify --single or --compare.")
                return 1
    
    # Start timing
    start_time = time()
    
    try:
        if args.single or not args.compare:
            # Single run analysis
            if path.name != "logs_floodns" and not any(f.name.endswith('.csv') for f in path.glob('*.csv')):
                # Check if logs_floodns is inside this directory
                logs_path = path / "logs_floodns"
                if logs_path.exists():
                    path = logs_path
                    logger.info(f"Using logs directory: {path}")
                else:
                    logger.warning(f"No logs_floodns directory found in {path}")
            
            logger.info(f"Starting bandwidth analysis for: {path}")
            stats = analyze_run(
                str(path),
                filter_inactive=not args.include_inactive,
                completed_only=not args.all_connections,
            )
            
            # Output selected key metrics
            if 'flow_total_bandwidth' in stats:
                print(f"\nTotal Bandwidth: {stats['flow_total_bandwidth']:.3f} Gbit/s")
            
            if 'flow_throughput_mean' in stats and 'flow_throughput_min' in stats and 'flow_throughput_max' in stats:
                print(f"Throughput: Mean={stats['flow_throughput_mean']:.3f} Min={stats['flow_throughput_min']:.3f} Max={stats['flow_throughput_max']:.3f} Gbit/s")
            
            if 'link_utilization_mean' in stats:
                print(f"Average Link Utilization: {stats['link_utilization_mean'] * 100:.1f}%")
            
            if 'connection_completion_rate' in stats:
                print(f"Connection Completion Rate: {stats['connection_completion_rate'] * 100:.1f}%")
            
            # Report results location
            output_file = Path(stats.get('output_file', path / 'bandwidth_results.statistics'))
            print(f"\nDetailed results written to: {output_file}")
            
        else:
            # Comparison analysis
            logger.info(f"Starting bandwidth comparison for routing strategies in: {path}")
            results = compare_routing_strategies(str(path), strategies=args.strategies)
            
            if results:
                # Print a comparison table of key metrics
                strategies = list(results.keys())
                
                # Common key metrics to compare
                metrics = [
                    'flow_total_bandwidth',
                    'flow_throughput_mean',
                    'flow_throughput_max',
                    'link_utilization_mean',
                    'connection_completion_rate'
                ]
                
                # Find which metrics are actually available
                available_metrics = []
                for metric in metrics:
                    if any(metric in results[strat] for strat in strategies):
                        available_metrics.append(metric)
                
                # Print header
                print("\nRouting Strategy Comparison")
                print("==========================")
                header = f"{'Metric':<30}"
                for strat in strategies:
                    header += f"{strat:<15}"
                print(f"\n{header}")
                print("-" * len(header))
                
                # Print each metric
                for metric in available_metrics:
                    row = f"{metric:<30}"
                    for strat in strategies:
                        if strat in results and metric in results[strat]:
                            value = results[strat][metric]
                            if isinstance(value, float):
                                row += f"{value:<15.3f}"
                            else:
                                row += f"{value:<15}"
                        else:
                            row += f"{'N/A':<15}"
                    print(row)
                
                # Report results location
                output_file = Path(path) / 'routing_comparison.txt'
                print(f"\nDetailed comparison written to: {output_file}")
            else:
                logger.error("No valid routing strategies found for comparison")
                return 1
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=args.verbose)
        return 1
    
    # End timing
    end_time = time()
    logger.info(f"Analysis completed in {end_time - start_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 