"""Compare netsh single-host filters without accepting wider address ranges."""
import ipaddress


def exact_ipv4_filter(value: str, expected: str) -> bool:
    try:
        target = ipaddress.IPv4Address(expected)
        if '-' in value:
            first, last = value.split('-')
            return ipaddress.IPv4Address(first) == target == ipaddress.IPv4Address(last)
        network = ipaddress.IPv4Network(value, strict=True)
        return network.prefixlen == 32 and network.network_address == target
    except (ValueError, TypeError):
        return False
