from enum import Enum


class HostOversubscription(str, Enum):
    OVERSUBSCRIPTION = "oversubscription"
    RNB = "rnb"  # rearrangable non-blocking
