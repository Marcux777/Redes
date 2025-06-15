from icmplib import async_ping
from typing import Tuple, Optional
from pysnmp.hlapi.asyncio import get_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity


ProbeResult = Tuple[str, Optional[str]]


async def probe_icmp(ip: str) -> Optional[ProbeResult]:
    """
    Executa uma sondagem ICMP (ping) assíncrona em um IP.

    Args:
        ip: O endereço IP para sondar.

    Returns:
        Uma tupla (tipo, valor) em caso de sucesso (ex: ("icmp", "1.23ms")),
        ou None se o host não responder.
        Levanta PermissionError se não tiver privilégios para criar raw sockets.
    """
    try:
        host = await async_ping(ip, count=1, timeout=1)
        if host.is_alive:
            return ("icmp", f"{host.avg_rtt}ms")
        return None
    except PermissionError:
        # Este erro é crítico e deve ser tratado no nível superior.
        print("ERRO FATAL: Permissão negada para criar raw sockets. Tente executar com 'sudo'.")
        raise
    except Exception:
        # Outras exceções (ex: timeout implícito) são tratadas como falha
        return None


async def probe_snmp(ip: str, community: str = 'public') -> Optional[ProbeResult]:
    """
    Executa uma sondagem SNMP assíncrona para obter o sysName de um dispositivo.

    Args:
        ip: O endereço IP para sondar.
        community: A string de comunidade SNMP.

    Returns:
        Uma tupla ("snmp", sysName) em caso de sucesso,
        ou None se o dispositivo não responder, a comunidade estiver errada,
        ou ocorrer outro erro SNMP.
    """
    snmp_engine = SnmpEngine()
    try:
        error_indication, error_status, error_index, var_binds = await get_cmd(
            snmp_engine,
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, 161), timeout=1, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0'))  # OID para sysName
        )

        if error_indication:
            # Trata erros como timeout ou comunidade incorreta
            # print(f"SNMP Error for {ip}: {error_indication}")
            return None
        elif error_status:
            # Trata erros de protocolo
            # print(f"SNMP Protocol Error for {ip}: {error_status.prettyPrint()}")
            return None
        else:
            # Extrai o valor do sysName
            sys_name = str(var_binds[0][1])
            return ("snmp", sys_name)
    except Exception:
        # Captura outras exceções, como falhas de rede
        return None
    finally:
        # Encerra o dispatcher SNMP, se disponível, evitando leaks de file descriptors.
        try:
            dispatcher = snmp_engine.transportDispatcher
            if dispatcher:
                dispatcher.closeDispatcher()
        except Exception:
            pass
