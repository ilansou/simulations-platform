from floodns.external.schemas.job import Job
from floodns.external.utils.graph import get_tor_of_host, get_tor_to_hosts

HEADER = "#src dst src_tor dst_tor start_time flow_size compute_time stage_index\n"
LINE = "{src} {dst} {src_tor} {dst_tor} {start_time} {flow_size} {compute_time} {stage_index}\n"


def write_ddp_file(n_tors: int, filename: str, job: Job):
    tor_to_hosts = get_tor_to_hosts(n_tors=n_tors)
    with open(filename, "w") as f:
        f.write(HEADER)
        for stage, dp in enumerate(job.data_parallels):
            for worker, next_worker in zip(dp.nics[:-1], dp.nics[1:]):
                f.write(
                    LINE.format(
                        src=worker,
                        src_tor=get_tor_of_host(tor_to_hosts=tor_to_hosts, host=worker),
                        dst=next_worker,
                        dst_tor=get_tor_of_host(tor_to_hosts=tor_to_hosts, host=next_worker),
                        start_time=job.start_time,
                        flow_size=dp.flow_size,
                        compute_time=job.compute_time,
                        stage_index=stage,
                    )
                )

            f.write(
                LINE.format(
                    src=dp.nics[-1],
                    src_tor=get_tor_of_host(tor_to_hosts=tor_to_hosts, host=dp.nics[-1]),
                    dst=dp.nics[0],
                    dst_tor=get_tor_of_host(tor_to_hosts=tor_to_hosts, host=dp.nics[0]),
                    start_time=job.start_time,
                    flow_size=dp.flow_size,
                    compute_time=job.compute_time,
                    stage_index=stage,
                )
            )
