import networkx as nx


def construct_bipartite_subgraph(edges: list) -> nx.MultiGraph:
    subgraph = nx.MultiGraph()
    for u, v, idx in edges:
        if "-" in u:
            assert "+" in v
            subgraph.add_node(u, bipartite=0)
            subgraph.add_node(v, bipartite=1)
        else:
            assert "+" in u and "-" in v
            subgraph.add_node(u, bipartite=1)
            subgraph.add_node(v, bipartite=0)

        subgraph.add_edge(u, v, idx)

    return subgraph


def construct_directed_multigraph(commodities: dict) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for conn_id, (src, dst) in commodities.items():
        graph.add_edge(src, dst, conn_id)
    return graph


def construct_bipartite_multigraph(graph: nx.DiGraph) -> nx.MultiGraph:
    bipartite_graph = nx.MultiGraph()

    nodes = list(graph.nodes)
    bipartite_graph.add_nodes_from(map(lambda x: f"{x}-", nodes), bipartite=0)
    bipartite_graph.add_nodes_from(map(lambda x: f"{x}+", nodes), bipartite=1)

    for src, dst, idx in graph.edges:
        bipartite_graph.add_edge(f"{src}-", f"{dst}+", idx)

    return bipartite_graph
