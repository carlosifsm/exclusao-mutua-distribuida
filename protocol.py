"""
Protocolo de mensagens (trabalho): F bytes fixos, campos separados por |.

Formato: MSG_ID|PROCESS_ID|000...0
Exemplo (F=16): REQUEST do processo 3 -> "1|3|00000000000"
"""

# Tamanho fixo F em bytes
F = 16

# Identificadores de mensagem (campo 1)
REQUEST = 1
GRANT = 2
RELEASE = 3

NOME_POR_ID = {REQUEST: "REQUEST", GRANT: "GRANT", RELEASE: "RELEASE"}


def codificar(msg_id: int, process_id: int) -> bytes:
    """Monta string com padding de zeros até F bytes."""
    prefixo = f"{msg_id}|{process_id}|"
    if len(prefixo) > F:
        raise ValueError(f"Prefixo maior que F={F}: {prefixo}")
    resto = F - len(prefixo)
    texto = prefixo + ("0" * resto)
    return texto.encode("utf-8")


def decodificar(dados: bytes) -> tuple[int, int]:
    """Lê MSG_ID e PROCESS_ID dos primeiros campos."""
    if len(dados) != F:
        raise ValueError(f"Esperado {F} bytes, veio {len(dados)}")
    texto = dados.decode("utf-8")
    partes = texto.split("|")
    return int(partes[0]), int(partes[1])


def ler_socket(sock) -> tuple[int, int]:
    """Recebe exatamente F bytes do socket."""
    dados = b""
    while len(dados) < F:
        pedaco = sock.recv(F - len(dados))
        if not pedaco:
            raise ConnectionError("Conexão encerrada")
        dados += pedaco
    return decodificar(dados)


def enviar_socket(sock, msg_id: int, process_id: int) -> None:
    sock.sendall(codificar(msg_id, process_id))
