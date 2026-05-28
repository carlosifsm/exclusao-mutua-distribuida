# Exclusão Mútua Distribuída — Algoritmo Centralizado

Este trabalho implementa um algoritmo de exclusão mútua distribuída utilizando sockets TCP e um coordenador central responsável por controlar o acesso à região crítica. Os processos clientes se comunicam com o coordenador através das mensagens REQUEST, GRANT e RELEASE, enquanto o coordenador mantém uma fila FIFO para garantir atendimento ordenado.

O projeto é composto pelos seguintes arquivos:

| Arquivo | Descrição |
|---|---|
| `protocol.py` | Definição do protocolo de mensagens |
| `coordinator.py` | Coordenador central |
| `client.py` | Processos clientes |
| `resultado.txt` | Arquivo compartilhado gerado durante a execução |

As mensagens seguem o formato:

```text
MSG_ID|PROCESS_ID|000...
```

Os tipos utilizados são:
- `1` → REQUEST
- `2` → GRANT
- `3` → RELEASE

O funcionamento do sistema ocorre da seguinte forma: o cliente envia um REQUEST ao coordenador, que adiciona o processo na fila de espera. Quando o recurso está disponível, o coordenador envia um GRANT autorizando a entrada na região crítica. O cliente então escreve em `resultado.txt`, permanece na região crítica por um tempo aleatório definido pelo seu perfil e, ao finalizar, envia um RELEASE liberando o recurso para o próximo processo da fila.

O arquivo client.py aceita os seguintes parâmetros de execução:
| Parâmetro | Descrição |
|---|---|
| -n | Quantidade de clientes criados |
| -r | Quantidade de acessos à região crítica por cliente |
| --perfil | Lista perfis de retenção da região crítica (repete o último para preencher até n) |


Os clientes podem utilizar diferentes perfis de retenção da região crítica:
- `normal` → tempos curtos;
- `guloso` → tempos longos;
- `misto` → alternância entre tempos curtos e longos.

Para executar o coordenador:

```bash
py coordinator.py
```

Para modo silencioso, sem imprimir eventos no terminal:

```bash
py coordinator.py --quiet
```

Exemplo de execução de 3 cliente e 5 requisições cada:

```bash
py client.py -n 3 -r 5 --perfil normal
```

Também é possível executar clientes com outros perfis:

```bash
py client.py -n 3 -r 5 --perfil guloso normal
```

O arquivo `resultado.txt` deve apresentar entradas ordenadas sem acessos simultâneos à região crítica, validando o funcionamento da exclusão mútua.