# Serviço de Verificação de Ativos de Rede

## 1. Introdução
Este documento descreve a implementação de um serviço de rede em Python que opera sobre o protocolo TCP na porta 35640. O serviço é projetado para responder simultaneamente a requisições de múltiplos clientes, verificando a disponibilidade de ativos de rede dentro de uma faixa de endereçamento IP fornecida em notação CIDR. A verificação de disponibilidade pode ser realizada utilizando os protocolos ICMP (ping) ou SNMP (para obter sysName e sysDescr).

## 2. Arquitetura do Sistema
O sistema é composto por dois componentes principais:

- **Servidor TCP Multi-threaded:** Responsável por escutar na porta especificada, aceitar conexões de clientes, processar as requisições de faixa CIDR e coordenar as verificações de disponibilidade dos ativos. Cada conexão de cliente é tratada em uma thread separada para permitir o processamento simultâneo de múltiplas requisições.
- **Módulos de Verificação de Ativos:** Funções auxiliares que realizam as verificações de disponibilidade via ICMP (ping) e SNMP. A verificação SNMP é priorizada e, se bem-sucedida, retorna o sysName do dispositivo. Caso contrário, a verificação ICMP é utilizada.

## 3. Requisitos e Dependências
Para executar o serviço, são necessárias as seguintes dependências:

- **Python 3.x:** A linguagem de programação utilizada.
- **pythonping:** Biblioteca Python para realizar pings ICMP. Pode ser instalada via pip:
  ```bash
  pip install pythonping
  ```
- **pysnmp:** Biblioteca Python para interagir com dispositivos SNMP. Pode ser instalada via pip:
  ```bash
  pip install pysnmp
  ```
- **Ferramentas de linha de comando `ping` e `snmpget`:** São utilizadas via subprocess para garantir a compatibilidade e evitar problemas de permissão com raw sockets. No Ubuntu/Debian, podem ser instaladas com:
  ```bash
  sudo apt-get install iputils-ping snmp
  ```

## 4. Como Executar o Serviço

### 4.1. Configuração do Ambiente
1. Certifique-se de ter o Python 3.x instalado.
2. Instale as dependências Python:
   ```bash
   pip install pythonping pysnmp
   ```
3. Instale as ferramentas de linha de comando:
   ```bash
   sudo apt-get update
   sudo apt-get install -y iputils-ping snmp
   ```

### 4.2. Iniciando o Servidor
Para iniciar o servidor, execute o arquivo `server.py`:
```bash
python3 server.py
```
O servidor começará a escutar na porta 35640.

### 4.3. Utilizando o Cliente
O cliente (`client.py`) pode ser usado para enviar requisições ao servidor. Ele aceita uma faixa CIDR como argumento de linha de comando:
```bash
python3 client.py 192.168.105.0/24
```
Substitua `192.168.105.0/24` pela faixa CIDR desejada. O cliente exibirá a lista de IPs ativos recebida do servidor.

## 5. Detalhes da Implementação

### 5.1. server.py
- `HOST` e `PORT`: Definem o endereço IP e a porta em que o servidor irá escutar.
- `check_ping(ip_address)`: Função que executa o comando ping do sistema operacional para verificar a disponibilidade de um IP. Retorna True se o ping for bem-sucedido, False caso contrário.
- `check_snmp(ip_address, community='public')`: Função que utiliza o comando snmpget para tentar obter o sysName (OID 1.3.6.1.2.1.1.5.0) de um dispositivo. Retorna o sysName se obtido com sucesso, caso contrário, retorna None.
- `handle_client(conn, addr)`: Esta função é executada em uma thread separada para cada cliente conectado. Ela recebe a faixa CIDR, itera sobre cada IP na faixa, tenta obter o sysName via SNMP e, se não conseguir, tenta um ping. A lista de IPs ativos (com sysName se disponível) é então enviada de volta ao cliente.
- `start_server()`: Inicializa o socket TCP, vincula-o ao endereço e porta, e entra em um loop para aceitar novas conexões de clientes, despachando cada uma para uma nova thread.

### 5.2. client.py
- `send_cidr(cidr_range)`: Conecta-se ao servidor, envia a faixa CIDR e recebe a resposta. Imprime a resposta no console.
- `main`: Processa os argumentos de linha de comando para obter a faixa CIDR e chama `send_cidr`.

## 6. Considerações Finais
Este serviço oferece uma solução robusta para a verificação de ativos de rede, combinando a flexibilidade do Python com a capacidade de lidar com múltiplas requisições simultaneamente. A utilização de ferramentas de linha de comando via subprocess para ICMP e SNMP garante a compatibilidade e o desempenho, superando desafios de permissão e dependências de bibliotecas Python de baixo nível.
