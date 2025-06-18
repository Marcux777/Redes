from icmplib import async_ping
from typing import Tuple, Optional, Dict
from pysnmp.hlapi.asyncio import get_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity


ProbeResult = Tuple[str, Optional[str]]

SNMP_OIDS: Dict[str, str] = {
    'Descrição do Sistema': '1.3.6.1.2.1.1.1.0',
    'Object ID': '1.3.6.1.2.1.1.2.0',
    'Tempo de Atividade': '1.3.6.1.2.1.1.3.0',
    'Nome SNMP': '1.3.6.1.2.1.1.5.0',
    'Contato': '1.3.6.1.2.1.1.4.0',
    'Serviços': '1.3.6.1.2.1.1.7.0',
    'Número de Interfaces': '1.3.6.1.2.1.2.1.0',
    'CPU Idle (%)': '1.3.6.1.4.1.2021.11.11.0',
    'Memória Total (kB)': '1.3.6.1.4.1.2021.4.5.0',
    'Memória Livre (kB)': '1.3.6.1.4.1.2021.4.6.0',
}


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


async def probe_snmp_info(ip: str, community: str = 'public') -> Optional[Dict[str, str]]:
    """
    Executa uma sondagem SNMP e devolve um dicionário com diversos atributos
    do host (descritos em SNMP_OIDS).

    Retorna None se nenhuma informação for obtida.
    """
    snmp_engine = SnmpEngine()
    info: Dict[str, str] = {}

    try:
        for desc, oid in SNMP_OIDS.items():
            error_indication, error_status, error_index, var_binds = await get_cmd(
                snmp_engine,
                CommunityData(community, mpModel=0),
                UdpTransportTarget((ip, 161), timeout=1, retries=1),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )

            if error_indication or error_status:
                continue  # Tenta próximo OID
            else:
                value = str(var_binds[0][1])
                info[desc] = value

        return info if info else None
    except Exception:
        return None
    finally:
        try:
            dispatcher = snmp_engine.transportDispatcher
            if dispatcher:
                dispatcher.closeDispatcher()
        except Exception:
            pass
