import asyncio
import socket
from getmac import get_mac_address
from .mac_vendor_lookup import MACVendorLookup
from .utils import parse_cidr  # Importa a função do nosso novo módulo
from .probes import probe_snmp_info, probe_icmp  # funções necessárias
from typing import Optional, Dict, List
import concurrent.futures

# Tipo de resultado detalhado, alinhado ao formato da versão "Scanner com SNMP"
HostInfo = Dict[str, Optional[str]]


def reverse_dns(ip: str) -> Optional[str]:
    """Tenta resolver o nome DNS do host (PTR record)."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def format_host_info(info: HostInfo) -> str:
    """Formata o dicionário HostInfo para string de resposta ao cliente."""
    lines: List[str] = []
    lines.append(f"Nome DNS: {info.get('name') or info['ip']}")
    lines.append(f"Endereço IP: {info['ip']}")
    lines.append(f"MAC Address: {info.get('mac', '') or ''}")
    lines.append(f"Fabricante: {info.get('vendor', '') or ''}")
    snmp_info: Optional[Dict[str, str]] = info.get('snmp_info')  # type: ignore
    if snmp_info:
        for desc, value in snmp_info.items():
            lines.append(f"{desc}: {value}")
    return '\n'.join(lines) + '\n\n'


def scan_host(ip: str, community: str) -> Optional[HostInfo]:
    """Escaneia um host individual e devolve informações detalhadas ou None."""
    host_info: HostInfo = {
        'ip': ip,
        'name': None,
        'mac': None,
        'vendor': None,
        'snmp_info': None,
    }

    try:
        # Primeiro tenta SNMP completo
        snmp_full = asyncio.run(probe_snmp_info(ip, community))
        if snmp_full:
            host_info['snmp_info'] = snmp_full

        # Checa se host está vivo: SNMP ok ou ICMP responde
        alive = bool(snmp_full)
        if not alive:
            icmp_result = asyncio.run(probe_icmp(ip))
            alive = bool(icmp_result)
        if not alive:
            return None  # host aparentemente inativo

        # Enriquecimento de dados
        host_info['name'] = reverse_dns(ip)
        mac = get_mac_address(ip=ip)
        host_info['mac'] = mac
        host_info['vendor'] = MACVendorLookup.get_vendor(mac) if mac else "Unknown"
        return host_info

    except PermissionError:
        print(f"AVISO: Permissões insuficientes para ICMP em {ip}.")
        return None
    except Exception as e:
        print(f"Erro ao escanear {ip}: {e}")
        return None


HOST = '0.0.0.0'
PORT = 35640
MAX_WORKERS = 50  # Número de threads para a varredura paralela


async def handle_client(reader, writer):
    """
    Corrotina para lidar com cada conexão de cliente.
    Fase 5: Orquestra a varredura paralela.
    """
    addr = writer.get_extra_info('peername')
    print(f"[NOVA CONEXÃO] {addr} conectado.")
    loop = asyncio.get_running_loop()

    try:
        data = await reader.read(1024)
        if not data:
            print(f"[{addr}] Cliente desconectou sem enviar dados.")
            return

        message = data.decode().strip()
        print(f"[{addr}] Recebido: {message}")

        # Extrair CIDR e comunidade (formato: "CIDR;comunidade")
        parts = message.split(';')
        cidr_part = parts[0]
        community = parts[1] if len(parts) > 1 else 'public'

        # Validar e gerar lista de hosts para varredura
        ip_list = parse_cidr(cidr_part)
        if ip_list is None:
            print(f"[{addr}] CIDR inválido recebido: {cidr_part}")
            error_message = "ERRO: Notação CIDR inválida. Use o formato '192.168.1.0/24'.\n"
            writer.write(error_message.encode())
            await writer.drain()
            return

        if ip_list:
            print(
                f"[{addr}] Varrendo {len(ip_list)} hosts para {cidr_part} com comunidade '{community}'...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Mapeia a função scan_host para cada IP na lista
                tasks = [loop.run_in_executor(
                    executor, scan_host, ip, community) for ip in ip_list]

                # Aguarda a conclusão de todas as tarefas
                results = await asyncio.gather(*tasks)

            # Filtra os Nones e formata a resposta
            active_hosts = [res for res in results if res]

            if active_hosts:
                response_lines = []
                for info in active_hosts:
                    response_lines.append(format_host_info(info))

                response = "\n".join(response_lines) + "\n"
            else:
                response = "Nenhum host ativo encontrado na faixa especificada.\n"

            writer.write(response.encode())
            await writer.drain()

        else:
            # Não há hosts na faixa (ex: /32)
            response = "Nenhum host ativo encontrado na faixa especificada.\n"
            writer.write(response.encode())
            await writer.drain()

    except ConnectionResetError:
        print(f"[{addr}] Conexão resetada pelo cliente.")
    except Exception as e:
        print(f"Erro ao lidar com o cliente {addr}: {e}")
    finally:
        print(f"[DESCONEXÃO] {addr} desconectado.")
        writer.close()
        await writer.wait_closed()


async def main():
    """
    Ponto de entrada principal para iniciar o servidor asyncio.
    """
    server = await asyncio.start_server(
        handle_client,
        HOST,
        PORT,
        reuse_address=True  # Permite reiniciar o servidor rapidamente
    )

    addr = server.sockets[0].getsockname()
    print(f'[ESCUTANDO] Servidor escutando em {addr[0]}:{addr[1]}')

    async with server:
        await server.serve_forever()

# O bloco if __name__ == "__main__" foi movido para run_server.py
