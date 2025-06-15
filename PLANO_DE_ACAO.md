# Plano de Ação: Implementação do Scanner de Rede de Alta Concorrência

Este documento transforma o plano arquitetural em um guia de implementação passo a passo. Utilize-o como um checklist para desenvolver, testar e validar a aplicação.

---

### Fase 1: Estrutura do Projeto e Configuração Inicial

O objetivo desta fase é estabelecer uma base de projeto sólida e profissional.

- [X] **Criar Estrutura de Diretórios**: Organizar o projeto conforme o layout proposto.
  ```
  /network-scanner
  |-- /scanner
  |   |-- __init__.py
  |   |-- server.py
  |   |-- probes.py
  |   |-- utils.py
  |-- /tests
  |   |-- test_server.py
  |   |-- test_probes.py
  |-- client.py
  |-- run_server.py
  |-- requirements.txt
  |-- README.md
  |-- .gitignore
  ```
- [ ] **Configurar Ambiente**: Inicializar um ambiente virtual (`python -m venv venv`).
- [X] **Gerenciar Dependências**: Criar `requirements.txt` e adicionar as bibliotecas necessárias: `pysnmp`, `icmplib`, `pytest`.
- [X] **Criar README Inicial**: Esboçar o arquivo `README.md`.
- [X] **Configurar Git**: Criar um arquivo `.gitignore` adequado para projetos Python.

---

### Fase 2: Implementação do Servidor TCP Básico com `asyncio`

Foco em criar o esqueleto funcional do servidor, capaz de aceitar conexões.

- [X] **Ponto de Entrada**: Implementar `run_server.py` para iniciar o servidor.
- [X] **Servidor `asyncio`**: Em `scanner/server.py`, implementar o servidor TCP usando `asyncio.start_server`.
- [X] **Manipulador de Cliente**: Criar a corrotina `handle_client` que, inicialmente, apenas aceita uma conexão, lê uma mensagem e a imprime no console do servidor.
- [X] **Robustez do Servidor**:
    - [X] Adicionar tratamento para `OSError: Address already in use` usando a opção `reuse_address=True`.
    - [X] Implementar o desligamento gracioso do servidor ao capturar `KeyboardInterrupt`.

---

### Fase 3: Lógica de Negócio - Análise de CIDR e Tratamento de Erros

Implementar a lógica central de interpretação da requisição do cliente.

- [X] **Utilitário de Rede**: Em `scanner/utils.py`, criar a função `parse_cidr(cidr_string)` que utiliza o módulo `ipaddress`.
- [X] **Geração de Hosts**: A função deve validar o CIDR e retornar uma lista de strings com todos os IPs de hosts válidos na rede.
- [X] **Integração com Servidor**: Integrar a chamada a `parse_cidr` no `handle_client`.
- [X] **Tratamento de Erro de Cliente**:
    - [X] Envolver a chamada `parse_cidr` em um bloco `try...except ValueError`.
    - [X] Em caso de erro, enviar uma mensagem clara (ex: "ERRO: Notação CIDR inválida") de volta ao cliente antes de fechar a conexão.

---

### Fase 4: Implementação das Sondagens de Rede (Probes)

Desenvolver os "sensores" da aplicação, focando em implementações nativas e robustas.

- [X] **Sondagem ICMP (Ping)**:
    - [X] Em `scanner/probes.py`, implementar a função `probe_icmp(ip)` usando `icmplib`.
    - [X] Garantir que a função capture `PermissionError` e retorne um resultado que indique a falha de permissão.
- [X] **Sondagem SNMP**:
    - [X] Em `scanner/probes.py`, implementar a função `probe_snmp(ip, community)` usando a API `asyncio` do `pysnmp`.
    - [X] Implementar a verificação rigorosa de `errorIndication` para tratar:
        - [X] Timeouts (sem resposta).
        - [X] Falhas de autenticação (`UnknownCommunityName`).
    - [X] A função deve extrair e retornar o `sysName` em caso de sucesso.

---

### Fase 5: Orquestração da Varredura Paralela Híbrida

