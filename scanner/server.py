import asyncio
from .utils import parse_cidr  # Importa a função do nosso novo módulo
from .probes import probe_snmp, probe_icmp  # Importar as sondas
from typing import Optional, Tuple
import concurrent.futures

# (IP, Tipo de resultado, Valor) ex: ("1.1.1.1", "snmp", "dns.google")
ScanResult = Tuple[str, str, str]


def scan_host(ip: str, community: str) -> Optional[ScanResult]:
    """
    Função de trabalho que escaneia um único host.
    Projetada para ser executada em um ThreadPoolExecutor.
    Tenta SNMP primeiro, depois faz fallback para ICMP.
    """
    try:
        # Pysnmp, mesmo com API asyncio, pode ser chamado de forma síncrona
        # dentro de um loop de eventos gerenciado por asyncio.run()
        snmp_result = asyncio.run(probe_snmp(ip, community))
        if snmp_result:
            _, value = snmp_result
            return (ip, "snmp", value)

        # Fallback para ICMP se SNMP falhar
        icmp_result = asyncio.run(probe_icmp(ip))
        if icmp_result:
            _, value = icmp_result
            return (ip, "icmp", value)

    except PermissionError:
        # Se o ping falhar por permissão, não podemos continuar
        print(
            f"AVISO: O escaneamento de {ip} falhou devido a um erro de permissão para ICMP.")
        return (ip, "error", "Permission Denied")

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
                for ip, proto, value in active_hosts:
                    if proto == 'snmp':
                        response_lines.append(f"{ip} {value}")
                    elif proto == 'icmp':
                        response_lines.append(ip)
                    # Ignoramos resultados de 'error' na saída final para o cliente

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
