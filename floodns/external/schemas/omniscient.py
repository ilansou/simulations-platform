from dataclasses import dataclass


@dataclass
class OmniscientSolution:
    job_id: int
    job_colliding_with: set
    virtual_links: set
    tors: set
    common_tors: set
    paths: set
