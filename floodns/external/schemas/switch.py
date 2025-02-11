from dataclasses import dataclass
from enum import Enum


@dataclass
class Switch:
    name: str
    port_bandwidth: int

    def __post_init__(self):
        self.port_count = get_port_count(name=self.name, port_bandwidth=self.port_bandwidth)


class Switches(Enum):
    TOFINO = Switch(name="Tofino", port_bandwidth=100)
    TOMAHAWK_3_100 = Switch(name="Tomahawk3", port_bandwidth=100)
    TOMAHAWK_3_200 = Switch(name="Tomahawk3", port_bandwidth=200)
    TOMAHAWK_3_400 = Switch(name="Tomahawk3", port_bandwidth=400)
    TOMAHAWK_4_100 = Switch(name="Tomahawk4", port_bandwidth=100)
    TOMAHAWK_4_200 = Switch(name="Tomahawk4", port_bandwidth=200)
    TOMAHAWK_4_400 = Switch(name="Tomahawk4", port_bandwidth=400)
    TOMAHAWK_5_200 = Switch(name="Tomahawk5", port_bandwidth=200)
    TOMAHAWK_5_400 = Switch(name="Tomahawk5", port_bandwidth=400)
    TOMAHAWK_5_800 = Switch(name="Tomahawk5", port_bandwidth=800)
    NVIDIA_SN5400_100 = Switch(name="NVidia_SN5400", port_bandwidth=100)
    NVIDIA_SN5400_200 = Switch(name="NVidia_SN5400", port_bandwidth=200)
    NVIDIA_SN5400_400 = Switch(name="NVidia_SN5400", port_bandwidth=400)
    NVIDIA_SN5600_100 = Switch(name="NVidia_SN5600", port_bandwidth=100)
    NVIDIA_SN5600_200 = Switch(name="NVidia_SN5600", port_bandwidth=200)
    NVIDIA_SN5600_400 = Switch(name="NVidia_SN5600", port_bandwidth=400)
    NVIDIA_SN5600_800 = Switch(name="NVidia_SN5600", port_bandwidth=800)


def get_port_count(name: str, port_bandwidth: int) -> int:
    if name == "Tomahawk3":
        if port_bandwidth == 400:
            return 32
        elif port_bandwidth == 200:
            return 64
        elif port_bandwidth == 100:
            return 128
        raise ValueError(f"Unknown port bandwidth: {port_bandwidth}")
    elif name == "Tomahawk4":
        if port_bandwidth == 400:
            return 64
        elif port_bandwidth == 200:
            return 128
        elif port_bandwidth == 100:
            return 256
        raise ValueError(f"Unknown port bandwidth: {port_bandwidth}")
    elif name == "Tomahawk5":
        if port_bandwidth == 800:
            return 64
        elif port_bandwidth == 400:
            return 128
        elif port_bandwidth == 200:
            return 256
        raise ValueError(f"Unknown port bandwidth: {port_bandwidth}")
    elif name == "Tofino" and port_bandwidth == 100:
        return 64
    elif name == "NVidia_SN5600":
        if port_bandwidth == 800:
            return 64
        elif port_bandwidth == 400:
            return 128
        elif port_bandwidth == 200:
            return 256
        elif port_bandwidth == 100:
            return 256
        raise ValueError(f"Unknown port bandwidth: {port_bandwidth}")
    elif name == "NVidia_SN5400":
        if port_bandwidth == 400:
            return 64
        elif port_bandwidth == 200:
            return 128
        elif port_bandwidth == 100:
            return 256
        raise ValueError(f"Unknown port bandwidth: {port_bandwidth}")
    raise ValueError(f"Unknown switch name: {name}")
