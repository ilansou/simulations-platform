import pandas as pd


def get_header(metric: str):
    header = metric
    if metric == "data_parallelism_time":
        header = "All-Reduce Time (sec)"
    elif metric == "fct":
        header = "FCT (ms)"
    elif metric == "throughput":
        header = "Throughput (Gbps)"
    elif metric == "computation_time":
        header = "Computation Time (sec)"
    return header


def get_metric_percentile(df: pd.DataFrame, percentile: str, metric: str):
    return {
        "Average": round(df[metric].mean(), 2),
        "Median": round(df[metric].median(), 2),
        "25th": round(df[metric].quantile(0.25), 2),
        "75th": round(df[metric].quantile(0.75), 2),
        "90th": round(df[metric].quantile(0.9), 2),
        "95th": round(df[metric].quantile(0.95), 2),
        "99th": round(df[metric].quantile(0.99), 2),
    }[percentile]


def get_routing_color(routing: str) -> str:
    return {
        "mcvlc": "blue",
        "edge_coloring": "orange",
        "simulated_annealing": "green",
        "ilp_solver": "red",
        "ecmp": "purple",
    }[routing]


def get_title(routing: str) -> str:
    return {
        "ecmp": "ECMP",
        "mcvlc": "Ours",
        "edge_coloring": "Edge Coloring",
        "simulated_annealing": "Simulated Annealing",
        "ilp_solver": "ILP Solver",
    }[routing]
