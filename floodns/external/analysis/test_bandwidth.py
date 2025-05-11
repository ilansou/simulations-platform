import os
import unittest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from analysis_bandwidth import (
    load_simulation_csv,
    preprocess_data,
    calc_flow_stats,
    calc_connection_stats,
    calc_link_stats,
    verify_results,
    write_statistics,
    analyze_run
)

class TestBandwidthAnalysis(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.run_dir = self.temp_dir.name
        
        # Create sample flow data
        self.flow_data = pd.DataFrame({
            'flow_id': [0, 1, 2, 3],
            'source_node_id': [1, 2, 3, 4],
            'dest_node_id': [5, 6, 7, 8],
            'path': ['1-[0]->5', '2-[1]->6', '3-[2]->7', '4-[3]->8'],
            'start_time': [0, 100, 200, 300],
            'end_time': [1000, 1100, 1200, 1300],
            'duration': [1000, 1000, 1000, 1000],
            'amount_sent': [5000, 10000, 15000, 20000],
            'average_bandwidth': [5, 10, 15, 20],
            'metadata': ['', '', '', '']
        })
        
        # Create sample connection data
        self.conn_data = pd.DataFrame({
            'connection_id': [0, 1],
            'source_node_id': [1, 3],
            'dest_node_id': [5, 7],
            'total_size': [10000, 20000],
            'amount_sent': [5000, 15000],
            'flow_list': ['0', '2'],
            'start_time': [0, 200],
            'end_time': [1000, 1200],
            'duration': [1000, 1000],
            'average_bandwidth': [5, 15],
            'completed': ['F', 'T'],
            'metadata': ['', '']
        })
        
        # Create sample link data
        self.link_data = pd.DataFrame({
            'link_id': [0, 1, 2, 3],
            'source_id': [1, 2, 3, 4],
            'target_id': [5, 6, 7, 8],
            'start_time': [0, 100, 200, 300],
            'end_time': [1000, 1100, 1200, 1300],
            'duration': [1000, 1000, 1000, 1000],
            'avg_utilization': [0.5, 0.6, 0.7, 0.8],
            'avg_active_flows': [1, 1, 1, 1],
            'metadata': ['', '', '', '']
        })
        
        # Write CSV files
        self.flow_data.to_csv(os.path.join(self.run_dir, 'flow_info.csv'), index=False, header=False)
        self.conn_data.to_csv(os.path.join(self.run_dir, 'connection_info.csv'), index=False, header=False)
        self.link_data.to_csv(os.path.join(self.run_dir, 'link_info.csv'), index=False, header=False)
    
    def tearDown(self):
        """Clean up temporary files"""
        self.temp_dir.cleanup()
    
    def test_load_simulation_csv(self):
        """Test loading CSV files"""
        df_flow, df_conn, df_link = load_simulation_csv(self.run_dir)
        
        # Check if data was loaded correctly
        self.assertEqual(len(df_flow), 4)
        self.assertEqual(len(df_conn), 2)
        self.assertEqual(len(df_link), 4)
        
        # Check column names
        expected_flow_cols = ['flow_id', 'source_node_id', 'dest_node_id', 'path', 'start_time', 
                            'end_time', 'duration', 'amount_sent', 'average_bandwidth', 'metadata']
        self.assertListEqual(list(df_flow.columns), expected_flow_cols)
    
    def test_preprocess_data(self):
        """Test data preprocessing"""
        df_flow, df_conn, df_link = load_simulation_csv(self.run_dir)
        df_flow_proc, df_conn_proc, df_link_proc = preprocess_data(df_flow, df_conn, df_link)
        
        # Check unit conversions
        self.assertAlmostEqual(df_flow_proc['duration'].iloc[0], 1.0e-6)  # 1000ns -> 0.000001s
        self.assertAlmostEqual(df_flow_proc['amount_sent'].iloc[0], 5.0e-6)  # 5000 -> 0.000005 Gbit
        
        # Test filtering
        df_flow_proc2, df_conn_proc2, df_link_proc2 = preprocess_data(
            df_flow, df_conn, df_link, completed_only=True
        )
        self.assertEqual(len(df_conn_proc2), 1)  # Only one connection is completed
    
    def test_calc_flow_stats(self):
        """Test flow statistics calculation"""
        df_flow, _, _ = load_simulation_csv(self.run_dir)
        df_flow_proc, _, _ = preprocess_data(df_flow, pd.DataFrame(), pd.DataFrame())
        
        stats = calc_flow_stats(df_flow_proc)
        
        # Check calculated statistics
        self.assertEqual(stats['flow_count'], 4)
        self.assertAlmostEqual(stats['flow_throughput_mean'], 12.5e-6)  # Mean of 5, 10, 15, 20 (scaled)
        self.assertEqual(stats['flow_unique_sources'], 4)
    
    def test_calc_connection_stats(self):
        """Test connection statistics calculation"""
        _, df_conn, _ = load_simulation_csv(self.run_dir)
        _, df_conn_proc, _ = preprocess_data(pd.DataFrame(), df_conn, pd.DataFrame())
        
        stats = calc_connection_stats(df_conn_proc)
        
        # Check calculated statistics
        self.assertEqual(stats['connection_count'], 2)
        self.assertEqual(stats['connection_completed_count'], 1)
        self.assertAlmostEqual(stats['connection_completion_rate'], 0.5)
    
    def test_calc_link_stats(self):
        """Test link statistics calculation"""
        _, _, df_link = load_simulation_csv(self.run_dir)
        _, _, df_link_proc = preprocess_data(pd.DataFrame(), pd.DataFrame(), df_link)
        
        stats = calc_link_stats(df_link_proc)
        
        # Check calculated statistics
        self.assertEqual(stats['link_count'], 4)
        self.assertAlmostEqual(stats['link_utilization_mean'], 0.65)  # Mean of 0.5, 0.6, 0.7, 0.8
    
    def test_verify_results(self):
        """Test result verification"""
        df_flow, df_conn, df_link = load_simulation_csv(self.run_dir)
        df_flow_proc, df_conn_proc, df_link_proc = preprocess_data(df_flow, df_conn, df_link)
        
        verification = verify_results(df_flow_proc, df_conn_proc, df_link_proc)
        
        # All verifications should pass with our test data
        for key, value in verification.items():
            self.assertTrue(value, f"Verification failed for {key}")
    
    def test_write_statistics(self):
        """Test writing statistics to a file"""
        stats = {
            'flow_count': 4,
            'flow_throughput_mean': 12.5,
            'connection_count': 2,
            'link_utilization_mean': 0.65
        }
        
        output_path = write_statistics(self.run_dir, stats)
        
        # Check if file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Check file content
        with open(output_path, 'r') as f:
            content = f.read()
            self.assertIn('flow_count=4', content)
            self.assertIn('flow_throughput_mean=12.500000', content)
    
    def test_analyze_run(self):
        """Test the full analysis pipeline"""
        stats = analyze_run(self.run_dir)
        
        # Check if key metrics are calculated
        self.assertIn('flow_count', stats)
        self.assertIn('connection_count', stats)
        self.assertIn('link_count', stats)
        
        # Check if output file was created
        self.assertTrue(os.path.exists(os.path.join(self.run_dir, 'bandwidth_results.statistics')))

if __name__ == '__main__':
    unittest.main() 