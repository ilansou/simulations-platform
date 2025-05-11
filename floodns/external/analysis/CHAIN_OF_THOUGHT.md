# Bandwidth Analysis Chain of Thought

This document explains the complete chain of thought for the bandwidth analysis process in the FloodNS simulation platform. Each step is documented in detail to ensure full transparency and reproducibility.

## 1. Data Ingestion

### Input File Formats

The simulation generates CSV files in the following standard format:

#### `flow_info.csv`
```
[flow_id],[source_node_id],[dest_node_id],[path],[start_time],[end_time],[duration],[amount_sent],[average_bandwidth],[metadata]
```

- `flow_id`: Unique identifier for the flow
- `source_node_id`: Node ID where the flow originates
- `dest_node_id`: Node ID where the flow terminates
- `path`: Human-readable path format (`node-[link]->node-[link]->...`)
- `start_time`: Flow start time in nanoseconds
- `end_time`: Flow end time in nanoseconds
- `duration`: Flow duration in nanoseconds
- `amount_sent`: Total amount of data sent in raw units
- `average_bandwidth`: Average bandwidth in Gbit/s
- `metadata`: Additional flow information

#### `connection_info.csv`
```
[connection_id],[source_node_id],[dest_node_id],[total_size],[amount_sent],[flow_list],[start_time],[end_time],[duration],[average_bandwidth],[completed],[metadata]
```

- `connection_id`: Unique identifier for the connection
- `source_node_id`: Node ID where the connection originates
- `dest_node_id`: Node ID where the connection terminates
- `total_size`: Total size of the connection in raw units
- `amount_sent`: Amount of data sent in raw units
- `flow_list`: Semicolon-separated list of flow IDs
- `start_time`: Connection start time in nanoseconds
- `end_time`: Connection end time in nanoseconds
- `duration`: Connection duration in nanoseconds
- `average_bandwidth`: Average bandwidth in Gbit/s
- `completed`: 'T' if connection completed, 'F' otherwise
- `metadata`: Additional connection information

#### `link_info.csv`
```
[link_id],[source_id],[target_id],[start_time],[end_time],[duration],[avg_utilization],[avg_active_flows],[metadata]
```

- `link_id`: Unique identifier for the link
- `source_id`: Source node ID
- `target_id`: Target node ID
- `start_time`: Link monitoring start time in nanoseconds
- `end_time`: Link monitoring end time in nanoseconds
- `duration`: Monitoring duration in nanoseconds
- `avg_utilization`: Average link utilization (0.0-1.0)
- `avg_active_flows`: Average number of active flows
- `metadata`: Additional link information

### Loading Process

