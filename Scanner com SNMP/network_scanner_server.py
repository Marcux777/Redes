import socket
import threading
import ipaddress
import re
from host_scanner import HostScanner

PORT = 35640
USE_ARP = True

class NetworkScannerServer:
    def __init__(self, port=PORT):
        self.port = port

    @staticmethod
    def parse_network_input(data):
        cidr_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$')
        if not cidr_pattern.match(data.strip()):
            return "ERRO: Formato inválido. Use apenas: 192.168.1.0/24 (CIDR).\n"
        try:
            network = ipaddress.IPv4Network(data.strip(), strict=False)
            return [network]
        except (ipaddress.AddressValueError, ValueError) as e:
            return f"ERRO: {str(e)}\n"

    @staticmethod
    def format_host_info(host_info):
        response = []
        response.append(f"Nome DNS: {host_info['name'] if host_info.get('name') else host_info['ip']}")
        response.append(f"Endereço IP: {host_info['ip']}")
        response.append(f"MAC Address: {host_info.get('mac', '')}")
        response.append(f"Fabricante: {host_info.get('vendor', '')}")
        if host_info.get('snmp_info'):
            for desc, value in host_info['snmp_info'].items():
                response.append(f"{desc}: {value}")
        return '\n'.join(response) + '\n\n'
    
    def scan(self, network):
        if network.prefixlen == 32:
            host_info = HostScanner.scan_host(str(network.network_address))
            if host_info:
                from snmp_helper import SNMPHelper
                host_info['snmp_info'] = SNMPHelper.get_all_info(host_info['ip'])
                host_info['name'] = HostScanner.get_hostname(host_info['ip'])
                return [host_info]
            return []
        
        arp_hosts = HostScanner.arp_scan(network)
        ping_results = HostScanner.ping_scan(network)
        existing_ips = {host['ip'] for host in arp_hosts}
        all_hosts = arp_hosts + [host for host in ping_results if host['ip'] not in existing_ips]

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from snmp_helper import SNMPHelper
        def enrich_host(host):
            host['snmp_info'] = SNMPHelper.get_all_info(host['ip'])
            host['name'] = HostScanner.get_hostname(host['ip'])
            return host
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(enrich_host, host) for host in all_hosts]
            enriched_hosts = [f.result() for f in as_completed(futures)]
        return enriched_hosts

    def handle_client(self, conn, addr):
        print(f"Conexão estabelecida com {addr}.")
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if not data:
                return
            print(f"Recebido de {addr}: {data}")
            networks = self.parse_network_input(data)
            if isinstance(networks, str):
                conn.sendall(networks.encode('utf-8'))
                return
            
            conn.sendall(b"Scan iniciado, aguarde...\n\n")
            active_hosts = []
            for net in networks:
                active_hosts.extend(self.scan(net))
            
            if active_hosts:
                response = f"Hosts ativos encontrados ({len(active_hosts)}):\n\n"
                response += ''.join([self.format_host_info(host_info) for host_info in active_hosts])
                conn.sendall(response.encode('utf-8'))
            else:
                conn.sendall(b"Nenhum host ativo encontrado na rede.\n")
        except Exception as e:
            print(f"Erro com {addr}: {e}")
        finally:
            conn.close()
            print(f"Conexão encerrada com {addr}.")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', self.port))
            s.listen()
            print(f"Servidor escutando na porta {self.port}...")
            while True:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
