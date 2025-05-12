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
from floodns.external.analysis.analysis_bandwidth import load_simulation_csv, preprocess_data


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
        
        # Example of a more specific analysis
        print("\nDemonstrating bandwidth calculation with reasoning...")
        df_flow, _, _ = load_simulation_csv(str(run_dir))
        df_flow, _, _ = preprocess_data(df_flow, None, None)
        
        # Get bandwidth calculation with reasoning
        bandwidth_result = explain_bandwidth_calculation(df_flow)
        print_reasoning_output(bandwidth_result)
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 