1. The CSV files are loaded using pandas without headers (as the original files don't have headers)
2. Column names are assigned based on the known file format
3. Basic validation is performed to ensure all required files exist
4. Rows are sorted for consistent processing:
   - Flow data is sorted by flow_id and start_time
   - Connection data is sorted by start_time and connection_id
   - Link data is used as-is

## 2. Preprocessing

The preprocessing phase ensures data is in the correct format for analysis:

### Unit Conversions

1. **Time Conversion**: All time values (duration, start_time, end_time) are converted from nanoseconds to seconds:
   ```python
   time_seconds = time_nanoseconds / 1e9
   ```

2. **Data Size Conversion**: All data size values (amount_sent, total_size) are converted from raw units to Gigabits:
   ```python
   size_gigabits = size_raw / 1e9
   ```

### Filtering Steps

1. **Inactive Links**: Links with zero utilization can be filtered out to focus on active network parts:
   ```python
   active_links = links[links['avg_utilization'] > 0]
   ```

2. **Completed Connections**: Optionally filter to include only completed connections:
   ```python
   completed_connections = connections[connections['completed'] == 'T']
   ```

### Data Validation

- Checks for missing values
- Handles infinity values (from potential division by zero)
- Ensures all numeric columns are converted to the appropriate data type

## 3. Calculations

### Flow Statistics

Flow bandwidth metrics are calculated as follows:

1. **Individual Flow Throughput**:
   ```python
   flow_throughput = flow['amount_sent'] / flow['duration']  # Gbit/s
   ```

2. **Total Bandwidth**:
   ```python
   total_bandwidth = sum(flow_throughputs)  # Gbit/s
   ```

3. **Statistical Measures**:
   - Mean: `np.mean(flow_throughputs)`
   - Min: `np.min(flow_throughputs)`
   - Max: `np.max(flow_throughputs)`
   - Standard Deviation: `np.std(flow_throughputs)`
   - Percentiles: `np.percentile(flow_throughputs, [0.1, 1, 50, 99, 99.9])`

### Connection Statistics

Connection bandwidth metrics are calculated as follows:

1. **Individual Connection Throughput**:
   ```python
   connection_throughput = connection['amount_sent'] / connection['duration']  # Gbit/s
   ```

2. **Total Bandwidth**:
   ```python
   total_bandwidth = sum(connection_throughputs)  # Gbit/s
   ```

3. **Completion Rate**:
   ```python
   completion_rate = count(connections['completed'] == 'T') / count(connections)
   ```

4. **Statistical Measures**: Same as for flows (mean, min, max, std, percentiles)

### Link Statistics

Link utilization metrics are calculated as follows:

1. **Utilization Statistics**:
   - Mean: `np.mean(link_utilizations)`
   - Min: `np.min(link_utilizations)`
   - Max: `np.max(link_utilizations)`
   - Standard Deviation: `np.std(link_utilizations)`
   - Percentiles: `np.percentile(link_utilizations, [0.1, 1, 50, 99, 99.9])`

2. **Active vs Inactive Links**:
   ```python
   active_count = sum(link['avg_utilization'] > 0)
   inactive_count = sum(link['avg_utilization'] == 0)
   ```

## 4. Verification

To ensure correctness, several verification checks are performed:

### Capacity Constraints
```python
all_links_within_capacity = all(link['avg_utilization'] <= 1.0 + epsilon)
```
Ensures that no link exceeds its capacity (with a small epsilon for floating-point precision).

### Non-negative Bandwidth
```python
all_flows_valid = all(flow['average_bandwidth'] >= 0)
all_connections_valid = all(connection['average_bandwidth'] >= 0)
```
Verifies that all bandwidth values are non-negative.

### Completion Consistency
```python
for completed_connection in connections[connections['completed'] == 'T']:
    is_consistent = abs(completed_connection['total_size'] - completed_connection['amount_sent']) <= flow_precision
```
For completed connections, the amount sent should equal the total size (within precision).

## 5. Output Generation

The analysis produces a structured statistics file that includes:

### File Format
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

### Key Metrics

The most important metrics reported in the "5-minute" result are:

1. **Total Bandwidth**: Sum of all flow/connection throughputs
2. **Mean Throughput**: Average throughput across all flows/connections
3. **Min/Max Throughput**: Range of throughput values
4. **Throughput Distribution**: Percentiles showing the distribution
5. **Link Utilization**: How efficiently the network is being used

## 6. Strategy Comparison

When comparing different routing strategies, the code does the following:

1. Analyzes each strategy's output separately
2. Compiles key metrics into a comparison table
3. Outputs a formatted table showing metrics side-by-side

Example format:
```
# Routing Strategy Comparison
# =========================

Metric                                    ecmp           mcvlc          edge_coloring   ilp_solver     
--------------------------------------------------------------------------------
flow_throughput_mean                      10.500000      12.300000      13.700000       15.200000      
flow_total_bandwidth                      100.000000     120.000000     140.000000      160.000000     
...
```

This comparison enables quick identification of the most effective routing strategy in terms of bandwidth utilization.

## 7. Manual Verification Example

To manually verify the calculations, consider this simple example:

### Raw Data
- Flow 1: 10 Gb sent over 2 seconds = 5 Gb/s
- Flow 2: 20 Gb sent over 4 seconds = 5 Gb/s
- Flow 3: 30 Gb sent over 3 seconds = 10 Gb/s

### Expected Calculation
- Total Bandwidth = 5 + 5 + 10 = 20 Gb/s
- Mean Throughput = (5 + 5 + 10) / 3 = 6.67 Gb/s
- Min Throughput = 5 Gb/s
- Max Throughput = 10 Gb/s

By following this step-by-step chain of thought, the bandwidth analysis results are fully transparent and reproducible. 