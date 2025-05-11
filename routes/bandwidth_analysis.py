import streamlit as st
import os
import glob
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId

from floodns.external.analysis.analysis_bandwidth import analyze_run, compare_routing_strategies
from db_client import experiments_collection
from conf import FLOODNS_ROOT

def save_bandwidth_stats_to_db(simulation_id, run_dir, stats):
    """Save bandwidth analysis results to the database"""
    try:
        # Convert numpy values to Python native types for MongoDB compatibility
        sanitized_stats = {}
        for key, value in stats.items():
            if isinstance(value, np.floating):
                sanitized_stats[key] = float(value)
            elif isinstance(value, np.integer):
                sanitized_stats[key] = int(value)
            else:
                sanitized_stats[key] = value
                
        # Update the experiment document with the analysis results
        experiments_collection.update_one(
            {"_id": ObjectId(simulation_id)},
            {
                "$set": {
                    "bandwidth_analysis": {
                        "stats": sanitized_stats,
                        "timestamp": datetime.now().isoformat(),
                        "output_file": os.path.join(run_dir, "bandwidth_results.statistics")
                    }
                }
            }
        )
        return True
    except Exception as e:
        st.error(f"Error saving bandwidth analysis to database: {e}")
        return False

def plot_throughput_distribution(stats):
    """Create a histogram of throughput distribution"""
    if not stats:
        return None
    
    # Extract data for plotting
    metrics = []
    values = []
    
    # Flow throughput
    if 'flow_throughput_mean' in stats:
        metrics.append('Flow Mean')
        values.append(stats['flow_throughput_mean'])
    if 'flow_throughput_min' in stats:
        metrics.append('Flow Min')
        values.append(stats['flow_throughput_min'])
    if 'flow_throughput_max' in stats:
        metrics.append('Flow Max')
        values.append(stats['flow_throughput_max'])
        
    # Connection throughput
    if 'connection_throughput_mean' in stats:
        metrics.append('Connection Mean')
        values.append(stats['connection_throughput_mean'])
    if 'connection_throughput_min' in stats:
        metrics.append('Connection Min')
        values.append(stats['connection_throughput_min'])
    if 'connection_throughput_max' in stats:
        metrics.append('Connection Max')
        values.append(stats['connection_throughput_max'])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(metrics, values)
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{height:.2f}',
                ha='center', va='bottom', rotation=0)
    
    ax.set_title('Throughput Statistics (Gbit/s)')
    ax.set_ylabel('Throughput (Gbit/s)')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    return fig

def plot_link_utilization(stats):
    """Create a pie chart of link utilization"""
    if not stats or 'link_count' not in stats:
        return None
    
    # Calculate active vs inactive links
    active = stats.get('link_active_count', 0)
    inactive = stats.get('link_inactive_count', 0)
    
    # If we don't have active/inactive counts but have total, assume all are active
    if active == 0 and inactive == 0 and stats['link_count'] > 0:
        active = stats['link_count']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie([active, inactive], 
           labels=['Active Links', 'Inactive Links'],
           autopct='%1.1f%%',
           startangle=90,
           colors=['#4CAF50', '#F44336'])
    ax.set_title('Link Utilization')
    
    return fig

def fetch_experiments_with_run_dir():
    """Fetch all experiments from database that have a run_dir field"""
    try:
        experiments = list(experiments_collection.find(
            {"run_dir": {"$exists": True, "$ne": None}, "state": "Finished"}
        ))
        for experiment in experiments:
            experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to string
        return experiments
    except Exception as e:
        st.error(f"Error fetching experiments: {e}")
        return []

