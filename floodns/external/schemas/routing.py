from enum import Enum


class Routing(str, Enum):
    ecmp = "ecmp"
    mcvlc = "mcvlc"
    edge_coloring = "edge_coloring"
    simulated_annealing = "simulated_annealing"
    ilp_solver = "ilp_solver"


class CentralizedControllerRouting(str, Enum):
    MCVLC = "mcvlc"
    EDGE_COLORING = "edge_coloring"
    ILP_SOLVER = "ilp_solver"
    SIMULATED_ANNEALING = "simulated_annealing"
