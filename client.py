import socket
import sys

HOST = '127.0.0.1'
PORT = 35640

def send_cidr(cidr_range):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        client.sendall(cidr_range.encode('utf-8'))
        
        response = b''
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
        
        print(f"Resposta do servidor:\n{response.decode('utf-8')}")
        client.close()
    except ConnectionRefusedError:
        print(f"Erro: Conexão recusada. Certifique-se de que o servidor está rodando em {HOST}:{PORT}")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 client.py <faixa_cidr>")
        print("Exemplo: python3 client.py 192.168.1.0/24")
        sys.exit(1)

    cidr_to_send = sys.argv[1]
    send_cidr(cidr_to_send)


