from floodns.external.utils.graph import get_tor_of_host, get_tor_to_hosts
from pulp import LpInteger, LpMinimize, LpProblem, LpVariable, lpSum


class CentralizedController:
    """
    Centralized controller with a global view of the network.
    It is assumed that the network is a 2-level Fat-Tree topology.
    """

    def __init__(self, n_tors: int):
        radix = n_tors // 2
        n_hosts = n_tors * radix
        self.tors = list(range(n_tors))
        self.cores = list(range(n_tors, n_tors + radix))
        self.hosts = list(range(n_tors + radix, n_tors + radix + n_hosts))

        self.tor_to_hosts = get_tor_to_hosts(n_tors=n_tors)

        self.links = []
        self.shortest_paths: dict = {}
        self.failed_links: set = set()
        self.failed_cores: set = set()
        self.paths_variables: dict = {}

        self.links_containing_paths: dict = {}

        self.problem = LpProblem("Min-Max-Link-Fairness", LpMinimize)

    def fetch_shortest_paths(self, virtual_link: tuple):
        return self.shortest_paths.get(virtual_link, [])

    def to_virtual_links(self, commodities: dict):
        for idx, (src, dst) in commodities.items():
            self.update_shortest_paths(src=src, dst=dst, idx=idx)

    def update_shortest_paths(self, src: int, dst: int, idx: int):
        if (src, dst) not in self.shortest_paths:
            src_tor, dst_tor = map(
                lambda host: get_tor_of_host(tor_to_hosts=self.tor_to_hosts, host=host), [src, dst]
            )
            non_failed_cores = sorted(set(self.cores).difference(self.failed_cores))
            self.shortest_paths[(src, dst)] = [
                [(src_tor, core), (core, dst_tor)] for core in non_failed_cores
            ]
        self.paths_variables[idx] = [
            self.create_variable(i=i, path=path, idx=idx)
            for i, path in enumerate(self.fetch_shortest_paths((src, dst)))
        ]

    def create_variable(self, i: int, path: list, idx: int):
        var = LpVariable(f"x_p_l_{idx}[{i}]", 0, 1, cat=LpInteger)
        for link in path:
            self.links_containing_paths[link].append(var)
        return var

    def construct_model(self):
        r"""
        Objective function for the Min Max Link Fairness problem

        :math:`\min \alpha`

        Subject to :math:`\sum_{p \in P_l} x_p^l = 1 \forall l \in L`

        :math:`\sum_{l \in L} \sum_{p \in P_l : e \in p} x_p^l \leq x_e \forall e \in E`

        :math:`x_e \leq \alpha \forall e \in E`

        :math:`x_p^l = 0 \forall l \in L, p \in P_l : e \in p \land e \in F`

        :math:`x_p^l \in \{0,1\} \forall p \in P_l, l \in L`

        :math:`x_e \in \mathbb{N}^+ \forall e \in E`

        :math:`\alpha \in \mathbb{N}^+`

        :return: The Min-Max-Link-Fairness problem
        """
        # Decision variables
        x_e = {
            link: LpVariable(f"x_e[{link[0]},{link[1]}]", 0, cat=LpInteger) for link in self.links
        }
        alpha = LpVariable("alpha", 0, cat=LpInteger)

        # Define the objective function
        self.problem += alpha

        # Virtual link traverse through one path only constraints
        for path_vars in self.paths_variables.values():
            self.problem += lpSum(path_vars) == 1

        # Min Max Link Fairness constraints
        for link in self.links:
            self.problem += lpSum(self.links_containing_paths[link]) <= x_e[link]

        # Alpha constraints
        for link in self.links:
            self.problem += x_e[link] <= alpha

        # Failed links constraints
        # for link in self.failed_links:
        #     self.problem += x_e[link] == 0

    def construct_max_concurrent_flow_model(self):
        pass

    def solve(self) -> float:
        try:
            status = self.problem.solve()
            if status != 1:
                raise ValueError("Solver failed to find a solution")
            return self.problem.objective.value()
        except ValueError as e:
            raise e

    def fetch_solution(self, commodities: dict) -> dict:
        assignments = {}
        for conn_id in commodities:
            var = next(filter(lambda v: v.value() > 0, self.paths_variables[conn_id]))
            selected_path = int(var.name.split("_")[-2])
            assignments[conn_id] = selected_path
        return assignments

    def cleanup(self):
        self.links = []
        self.shortest_paths: dict = {}
        self.failed_links: set = set()
        self.failed_cores: set = set()
        self.paths_variables: dict = {}

    def link_initialization(self):
        for tor_id in self.tors:
            for core_id in self.cores:
                if core_id in self.failed_cores:
                    continue
                link = (tor_id, core_id)
                if link not in self.failed_links:
                    self.links.append(link)

                link = (core_id, tor_id)
                if link not in self.failed_links:
                    self.links.append(link)

        self.links_containing_paths = {link: [] for link in self.links}
