#!/usr/bin/env python
"""
Demo script to showcase Chain of Thought reasoning in the simulation platform.
This script demonstrates how to use the step-by-step reasoning functionality 
for analyzing simulation results.
"""

import os
import sys
import argparse
from pathlib import Path

from llm.think_step_by_step import analyze_and_explain, explain_bandwidth_calculation
from floodns.external.analysis.analysis_bandwidth import load_simulation_csv, preprocess_data, calculate_total_bandwidth


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Demo for Chain of Thought reasoning on simulation data"
    )
    parser.add_argument(
        "--run-dir", 
        type=str, 
        required=True,
        help="Path to the simulation results directory containing CSV files"
    )
    parser.add_argument(
        "--question", 
        type=str, 
        default="Calculate total bandwidth and explain your method step by step.",
        help="Question to analyze with step-by-step reasoning"
    )
    parser.add_argument(
        "--api", 
        action="store_true",
        help="Use API for generation instead of local model"
    )
    parser.add_argument(
        "--no-llm", 
        action="store_true",
        help="Skip LLM reasoning and use direct calculation only"
    )
    return parser.parse_args()


def print_reasoning_output(output):
    """Format and print the reasoning output"""
    print("\n" + "="*80)
    print("STEP-BY-STEP REASONING PROCESS")
    print("="*80 + "\n")
    print(output["reasoning"])
    
    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80 + "\n")
    print(output["result"])
    print("\n")


def print_direct_calculation(bandwidth_info):
    """Format and print the direct calculation results"""
    print("\n" + "="*80)
    print("DIRECT BANDWIDTH CALCULATION (NO LLM)")
    print("="*80 + "\n")
    
    print("Step 1: Load flow data from simulation results")
    print("Step 2: Extract all flow data volumes")
    print("Step 3: Sum data volumes across all flows")
    print("Step 4: Calculate time span if time data is available")
    print("Step 5: Compute bandwidth rate as volume/time")
    
    print("\n" + "="*80)
    print("CALCULATION RESULTS")
    print("="*80 + "\n")
    
    # Format values with appropriate units
    formatted_info = {}
    for key, value in bandwidth_info.items():
        if value is None:
            formatted_info[key] = "N/A"
        elif key == "total_data_volume":
            formatted_info[key] = f"{value:.6f} Gbit"
        elif key == "bandwidth_rate":
            formatted_info[key] = f"{value:.6f} Gbit/s"
        elif isinstance(value, (int, float)):
            formatted_info[key] = f"{value:,}"
        else:
            formatted_info[key] = str(value)
    
    # Print the formatted results
    max_key_length = max(len(key) for key in formatted_info.keys())
    for key, value in formatted_info.items():
        print(f"{key.ljust(max_key_length+2)}: {value}")
    
    print("\n")


def main():
    """Main function to demonstrate Chain of Thought reasoning"""
    args = parse_arguments()
    
    # Check if run directory exists
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Error: Run directory '{run_dir}' does not exist.")
        return 1
    
    print(f"Analyzing data in: {run_dir}")
    print(f"Question: {args.question}")
    
    # Load the data regardless of method
    try:
        df_flow, df_conn, df_link = load_simulation_csv(str(run_dir))
        df_flow, df_conn, df_link = preprocess_data(df_flow, df_conn, df_link)
    except Exception as e:
        print(f"Error loading simulation data: {str(e)}")
        return 1
    
    # Direct calculation fallback (or primary if --no-llm)
    if args.no_llm:
        print("Using direct calculation without LLM reasoning")
        bandwidth_info = calculate_total_bandwidth(df_flow)
        print_direct_calculation(bandwidth_info)
        return 0
    
    # Continue with LLM-based reasoning if not skipped
    print(f"Using API: {'Yes' if args.api else 'No (using local model if available)'}")
    
    try:
        # Use the analyze_and_explain function for general questions
        print("\nAnalyzing with step-by-step reasoning...")
        result = analyze_and_explain(
            query=args.question, 
            run_dir=str(run_dir),
            use_api=args.api
        )
        
        # Print the reasoning and result
        print_reasoning_output(result)
        
        # Only proceed with bandwidth calculation if first analysis worked
        if "technical error" not in result["result"] and "Unable to perform analysis" not in result["result"]:
            # Example of a more specific analysis
            print("\nDemonstrating bandwidth calculation with reasoning...")
            
            # Get bandwidth calculation with reasoning
            bandwidth_result = explain_bandwidth_calculation(df_flow)
            print_reasoning_output(bandwidth_result)
        else:
            # Fallback to direct calculation
            print("\nLLM reasoning failed. Falling back to direct calculation...")
            bandwidth_info = calculate_total_bandwidth(df_flow)
            print_direct_calculation(bandwidth_info)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nFalling back to direct calculation...")
        
        try:
            bandwidth_info = calculate_total_bandwidth(df_flow)
            print_direct_calculation(bandwidth_info)
        except Exception as calc_e:
            print(f"Direct calculation also failed: {str(calc_e)}")
        
        print("\nTroubleshooting tips:")
        print("1. If you see 'FP8 quantized models' error: Your GPU doesn't support this model format.")
        print("   Solution: Try running with --api flag to use online API instead.")
        print("2. If you see '404 Client Error': The API endpoint may be incorrectly configured.")
        print("   Solution: Check your HF_TOKEN environment variable or use a different model.")
        print("3. If you're seeing Streamlit warnings: These are normal and can be ignored.")
        print("4. For guaranteed results without LLM: Try running with --no-llm flag.")
        print("\nTo run with Streamlit interface (recommended):")
        print(f"   streamlit run {sys.argv[0]} -- --run-dir {args.run_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 