from enum import Enum


class Routing(str, Enum):
<<<<<<< HEAD
    ECMP = "ecmp"
    MCVLC = "mcvlc"
    EDGE_COLORING = "edge_coloring"
    ILP_SOLVER = "ilp_solver"
    SIMULATED_ANNEALING = "simulated_annealing"
=======
    ecmp = "ecmp"
    mcvlc = "mcvlc"
    edge_coloring = "edge_coloring"
    simulated_annealing = "simulated_annealing"
    ilp_solver = "ilp_solver"
>>>>>>> e55857a8430394049ed29d2cc14101bf4479bdb5


class CentralizedControllerRouting(str, Enum):
    MCVLC = "mcvlc"
    EDGE_COLORING = "edge_coloring"
    ILP_SOLVER = "ilp_solver"
    SIMULATED_ANNEALING = "simulated_annealing"
