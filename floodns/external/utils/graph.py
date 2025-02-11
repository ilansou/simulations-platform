def get_tor_to_hosts(n_tors: int) -> dict:
    radix = n_tors // 2
    tor_to_hosts = {}
    for tor in range(n_tors):
        tor_to_hosts[tor] = set()
        start_server = n_tors + radix + tor * radix
        end_server = start_server + radix
        tor_to_hosts[tor].update(range(start_server, end_server))

    return tor_to_hosts


def get_tor_of_host(tor_to_hosts: dict, host: int) -> int:
    for tor, hosts in tor_to_hosts.items():
        if host in hosts:
            return tor

    raise ValueError(f"Host {host} not found in any tor")
