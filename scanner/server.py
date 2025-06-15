import socket
import threading
import ipaddress
import subprocess

HOST = '0.0.0.0'
PORT = 35640

def check_ping(ip_address):
    try:
        # Use o comando ping do sistema operacional
        # -c 1: envia 1 pacote
        # -W 1: timeout de 1 segundo
        command = ['ping', '-c', '1', '-W', '1', ip_address]
        result = subprocess.run(command, capture_output=True, text=True, timeout=2)
        
        # Verifica o código de retorno e a saída para determinar o sucesso
        if result.returncode == 0 and "1 received" in result.stdout:
            return True
        else:
            return False
    except subprocess.TimeoutExpired:
        print(f"Ping para {ip_address} excedeu o tempo limite.")
        return False
    except Exception as e:
        print(f"Erro ao pingar {ip_address}: {e}")
        return False

def check_snmp(ip_address, community='public'):
    sys_name = None
    
    # OID para sysName
    try:
        command = ["snmpget", "-v", "2c", "-c", community, ip_address, "1.3.6.1.2.1.1.5.0"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            output = result.stdout.strip()
            if "SNMPv2-MIB::sysName.0 = STRING:" in output:
                sys_name = output.split("STRING:")[1].strip()
    except Exception as e:
        print(f"Erro ao obter sysName de {ip_address} via SNMP: {e}")

    return sys_name

def handle_client(conn, addr):
    print(f"[NOVA CONEXÃO] {addr} conectado.")

    connected = True
    while connected:
        try:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break

            print(f"[{addr}] Recebido: {data}")

            # Processar a faixa CIDR
            try:
                network = ipaddress.ip_network(data, strict=False)
                active_ips = []
                for ip in network.hosts():
                    ip_str = str(ip)
                    sys_name = check_snmp(ip_str)
                    if sys_name:
                        active_ips.append(f"{ip_str} {sys_name}")
                    elif check_ping(ip_str):
                        active_ips.append(ip_str)
                
                if active_ips:
                    response = "\n".join(active_ips) + "\n"
                else:
                    response = "Nenhum IP ativo encontrado na faixa.\n"
                
                conn.sendall(response.encode('utf-8'))

            except ValueError:
                response = "Erro: Formato CIDR inválido. Por favor, envie no formato 192.168.1.0/24\n"
                conn.sendall(response.encode('utf-8'))

        except Exception as e:
            print(f"Erro ao lidar com o cliente {addr}: {e}")
            connected = False

    print(f"[DESCONEXÃO] {addr} desconectado.")
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[ESCUTANDO] Servidor escutando em {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[CONEXÕES ATIVAS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()


