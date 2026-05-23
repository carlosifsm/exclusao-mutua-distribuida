"""
Coordenador centralizado (3 threads):
  1) aceita conexões TCP;
  2) executa o algoritmo (fila FIFO + GRANT/RELEASE);
  3) interface no terminal (fila, atendimentos, sair).

Log em coordenador.log: instante, tipo, origem, destino.
"""

import argparse
import select
import socket
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

from protocol import F, GRANT, NOME_POR_ID, RELEASE, REQUEST, decodificar, enviar_socket

# --- estado compartilhado (RLock: tentar_conceder é chamado com lock já held) ---
lock = threading.RLock()
fila = deque()                    # pedidos FIFO (process_id)
em_uso = None                     # processo na região crítica
conexoes = {}                     # process_id -> socket
sockets_ativos = []               # todos os sockets para select()
atendimentos = defaultdict(int)   # quantas vezes cada processo recebeu GRANT
rodando = True

LOG_PATH = Path("coordenador.log")
log_lock = threading.Lock()


def registrar_log(direcao: str, msg_id: int, origem, destino) -> None:
    """Grava RECV/SEND com instante, tipo e processos origem/destino."""
    instante = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    tipo = NOME_POR_ID[msg_id]
    linha = f"{instante} {direcao} {tipo} origem={origem} destino={destino}\n"
    with log_lock:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(linha)


def tentar_conceder() -> None:
    """Concede ao primeiro da fila se o recurso está livre. Requer lock."""
    global em_uso
    with lock:
        if em_uso is not None or not fila:
            return
        proximo = fila.popleft()
        em_uso = proximo
        atendimentos[proximo] += 1
        conn = conexoes.get(proximo)
    if conn is None:
        return
    registrar_log("SEND", GRANT, "coord", proximo)
    enviar_socket(conn, GRANT, proximo)
    print(f"[coord] GRANT -> processo {proximo}")


def processar_mensagem(msg_id: int, process_id: int) -> None:
    """Trata REQUEST/RELEASE."""
    global em_uso

    if msg_id == REQUEST:
        registrar_log("RECV", REQUEST, process_id, "coord")
        with lock:
            print(f"[coord] REQUEST de {process_id} | fila={list(fila)} em_uso={em_uso}")
            fila.append(process_id)
        tentar_conceder()

    elif msg_id == RELEASE:
        registrar_log("RECV", RELEASE, process_id, "coord")
        print(f"[coord] RELEASE de {process_id}")
        with lock:
            if em_uso == process_id:
                em_uso = None
            else:
                print(f"[coord] aviso: RELEASE de {process_id} com em_uso={em_uso}")
        tentar_conceder()

    else:
        print(f"[coord] mensagem ignorada: id={msg_id}")


def thread_aceitar(servidor: socket.socket) -> None:
    """Thread 1: recebe novas conexões e registra socket para o select."""
    while rodando:
        try:
            servidor.settimeout(0.5)
            conn, addr = servidor.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        print(f"[coord] conexão de {addr}")
        with lock:
            sockets_ativos.append(conn)
            # process_id será associado na primeira mensagem


def thread_algoritmo() -> None:
    """Thread 2: lê mensagens dos clientes (select) e executa exclusão mútua."""
    while rodando:
        with lock:
            copia = list(sockets_ativos)

        if not copia:
            time.sleep(0.05)
            continue

        prontos, _, erros = select.select(copia, [], copia, 0.5)

        for conn in prontos + erros:
            try:
                dados = b""
                while len(dados) < F:
                    pedaco = conn.recv(F - len(dados))
                    if not pedaco:
                        raise ConnectionError()
                    dados += pedaco
                msg_id, process_id = decodificar(dados)
            except (ConnectionError, OSError):
                remover_socket(conn)
                continue

            with lock:
                conexoes[process_id] = conn
                processar_mensagem(msg_id, process_id)


def remover_socket(conn: socket.socket) -> None:
    with lock:
        if conn in sockets_ativos:
            sockets_ativos.remove(conn)
        for pid, s in list(conexoes.items()):
            if s is conn:
                del conexoes[pid]
                print(f"[coord] processo {pid} desconectou")


def thread_interface() -> None:
    """Thread 3: comandos do terminal."""
    global rodando
    print("\nComandos: 1=fila | 2=atendimentos | 3=encerrar\n")
    while rodando:
        try:
            cmd = input("coord> ").strip()
        except EOFError:
            break

        if cmd == "1":
            with lock:
                print(f"Fila atual: {list(fila)} | em_uso={em_uso}")
        elif cmd == "2":
            with lock:
                if atendimentos:
                    for pid in sorted(atendimentos):
                        print(f"  processo {pid}: {atendimentos[pid]} atendimento(s)")
                else:
                    print("  nenhum atendimento registrado")
        elif cmd == "3":
            print("[coord] encerrando...")
            rodando = False
            break
        else:
            print("Comando inválido. Use 1, 2 ou 3.")


def main() -> None:
    global rodando

    parser = argparse.ArgumentParser(description="Coordenador de exclusão mútua")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    LOG_PATH.write_text("", encoding="utf-8")

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((args.host, args.port))
    servidor.listen()
    print(f"[coord] escutando {args.host}:{args.port} (F={F} bytes)")

    t1 = threading.Thread(target=thread_aceitar, args=(servidor,), daemon=True)
    t2 = threading.Thread(target=thread_algoritmo, daemon=True)
    t1.start()
    t2.start()

    try:
        while rodando:
            time.sleep(0.2)
    except KeyboardInterrupt:
        rodando = False

    rodando = False
    servidor.close()
    with lock:
        for s in sockets_ativos:
            s.close()
    print("[coord] finalizado")
    sys.exit(0)


if __name__ == "__main__":
    main()
