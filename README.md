# Exclusão Mútua Distribuída — Algoritmo Centralizado

Trabalho de Sistemas Distribuídos usando:
- sockets TCP;
- coordenador central;
- fila FIFO;
- mensagens REQUEST, GRANT e RELEASE.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `protocol.py` | Protocolo das mensagens |
| `coordinator.py` | Coordenador |
| `client.py` | Processo cliente |
| `resultado.txt` | Arquivo compartilhado gerado na execução |

---

## Mensagens

Formato:

```text
MSG_ID|PROCESS_ID|000...
```

Tipos:

| ID | Tipo |
|---|---|
| 1 | REQUEST |
| 2 | GRANT |
| 3 | RELEASE |

Exemplo:

```text
1|3|00000000000
```

---

## Como funciona

1. Cliente envia REQUEST.
2. Coordenador coloca na fila.
3. Coordenador envia GRANT para um cliente por vez.
4. Cliente escreve em `resultado.txt`.
5. Cliente espera `k` segundos.
6. Cliente envia RELEASE.

---

## Executar

### Coordenador

```bash
py coordinator.py
```

---

### Cliente

Exemplo:

```bash
py client.py --id 1 -r 5 -k 1
```

Parâmetros:
- `--id` → identificador do processo
- `-r` → número de repetições
- `-k` → tempo dentro da região crítica

---

## Resultado esperado

Arquivo `resultado.txt`:

```text
1 2026-05-21 14:30:01.042
2 2026-05-21 14:30:02.113
3 2026-05-21 14:30:03.201
```

Cada processo deve escrever `r` vezes.