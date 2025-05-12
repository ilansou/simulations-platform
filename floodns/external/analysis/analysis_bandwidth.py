import os
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def load_simulation_csv(run_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the CSV files containing simulation data.
    
    Parameters:
    -----------
    run_dir : str
        Path to the logs_floodns directory containing simulation output files
    
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Dataframes for flow_info, connection_info, and link_info
    
    Expected CSV formats:
    - flow_info.csv: flow_id, source_node_id, dest_node_id, path, start_time, end_time, 
                     duration, amount_sent, average_bandwidth, metadata
    - connection_info.csv: connection_id, source_node_id, dest_node_id, total_size, 
                          amount_sent, flow_list, start_time, end_time, duration,
                          average_bandwidth, completed, metadata
    - link_info.csv: link_id, source_id, target_id, start_time, end_time, duration,
                    avg_utilization, avg_active_flows, metadata
    """
    logger.info(f"Loading simulation data from: {run_dir}")
    
    # Define column names based on the file format documentation
    flow_cols = ['flow_id', 'source_node_id', 'dest_node_id', 'path', 'start_time', 
                'end_time', 'duration', 'amount_sent', 'average_bandwidth', 'metadata']
    
    conn_cols = ['connection_id', 'source_node_id', 'dest_node_id', 'total_size', 
                'amount_sent', 'flow_list', 'start_time', 'end_time', 'duration',
                'average_bandwidth', 'completed', 'metadata']
    
    link_cols = ['link_id', 'source_id', 'target_id', 'start_time', 'end_time', 
                'duration', 'avg_utilization', 'avg_active_flows', 'metadata']
    
    # Check if files exist
    flow_path = os.path.join(run_dir, 'flow_info.csv')
    conn_path = os.path.join(run_dir, 'connection_info.csv')
    link_path = os.path.join(run_dir, 'link_info.csv')
    
    missing_files = []
    if not os.path.exists(flow_path):
        missing_files.append('flow_info.csv')
    if not os.path.exists(conn_path):
        missing_files.append('connection_info.csv')
    if not os.path.exists(link_path):
        missing_files.append('link_info.csv')
        
    if missing_files:
        logger.warning(f"Missing data files: {', '.join(missing_files)}")
    
    # Load dataframes with appropriate error handling
    try:
        df_flow = pd.read_csv(flow_path, names=flow_cols)
        logger.info(f"Loaded flow data: {len(df_flow)} rows")
    except Exception as e:
        logger.error(f"Error loading flow data: {str(e)}")
        df_flow = pd.DataFrame(columns=flow_cols)
    
    try:
        df_conn = pd.read_csv(conn_path, names=conn_cols)
        logger.info(f"Loaded connection data: {len(df_conn)} rows")
    except Exception as e:
        logger.error(f"Error loading connection data: {str(e)}")
        df_conn = pd.DataFrame(columns=conn_cols)
    
    try:
        df_link = pd.read_csv(link_path, names=link_cols)
        logger.info(f"Loaded link data: {len(df_link)} rows")
    except Exception as e:
        logger.error(f"Error loading link data: {str(e)}")
        df_link = pd.DataFrame(columns=link_cols)
    
    # Sort dataframes
    if not df_flow.empty:
        df_flow.sort_values(['flow_id', 'start_time'], inplace=True)
    
    if not df_conn.empty:
        df_conn.sort_values(['start_time', 'connection_id'], inplace=True)
    
    return df_flow, df_conn, df_link

def preprocess_data(df_flow: pd.DataFrame, df_conn: pd.DataFrame, df_link: pd.DataFrame, 
                    filter_inactive: bool = True, completed_only: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Preprocess the simulation data for analysis.
    
    Parameters:
    -----------
    df_flow : pd.DataFrame
        Flow information dataframe
    df_conn : pd.DataFrame
        Connection information dataframe
    df_link : pd.DataFrame
        Link information dataframe
    filter_inactive : bool, optional
        Whether to filter out inactive links (default: True)
    completed_only : bool, optional
        Whether to keep only completed connections (default: False)
    
    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Preprocessed dataframes
    """
    logger.info("Preprocessing simulation data")
    
    # Make copies to avoid modifying the original dataframes
    df_flow = df_flow.copy() if df_flow is not None else None
    df_conn = df_conn.copy() if df_conn is not None else None
    df_link = df_link.copy() if df_link is not None else None
    
    # Filter inactive links
    if filter_inactive and df_link is not None and not df_link.empty:
        inactive_count = len(df_link[df_link['avg_utilization'] == 0])
        if inactive_count > 0:
            logger.info(f"Filtering out {inactive_count} inactive links")
            df_link = df_link[df_link['avg_utilization'] > 0]
    
    # Filter for completed connections only
    if completed_only and df_conn is not None and not df_conn.empty:
        # In the CSV, completed is marked as 'T' for true and 'F' for false
        completed_count = len(df_conn[df_conn['completed'] == 'T'])
        incomplete_count = len(df_conn) - completed_count
        if incomplete_count > 0:
            logger.info(f"Filtering out {incomplete_count} incomplete connections")
            df_conn = df_conn[df_conn['completed'] == 'T']
    
    # Unit conversions
    if df_flow is not None and not df_flow.empty:
        logger.info("Converting flow data units")
        # Convert nanoseconds to seconds for time values
        df_flow['duration'] = df_flow['duration'].astype(float) / 1e9
        df_flow['start_time'] = df_flow['start_time'].astype(float) / 1e9
        df_flow['end_time'] = df_flow['end_time'].astype(float) / 1e9
        # Convert raw units to Gbit
        df_flow['amount_sent'] = df_flow['amount_sent'].astype(float) / 1e9
    
    if df_conn is not None and not df_conn.empty:
        logger.info("Converting connection data units")
        # Convert nanoseconds to seconds for time values
        df_conn['duration'] = df_conn['duration'].astype(float) / 1e9
        df_conn['start_time'] = df_conn['start_time'].astype(float) / 1e9
        df_conn['end_time'] = df_conn['end_time'].astype(float) / 1e9
        # Convert raw units to Gbit
        df_conn['total_size'] = df_conn['total_size'].astype(float) / 1e9
        df_conn['amount_sent'] = df_conn['amount_sent'].astype(float) / 1e9
    
    if df_link is not None and not df_link.empty:
        logger.info("Converting link data units")
        # Convert nanoseconds to seconds for time values
        df_link['duration'] = df_link['duration'].astype(float) / 1e9
        df_link['start_time'] = df_link['start_time'].astype(float) / 1e9
        df_link['end_time'] = df_link['end_time'].astype(float) / 1e9
    
    return df_flow, df_conn, df_link

def calc_flow_stats(df_flow: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics for flow data.
    
    Parameters:
    -----------
    df_flow : pd.DataFrame
        Preprocessed flow information dataframe
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary of flow statistics
    """
    if df_flow.empty:
        logger.warning("Flow dataframe is empty, cannot calculate statistics")
        return {}
    
    logger.info("Calculating flow statistics")
    
    # Calculate throughput for each flow (Gbit/s)
    throughputs = df_flow['amount_sent'] / df_flow['duration']
    
    # Handle potential division by zero
    throughputs = throughputs.replace([np.inf, -np.inf], np.nan).dropna()
    
    if throughputs.empty:
        logger.warning("No valid throughput values found")
        return {}
    
    # Calculate statistics
    percentiles = [0.1, 1, 50, 99, 99.9]
    percentile_values = np.percentile(throughputs, percentiles)
    percentile_dict = {f'flow_throughput_{p}th': val for p, val in zip(percentiles, percentile_values)}
    
    stats = {
        'flow_count': len(df_flow),
        'flow_total_bandwidth': throughputs.sum(),
        'flow_throughput_mean': throughputs.mean(),
        'flow_throughput_std': throughputs.std(),
        'flow_throughput_min': throughputs.min(),
        'flow_throughput_max': throughputs.max(),
        'flow_unique_sources': df_flow['source_node_id'].nunique(),
        'flow_unique_targets': df_flow['dest_node_id'].nunique(),
    }
    
    # Add percentiles to stats
    stats.update(percentile_dict)
    
    return stats

def calc_connection_stats(df_conn: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics for connection data.
    
    Parameters:
    -----------
    df_conn : pd.DataFrame
        Preprocessed connection information dataframe
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary of connection statistics
    """
    if df_conn.empty:
        logger.warning("Connection dataframe is empty, cannot calculate statistics")
        return {}
    
    logger.info("Calculating connection statistics")
    
    # Calculate throughput for each connection (Gbit/s)
    throughputs = df_conn['amount_sent'] / df_conn['duration']
    
    # Handle potential division by zero
    throughputs = throughputs.replace([np.inf, -np.inf], np.nan).dropna()
    
    if throughputs.empty:
        logger.warning("No valid connection throughput values found")
        return {}
    
    # Calculate completion metrics
    if 'completed' in df_conn.columns:
        completed_count = (df_conn['completed'] == 'T').sum()
        completion_rate = completed_count / len(df_conn)
    else:
        completed_count = 0
        completion_rate = 0
    
    # Calculate statistics
    percentiles = [0.1, 1, 50, 99, 99.9]
    percentile_values = np.percentile(throughputs, percentiles)
    percentile_dict = {f'conn_throughput_{p}th': val for p, val in zip(percentiles, percentile_values)}
    
    stats = {
        'connection_count': len(df_conn),
        'connection_completed_count': completed_count,
        'connection_completion_rate': completion_rate,
        'connection_total_bandwidth': throughputs.sum(),
        'connection_throughput_mean': throughputs.mean(),
        'connection_throughput_std': throughputs.std(),
        'connection_throughput_min': throughputs.min(),
        'connection_throughput_max': throughputs.max(),
        'connection_unique_sources': df_conn['source_node_id'].nunique(),
        'connection_unique_targets': df_conn['dest_node_id'].nunique(),
    }
    
    # Add percentiles to stats
    stats.update(percentile_dict)
    
    return stats

def calc_link_stats(df_link: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate statistics for link utilization.
    
    Parameters:
    -----------
    df_link : pd.DataFrame
        Preprocessed link information dataframe
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary of link statistics
    """
    if df_link.empty:
        logger.warning("Link dataframe is empty, cannot calculate statistics")
        return {}
    
    logger.info("Calculating link statistics")
    
    # Extract utilization values
    utilization = df_link['avg_utilization']
    
    # Calculate statistics
    percentiles = [0.1, 1, 50, 99, 99.9]
    percentile_values = np.percentile(utilization, percentiles)
    percentile_dict = {f'link_utilization_{p}th': val for p, val in zip(percentiles, percentile_values)}
    
    stats = {
        'link_count': len(df_link),
        'link_active_count': (utilization > 0).sum(),
        'link_inactive_count': (utilization == 0).sum(),
        'link_utilization_mean': utilization.mean(),
        'link_utilization_std': utilization.std(),
        'link_utilization_min': utilization.min(),
        'link_utilization_max': utilization.max(),
        'link_unique_sources': df_link['source_id'].nunique(),
        'link_unique_targets': df_link['target_id'].nunique(),
    }
    
    # Add percentiles to stats
    stats.update(percentile_dict)
    
    return stats

def verify_results(df_flow: pd.DataFrame, df_conn: pd.DataFrame, df_link: pd.DataFrame, flow_precision: float = 1e-9) -> Dict[str, bool]:
    """
    Verify the simulation results for correctness.
    
    Parameters:
    -----------
    df_flow : pd.DataFrame
        Preprocessed flow information dataframe
    df_conn : pd.DataFrame
        Preprocessed connection information dataframe
    df_link : pd.DataFrame
        Preprocessed link information dataframe
    flow_precision : float, optional
        Precision threshold for flow calculations (default: 1e-9)
    
    Returns:
    --------
    Dict[str, bool]
        Dictionary of verification results
    """
    logger.info("Verifying simulation results")
    
    verification = {}
    
    # Check link capacity constraints
    if not df_link.empty:
        # Link utilization should be between 0 and 1 (or slightly above 1 due to floating point)
        capacity_check = (df_link['avg_utilization'] <= 1.0 + 1e-6).all()
        verification['link_capacity_valid'] = capacity_check
        if not capacity_check:
            logger.warning("Link capacity constraint violated")
    
    # Check for negative bandwidth values
    if not df_flow.empty:
        bandwidth_check = (df_flow['average_bandwidth'] >= 0).all()
        verification['flow_bandwidth_valid'] = bandwidth_check
        if not bandwidth_check:
            logger.warning("Negative flow bandwidth detected")
    
    # Check for negative connection bandwidth
    if not df_conn.empty:
        conn_bandwidth_check = (df_conn['average_bandwidth'] >= 0).all()
        verification['connection_bandwidth_valid'] = conn_bandwidth_check
        if not conn_bandwidth_check:
            logger.warning("Negative connection bandwidth detected")
    
    # Check for connection completion consistency
    if not df_conn.empty and 'completed' in df_conn.columns and 'amount_sent' in df_conn.columns and 'total_size' in df_conn.columns:
        # For completed connections, amount_sent should equal total_size (within precision)
        completed_df = df_conn[df_conn['completed'] == 'T']
        if not completed_df.empty:
            completion_check = ((completed_df['total_size'] - completed_df['amount_sent']).abs() <= flow_precision).all()
            verification['connection_completion_valid'] = completion_check
            if not completion_check:
                logger.warning("Completed connection data inconsistency detected")
    
    return verification

def write_statistics(run_dir: str, stats: Dict[str, Any]) -> str:
    """
    Write the calculated statistics to a file.
    
    Parameters:
    -----------
    run_dir : str
        Path to the directory containing simulation output files
    stats : Dict[str, Any]
        Dictionary of statistics to write
    
    Returns:
    --------
    str
        Path to the output statistics file
    """
    output_path = os.path.join(run_dir, 'bandwidth_results.statistics')
    logger.info(f"Writing statistics to: {output_path}")
    
    with open(output_path, 'w') as f:
        f.write("# Bandwidth Analysis Results\n")
        f.write("# =======================\n\n")
        
        # Write statistics in sections
        sections = [
            ("Flow Statistics", {k: v for k, v in stats.items() if k.startswith('flow_')}),
            ("Connection Statistics", {k: v for k, v in stats.items() if k.startswith('conn_')}),
            ("Link Statistics", {k: v for k, v in stats.items() if k.startswith('link_')}),
            ("Verification Results", {k: v for k, v in stats.items() if k.startswith('verif_')})
        ]
        
        for section_title, section_stats in sections:
            if section_stats:
                f.write(f"## {section_title}\n")
                for key, value in sorted(section_stats.items()):
                    if isinstance(value, float):
                        f.write(f"{key}={value:.6f}\n")
                    else:
                        f.write(f"{key}={value}\n")
                f.write("\n")
    
    logger.info(f"Statistics written to {output_path}")
    return output_path

def analyze_run(run_dir: str, filter_inactive: bool = True, completed_only: bool = False, 
               flow_precision: float = 1e-9) -> Dict[str, Any]:
    """
    Analyze a simulation run and calculate bandwidth statistics.
    
    Parameters:
    -----------
    run_dir : str
        Path to the directory containing simulation output files
    filter_inactive : bool, optional
        Whether to filter out inactive links (default: True)
    completed_only : bool, optional
        Whether to keep only completed connections (default: False)
    flow_precision : float, optional
        Precision threshold for flow calculations (default: 1e-9)
    
    Returns:
    --------
    Dict[str, Any]
        Dictionary of all calculated statistics
    """
    logger.info(f"Starting bandwidth analysis for: {run_dir}")
    
    # Load data
    df_flow, df_conn, df_link = load_simulation_csv(run_dir)
    
    # Preprocess data
    df_flow, df_conn, df_link = preprocess_data(
        df_flow, df_conn, df_link, 
        filter_inactive=filter_inactive, 
        completed_only=completed_only
    )
    
    # Calculate statistics
    stats = {}
    
    # Flow statistics
    flow_stats = calc_flow_stats(df_flow)
    stats.update(flow_stats)
    
    # Connection statistics
    connection_stats = calc_connection_stats(df_conn)
    stats.update(connection_stats)
    
    # Link statistics
    link_stats = calc_link_stats(df_link)
    stats.update(link_stats)
    
    # Verify results
    verification = verify_results(df_flow, df_conn, df_link, flow_precision)
    stats.update({f"verif_{k}": v for k, v in verification.items()})
    
    # Write statistics to file
    output_path = write_statistics(run_dir, stats)
    
    # Log key results
    if 'flow_total_bandwidth' in stats:
        logger.info(f"Total flow bandwidth: {stats['flow_total_bandwidth']:.3f} Gbit/s")
    if 'connection_total_bandwidth' in stats:
        logger.info(f"Total connection bandwidth: {stats['connection_total_bandwidth']:.3f} Gbit/s")
    if 'link_utilization_mean' in stats:
        logger.info(f"Mean link utilization: {stats['link_utilization_mean']:.3f}")
    
    logger.info(f"Analysis complete. Results written to: {output_path}")
    
    return stats

def compare_routing_strategies(experiment_folder, strategies):
    """
    Compare bandwidth metrics across different routing strategies for the same simulation parameters.
    
    Parameters:
    -----------
    experiment_folder : str
        Path to the experiment folder containing subdirectories for each routing strategy
    strategies : list
        List of routing strategy names to compare
        
    Returns:
    --------
    dict
        Dictionary mapping strategy names to their bandwidth statistics
    """
    logger.info(f"Comparing routing strategies in {experiment_folder}: {strategies}")
    
    # Dictionary to store results for each strategy
    results = {}
    
    for strategy in strategies:
        strategy_path = os.path.join(experiment_folder, strategy, "logs_floodns")
        if os.path.exists(strategy_path):
            logger.info(f"Analyzing strategy: {strategy}")
            try:
                # Run bandwidth analysis for this strategy
                stats = analyze_run(run_dir=strategy_path)
                results[strategy] = stats
            except Exception as e:
                logger.error(f"Error analyzing strategy {strategy}: {e}")
        else:
            logger.warning(f"Strategy path not found: {strategy_path}")
    
    # Write comparison results to file
    output_file = os.path.join(experiment_folder, "routing_comparison.txt")
    with open(output_file, "w") as f:
        f.write(f"Routing Strategy Comparison\n")
        f.write(f"==========================\n\n")
        f.write(f"Experiment: {os.path.basename(experiment_folder)}\n")
        f.write(f"Strategies compared: {', '.join(strategies)}\n\n")
        
        # Write key metrics for each strategy
        metrics = ['flow_total_bandwidth', 'flow_throughput_mean', 'flow_throughput_max', 'link_utilization_mean']
        f.write(f"{'Metric':<30} " + " ".join([f"{s:<15}" for s in strategies]) + "\n")
        f.write("-" * 80 + "\n")
        
        for metric in metrics:
            f.write(f"{metric:<30} ")
            for strategy in strategies:
                if strategy in results and metric in results[strategy]:
                    f.write(f"{results[strategy][metric]:<15.3f} ")
                else:
                    f.write(f"{'N/A':<15} ")
            f.write("\n")
    
    logger.info(f"Comparison results written to {output_file}")
    return results

def calculate_total_bandwidth(df_flow):
    """
    Calculate total bandwidth from flow data directly.
    
    Args:
        df_flow (pd.DataFrame): Flow dataframe with data volumes
        
    Returns:
        dict: Dictionary with bandwidth metrics
    """
    try:
        # Get total data volume across all flows
        if 'data_volume' in df_flow.columns:
            total_volume = df_flow['data_volume'].sum()
        elif 'volume' in df_flow.columns:
            total_volume = df_flow['volume'].sum()
        elif 'amount_sent' in df_flow.columns:  # This matches the actual column in FloodNS data
            total_volume = df_flow['amount_sent'].sum()
        else:
            # Try to find any column that might contain volume data
            numeric_cols = df_flow.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                if any(term in col.lower() for term in ['volume', 'data', 'size', 'bytes', 'bits', 'sent', 'amount']):
                    total_volume = df_flow[col].sum()
                    break
            else:
                total_volume = 0
                
        # If we have time data, calculate bandwidth rate
        if 'end_time' in df_flow.columns and 'start_time' in df_flow.columns:
            # Calculate total time span
            max_end = df_flow['end_time'].max()
            min_start = df_flow['start_time'].min()
            time_span = max_end - min_start
            
            # Avoid division by zero
            if time_span > 0:
                bandwidth_rate = total_volume / time_span
            else:
                bandwidth_rate = total_volume  # Assume instantaneous if time span is zero
        else:
            bandwidth_rate = None
            
        return {
            "total_data_volume": total_volume,
            "bandwidth_rate": bandwidth_rate,
            "num_flows": len(df_flow),
            "active_flows": df_flow[df_flow['active'] == True].shape[0] if 'active' in df_flow.columns else None
        }
    except Exception as e:
        print(f"Error calculating bandwidth: {e}")
        return {
            "total_data_volume": None,
            "bandwidth_rate": None,
            "error": str(e)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze bandwidth from FloodNS simulation output")
    parser.add_argument("run_dir", help="Path to the logs_floodns directory or experiment directory")
    parser.add_argument("--compare", action="store_true", help="Compare different routing strategies")
    parser.add_argument("--include-inactive", action="store_true", help="Include inactive links in analysis")
    parser.add_argument("--all-connections", action="store_true", help="Include incomplete connections in analysis")
    args = parser.parse_args()
    
    if args.compare:
        compare_routing_strategies(args.run_dir)
    else:
        analyze_run(
            args.run_dir,
            filter_inactive=not args.include_inactive,
            completed_only=not args.all_connections
        ) 