def main():
    st.title("Bandwidth Analysis")
    
    # Check if an experiment_id was passed in query params
    experiment_id = st.query_params.get("experiment_id", None)
    preselected_experiment = None
    
    if experiment_id:
        try:
            # Fetch the experiment from the database
            experiment = experiments_collection.find_one({"_id": ObjectId(experiment_id)})
            if experiment:
                experiment['_id'] = str(experiment['_id'])  # Convert ObjectId to string
                preselected_experiment = experiment
                st.info(f"Analyzing experiment: {experiment['simulation_name']}")
        except Exception as e:
            st.error(f"Error loading experiment: {e}")
    
    # Create tabs for single run analysis and comparison
    tab1, tab2 = st.tabs(["Single Run Analysis", "Routing Strategy Comparison"])
    
    with tab1:
        st.subheader("Analyze Bandwidth for a Single Simulation")
        
        # Fetch available experiments
        experiments = fetch_experiments_with_run_dir()
        
        if not experiments:
            st.warning("No completed simulations found. Please run some simulations first.")
            return
        
        # Create a dictionary for the selectbox
        experiment_options = {f"{exp['simulation_name']} ({exp['date']})": exp for exp in experiments}
        
        # Determine preselected index if applicable
        preselected_index = 0
        if preselected_experiment:
            # Find the key for the preselected experiment
            for i, (label, exp) in enumerate(experiment_options.items()):
                if exp['_id'] == preselected_experiment['_id']:
                    preselected_index = i
                    break
        
        # Let user select an experiment
        selected_experiment_label = st.selectbox(
            "Select a simulation to analyze:",
            options=list(experiment_options.keys()),
            index=preselected_index
        )
        
        selected_experiment = experiment_options[selected_experiment_label]
        simulation_id = selected_experiment['_id']
        run_dir = selected_experiment['run_dir']
        
        # Display experiment details
        with st.expander("Experiment Details", expanded=False):
            st.write(f"**Simulation Name:** {selected_experiment['simulation_name']}")
            st.write(f"**Run Date:** {selected_experiment['date']}")
            st.write(f"**Parameters:** {selected_experiment['params']}")
            st.write(f"**Run Directory:** {run_dir}")
        
        # Analysis options
        with st.expander("Analysis Options", expanded=True):
            include_inactive = st.checkbox("Include inactive links", value=False)
            include_incomplete = st.checkbox("Include incomplete connections", value=True)
            
        # Check if analysis has already been run
        has_previous_analysis = 'bandwidth_analysis' in selected_experiment
        
        if has_previous_analysis:
            st.info("This simulation has already been analyzed. You can view the results or re-analyze it.")
            
            if st.button("View Previous Analysis"):
                stats = selected_experiment['bandwidth_analysis']['stats']
                
                # Display key metrics
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    st.metric("Total Bandwidth", f"{stats.get('flow_total_bandwidth', 0):.3f} Gbit/s")
                    st.metric("Mean Throughput", f"{stats.get('flow_throughput_mean', 0):.3f} Gbit/s")
                
                with metrics_col2:
                    st.metric("Link Utilization", f"{stats.get('link_utilization_mean', 0) * 100:.1f}%")
                    st.metric("Completion Rate", f"{stats.get('connection_completion_rate', 0) * 100:.1f}%")
                
                # Display visualizations
                throughput_fig = plot_throughput_distribution(stats)
                if throughput_fig:
                    st.pyplot(throughput_fig)
                
                utilization_fig = plot_link_utilization(stats)
                if utilization_fig:
                    st.pyplot(utilization_fig)
                
                # Download link for full results
                output_file = selected_experiment['bandwidth_analysis'].get('output_file')
                if output_file and os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        st.download_button(
                            label="Download Analysis Results",
                            data=f.read(),
                            file_name="bandwidth_results.statistics",
                            mime="text/plain"
                        )
        
        # Run analysis button
        analysis_button_label = "Re-analyze" if has_previous_analysis else "Run Bandwidth Analysis"
        if st.button(analysis_button_label):
            try:
                with st.spinner("Analyzing bandwidth data..."):
                    stats = analyze_run(
                        run_dir=run_dir,
                        filter_inactive=not include_inactive,
                        completed_only=not include_incomplete
                    )
                
                st.success("Analysis completed successfully!")
                
                # Save to database
                if save_bandwidth_stats_to_db(simulation_id, run_dir, stats):
                    st.success("Results saved to database")
                
                # Display key metrics
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    st.metric("Total Bandwidth", f"{stats.get('flow_total_bandwidth', 0):.3f} Gbit/s")
                    st.metric("Mean Throughput", f"{stats.get('flow_throughput_mean', 0):.3f} Gbit/s")
                
                with metrics_col2:
                    st.metric("Link Utilization", f"{stats.get('link_utilization_mean', 0) * 100:.1f}%")
                    st.metric("Completion Rate", f"{stats.get('connection_completion_rate', 0) * 100:.1f}%")
                
                # Display visualizations
                throughput_fig = plot_throughput_distribution(stats)
                if throughput_fig:
                    st.pyplot(throughput_fig)
                
                utilization_fig = plot_link_utilization(stats)
                if utilization_fig:
                    st.pyplot(utilization_fig)
                
                # Display full results in expandable section
                with st.expander("Full Analysis Results", expanded=False):
                    st.json(stats)
                
                # Provide download link
                output_file = os.path.join(run_dir, "bandwidth_results.statistics")
                if os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        st.download_button(
                            label="Download Analysis Results",
                            data=f.read(),
                            file_name="bandwidth_results.statistics",
                            mime="text/plain"
                        )
            
            except Exception as e:
                st.error(f"Error during bandwidth analysis: {str(e)}")
                import traceback
                st.code(traceback.format_exc(), language="python")
    
    with tab2:
        st.subheader("Compare Routing Strategies")
        
        # Explanation of comparison
        st.info("This feature allows you to compare bandwidth metrics across different routing algorithms for the same simulation parameters.")
        
        # Find simulation folders with multiple strategies
        all_experiment_folders = glob.glob(os.path.join(str(Path(FLOODNS_ROOT)), "runs", "seed_*", "concurrent_jobs_*", "*_core_failures", "*"))
        
        # Filter to folders that contain multiple routing strategy directories
        valid_comparison_folders = []
        for folder in all_experiment_folders:
            if os.path.isdir(folder):
                routing_dirs = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
                if len(routing_dirs) > 1:
                    valid_comparison_folders.append(folder)
        
        if not valid_comparison_folders:
            st.warning("No simulation folders found with multiple routing strategies for comparison.")
            return
        
        # Let user select a folder for comparison
        selected_folder = st.selectbox(
            "Select a simulation folder to compare routing strategies:",
            options=valid_comparison_folders,
            format_func=lambda x: os.path.basename(os.path.dirname(os.path.dirname(x))) + " / " + 
                                   os.path.basename(os.path.dirname(x)) + " / " + 
                                   os.path.basename(x)
        )
        
        # Get available strategies in this folder
        available_strategies = [d for d in os.listdir(selected_folder) if os.path.isdir(os.path.join(selected_folder, d))]
        
        # Let user select which strategies to compare
        selected_strategies = st.multiselect(
            "Select routing strategies to compare:",
            options=available_strategies,
            default=available_strategies
        )
        
        if selected_strategies:
            if st.button("Compare Strategies"):
                try:
                    with st.spinner("Comparing routing strategies..."):
                        results = compare_routing_strategies(
                            experiment_folder=selected_folder,
                            strategies=selected_strategies
                        )
                    
                    st.success("Comparison completed successfully!")
                    
                    # Create table for key metrics
                    metrics_to_show = [
                        'flow_total_bandwidth',
                        'flow_throughput_mean',
                        'flow_throughput_max',
                        'link_utilization_mean'
                    ]
                    
                    # Prepare data for DataFrame
                    comparison_data = []
                    
                    for metric in metrics_to_show:
                        row = {'Metric': metric}
                        for strategy in selected_strategies:
                            if strategy in results and metric in results[strategy]:
                                row[strategy] = results[strategy][metric]
                            else:
                                row[strategy] = None
                        comparison_data.append(row)
                    
                    # Create and display DataFrame
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df.set_index('Metric').style.format("{:.3f}"))
                    
                    # Create bar chart comparison
                    st.subheader("Bandwidth Comparison")
                    
                    # Prepare data for chart
                    metrics_for_chart = []
                    strategies_list = []
                    values_list = []
                    
                    for metric in metrics_to_show:
                        for strategy in selected_strategies:
                            if strategy in results and metric in results[strategy]:
                                metrics_for_chart.append(metric)
                                strategies_list.append(strategy)
                                values_list.append(results[strategy][metric])
                    
                    # Create DataFrame for chart
                    chart_data = pd.DataFrame({
                        'Metric': metrics_for_chart,
                        'Strategy': strategies_list,
                        'Value': values_list
                    })
                    
                    # Create and display bar chart
                    fig, ax = plt.subplots(figsize=(12, 8))
                    
                    # Generate positions for grouped bars
                    unique_metrics = sorted(chart_data['Metric'].unique())
                    unique_strategies = sorted(chart_data['Strategy'].unique())
                    
                    bar_width = 0.8 / len(unique_strategies)
                    
                    for i, strategy in enumerate(unique_strategies):
                        strategy_data = chart_data[chart_data['Strategy'] == strategy]
                        x_positions = np.arange(len(unique_metrics)) + (i - len(unique_strategies)/2 + 0.5) * bar_width
                        
                        # Get values for this strategy
                        values = []
                        for metric in unique_metrics:
                            metric_value = strategy_data[strategy_data['Metric'] == metric]['Value'].values
                            values.append(metric_value[0] if len(metric_value) > 0 else 0)
                        
                        # Plot bars for this strategy
                        bars = ax.bar(x_positions, values, width=bar_width, label=strategy)
                        
                        # Add value labels on top of bars
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                                   f'{height:.2f}',
                                   ha='center', va='bottom', rotation=0)
                    
                    # Configure chart
                    ax.set_xticks(np.arange(len(unique_metrics)))
                    ax.set_xticklabels([m.replace('flow_', '').replace('link_', '') for m in unique_metrics])
                    ax.set_title('Routing Strategy Comparison')
                    ax.set_ylabel('Value')
                    ax.legend()
                    ax.grid(axis='y', linestyle='--', alpha=0.7)
                    
                    st.pyplot(fig)
                    
                    # Provide download link to comparison file
                    comparison_file = os.path.join(selected_folder, 'routing_comparison.txt')
                    if os.path.exists(comparison_file):
                        with open(comparison_file, "r") as f:
                            st.download_button(
                                label="Download Comparison Results",
                                data=f.read(),
                                file_name="routing_comparison.txt",
                                mime="text/plain"
                            )
                
                except Exception as e:
                    st.error(f"Error during strategy comparison: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")

if __name__ == "__main__":
    main() 