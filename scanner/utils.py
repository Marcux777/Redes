import ipaddress
from typing import List, Optional


def parse_cidr(cidr_string: str) -> Optional[List[str]]:
    """
    Analisa uma string CIDR e retorna uma lista de IPs de hosts.

    Args:
        cidr_string: A notação de rede em formato CIDR (ex: "192.168.1.0/24").

    Returns:
        Uma lista de strings de IP, ou None se o CIDR for inválido.
    """
    try:
        network = ipaddress.ip_network(cidr_string.strip(), strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError:
        # Retorna None para indicar que a string CIDR era inválida
        return None
