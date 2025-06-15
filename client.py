import socket
import argparse
import sys

def run_client(host: str, port: int, cidr: str, community: str):
    """
    Conecta-se ao servidor de varredura, envia uma requisição e imprime a resposta.
    """
    request = f"{cidr};{community}"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print(f"Conectando a {host}:{port}...")
            s.connect((host, port))

            print(f"Enviando requisição: {request}")
            s.sendall(request.encode('utf-8'))

            # Desativa o lado de escrita do socket para sinalizar fim do envio
            s.shutdown(socket.SHUT_WR)

            print("Aguardando resposta do servidor...")
            response = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    # Fim da resposta
                    break
                response += chunk

            print("\n--- Resposta do Servidor ---")
            print(response.decode('utf-8'))
            print("--- Fim da Resposta ---\n")

    except ConnectionRefusedError:
        print(f"\nERRO: Conexão recusada. O servidor está rodando em {host}:{port}?", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cliente para o serviço de Scanner de Rede.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("cidr", help="A faixa de rede em notação CIDR a ser escaneada. Ex: '192.168.1.0/24'")
    parser.add_argument("--host", default="127.0.0.1", help="O endereço do host do servidor. Padrão: 127.0.0.1")
    parser.add_argument("--port", type=int, default=35640, help="A porta do servidor. Padrão: 35640")
    parser.add_argument("--community", default="public", help="A comunidade SNMP a ser usada. Padrão: 'public'")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    run_client(args.host, args.port, args.cidr, args.community)
