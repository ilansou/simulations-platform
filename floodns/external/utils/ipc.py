def fetch_commodities(commodities_str: str) -> dict:
    commodities = commodities_str.replace("{", "").replace("}", "").split(", ")
    commodities = [t.split("=") for t in commodities]
    result_map = {}
    for conn_id, commodity in commodities:
        idx = int(conn_id)
        result_map[idx] = eval(commodity)
    return result_map
