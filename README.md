# Scanner de Rede Concorrente

Este projeto implementa um serviço de rede de alto desempenho em Python, projetado para escanear faixas de rede e identificar hosts ativos. Ele utiliza uma arquitetura moderna baseada em `asyncio` para gerenciar múltiplas conexões de clientes simultaneamente e um modelo de concorrência híbrido para executar as sondagens de rede de forma eficiente.

## ✨ Funcionalidades

- **Servidor TCP Assíncrono**: Construído com `asyncio` para lidar com um grande número de clientes concorrentes com baixo consumo de recursos.
- **Arquitetura Híbrida**: Utiliza um `ThreadPoolExecutor` para executar as operações de varredura (sondagens de rede) em paralelo, isolando o loop de eventos principal e garantindo que o servidor permaneça responsivo.
- **Sondagem Inteligente**:
    - **SNMP**: Prioriza a sondagem via SNMP (v2c) para obter informações detalhadas do host, como o `sysName` (OID `1.3.6.1.2.1.1.5.0`).
    - **ICMP (Ping)**: Realiza um fallback para uma sondagem ICMP (`ping`) se o host não responder ao SNMP.
- **Implementações Nativas**: Utiliza bibliotecas Python puras (`pysnmp`, `icmplib`) em vez de depender de chamadas de subprocessos a comandos do sistema operacional, tornando a aplicação mais robusta, segura e portável.
- **Cliente Interativo**: Inclui um cliente de linha de comando (`client.py`) para facilitar a interação com o servidor.

## ⚙️ Estrutura do Projeto

```
/
|-- /scanner            # Módulos principais da aplicação
|   |-- server.py       # Lógica do servidor asyncio e orquestração da varredura
|   |-- probes.py       # Funções de sondagem (ICMP e SNMP)
|   |-- utils.py        # Utilitários, como o parser de CIDR
|-- client.py           # Cliente de linha de comando para interagir com o servidor
|-- run_server.py       # Ponto de entrada para iniciar o servidor
|-- requirements.txt    # Dependências do projeto
|-- README.md           # Esta documentação
|-- .gitignore
```

## 🚀 Como Executar

### 1. Pré-requisitos
- Python 3.7+
- Acesso para criar *raw sockets* (geralmente requer privilégios de administrador/root para a sondagem ICMP).

### 2. Instalação

1.  **Clone o repositório:**
    ```bash
    git clone <url_do_repositorio>
    cd network-scanner
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Iniciando o Servidor

O servidor precisa de permissões para criar *raw sockets* para a sondagem ICMP. Portanto, execute-o com `sudo`.

```bash
sudo python3 run_server.py
```
O servidor começará a escutar na porta `35640` e exibirá uma mensagem de confirmação.

### 4. Usando o Cliente

Em um **outro terminal**, use o `client.py` para enviar requisições de varredura.

**Sintaxe:**
```bash
python3 client.py <cidr> [--host <ip>] [--port <porta>] [--community <string>]
```

**Exemplos:**

-   **Varredura Simples (ICMP/SNMP com comunidade 'public'):**
    ```bash
    python3 client.py 192.168.1.0/24
    ```

-   **Varredura em um host específico:**
    ```bash
    python3 client.py 8.8.8.8/32
    ```

-   **Especificando uma comunidade SNMP diferente:**
    ```bash
    python3 client.py 10.10.0.0/22 --community "comunidade-secreta"
    ```

-   **Conectando a um servidor em outro host:**
    ```bash
    python3 client.py 192.168.1.0/24 --host 192.168.1.100
    ```

A resposta do servidor listará os hosts ativos encontrados, indicando se a descoberta foi via `SNMP` (e o `sysName`) ou `ICMP`.