Integrar todos os componentes, implementando o modelo de concorrência de dois níveis.

- [X] **Função de Trabalho (Worker)**: Em `scanner/server.py`, criar a função `scan_host(ip, snmp_community)`.
- [X] **Lógica de Fallback**: Implementar a lógica em `scan_host`:
    1. Tentar a sondagem SNMP.
    2. Se SNMP falhar (qualquer erro), tentar a sondagem ICMP.
    3. Retornar `(ip, sysName)` em caso de sucesso do SNMP, `(ip, None)` em sucesso do ICMP, ou `None` se ambos falharem.
- [X] **Executor de Threads**: Em `handle_client`, inicializar um `concurrent.futures.ThreadPoolExecutor`.
- [X] **Execução Paralela**: Usar `loop.run_in_executor` com o `executor.map` para aplicar `scan_host` a toda a lista de IPs.
- [X] **Coleta e Resposta**:
    - [X] Coletar os resultados da varredura.
    - [X] Filtrar os resultados `None`.
    - [X] Formatar a resposta (um IP por linha, com `sysName` se disponível).
    - [X] Enviar a resposta formatada ao cliente, usando `writer.write()` e `await writer.drain()`.
- [X] **Resiliência da Conexão**: Envolver a lógica de leitura em `handle_client` em um `try...except` para `asyncio.IncompleteReadError` e `ConnectionResetError` para lidar com desconexões abruptas.

---

### Fase 6: Validação e Testes (Exploração da Aplicação)

Provar a correção e a robustez da aplicação através de testes automatizados e manuais.

- [X] **Configurar `pytest`**: Preparar o ambiente de testes.
- [X] **Testes Unitários**:
    - [X] Em `tests/test_utils.py`, testar a função `parse_cidr` com entradas válidas e inválidas.
- [X] **Testes de Integração**:
    - [X] Em `tests/test_server.py`, criar testes que iniciam o servidor e se conectam a ele.
    - [X] **Cenário Ideal**: Testar uma varredura em uma rede mock onde os hosts respondem a ICMP e SNMP.
    - [X] **Teste de Fallback**: Testar com um host que só responde a ICMP, verificando se o fallback funciona.
    - [X] **Teste de Erro de Cliente**: Testar o envio de um CIDR inválido.
- [X] **Cliente de Teste**: Desenvolver `client.py` para permitir testes manuais e demonstrações fáceis.

---

### Fase 7: Testes de Estresse e Análise de Desempenho

Levar a aplicação aos seus limites para entender seu comportamento sob carga.

- [X] **Escalabilidade Vertical**:
    - [X] Realizar uma varredura em uma rede grande (ex: /20 ou /16) para analisar o uso de memória e CPU.
    - [X] Medir o tempo total da varredura e identificar gargalos.
- [X] **Resiliência a Redes Instáveis**:
    - [X] Testar contra uma rede com hosts lentos (alta latência) e hosts que não respondem (timeout).
    - [X] Validar que o servidor permanece responsivo a outros clientes durante essa varredura.
- [X] **Escalabilidade Horizontal (Concorrência)**:
    - [X] Criar um script que simula 50-100 clientes se conectando e requisitando varreduras simultaneamente.
    - [X] Monitorar a performance do servidor `asyncio`.
- [X] **Teste de Segurança/Configuração**:
    - [X] Executar uma varredura com uma comunidade SNMP incorreta e verificar se os logs do servidor registram o erro de autenticação específico e se o fallback para ICMP ocorre corretamente.

---

### Fase 8: Documentação e Finalização

Empacotar o projeto de forma profissional.

- [X] **Completar `README.md`**: Detalhar todas as seções: Visão Geral, Funcionalidades, Instalação (`pip install -r requirements.txt`), Execução (`python run_server.py`) e Uso (`python client.py <host> <port>`).
- [X] **Revisão de Código**: Adicionar `docstrings` e comentários onde a lógica for complexa.
- [X] **Preparação para Defesa**: Revisar as perguntas e respostas da seção 4.3 do plano original e refinar as respostas com base na implementação final.
