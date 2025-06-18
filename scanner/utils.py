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
        host_ips = [str(ip) for ip in network.hosts()]
        # Para redes /32, hosts() retorna vazio; incluímos o próprio endereço.
        if not host_ips:
            host_ips = [str(network.network_address)]
        return host_ips
    except ValueError:
        # Retorna None para indicar que a string CIDR era inválida
        return None
