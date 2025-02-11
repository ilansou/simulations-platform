from enum import Enum


class Routing(str, Enum):
    ECMP = "ecmp"
    MCVLC = "mcvlc"
    EDGE_COLORING = "edge_coloring"
    ILP_SOLVER = "ilp_solver"
    SIMULATED_ANNEALING = "simulated_annealing"


class CentralizedControllerRouting(str, Enum):
    MCVLC = "mcvlc"
    EDGE_COLORING = "edge_coloring"
    ILP_SOLVER = "ilp_solver"
    SIMULATED_ANNEALING = "simulated_annealing"
