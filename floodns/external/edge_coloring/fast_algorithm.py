from os.path import dirname, exists, join
from subprocess import PIPE, Popen, check_call


def fast_edge_coloring(commodities: dict, output_folder: str) -> dict:
    nodes = set()
    for src, dst in commodities.values():
        nodes.add(src)
        nodes.add(dst)
    nodes_mapping = {node: i for i, node in enumerate(nodes)}
    edges = [(nodes_mapping[src], nodes_mapping[dst]) for src, dst in commodities.values()]

    cpp_file = join(dirname(__file__), "fast_edge_coloring.cpp")
    output_file = join(output_folder, "output")
    if not exists(output_file):
        check_call(["g++", "-std=c++11", "-o", output_file, cpp_file])
        # check_call(["clang++", cpp_file, "output", "-stdlib=libc++"])

    # inputs to the C++ program, as a string
    inputs = f"{len(nodes)} {len(nodes)} {len(commodities)}\n"
    for u, v in edges:
        inputs += f"{u} {v}\n"

    # run the executable, and provide input
    process = Popen(f"./{output_file}", stdin=PIPE, stdout=PIPE)
    stdout, stderr = process.communicate(input=inputs.encode())

    # parse the output
    output = list(map(int, stdout.decode("utf-8").split("\n")[:-1]))
    assignments = {}
    for conn_id, color in zip(commodities.keys(), output):
        assignments[conn_id] = color

    return assignments
