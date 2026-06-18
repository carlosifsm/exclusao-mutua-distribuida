import argparse
import random
import socket
import time
import threading
from datetime import datetime
from pathlib import Path

from protocol import GRANT, RELEASE, REQUEST, enviar_socket, ler_socket

RESULTADO = Path("resultado.txt")

def regiao_critica(process_id: int) -> None:

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    linha = f"{process_id} {agora}\n"

    with RESULTADO.open("a", encoding="utf-8") as f:
        f.write(linha)
    
    time.sleep(1)

def thread_processo(
    process_id: int,
    host: str,
    port: int,
    repeticoes: int,
) -> None:
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print(
        f"[proc {process_id}] conectado "
    )

    try:

        for i in range(1, repeticoes + 1):

            print(f"[proc {process_id}] {i}/{repeticoes} REQUEST")

            enviar_socket(sock, REQUEST, process_id)

            msg_id, pid = ler_socket(sock)

            if msg_id != GRANT or pid != process_id:
                print(
                    f"[proc {process_id}] erro: "
                    f"esperava GRANT, veio {msg_id}|{pid}"
                )
                break

            regiao_critica(process_id)

            enviar_socket(sock, RELEASE, process_id)
            print(f"[proc {process_id}] RELEASE")
            
            time.sleep(random.uniform(1, 5))

    finally:

        sock.close()

        print(f"[proc {process_id}] terminou")
    

def main() -> None:

    parser = argparse.ArgumentParser(description="Processo cliente")

    parser.add_argument("--host", default="127.0.0.1")

    parser.add_argument("--port", type=int, default=9000)

    parser.add_argument(
        "-n",
        type=int,
        default=3,
        help="Quantidade de threads cliente"
    )

    parser.add_argument(
        "-r",
        type=int,
        default=3,
        help="Quantidade de acessos à RC"
    )

    args = parser.parse_args()

    threads = []

    for process_id in range(1, args.n + 1):

        t = threading.Thread(
            target=thread_processo,
            args=(
                process_id,
                args.host,
                args.port,
                args.r,
            )
        )

        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\nTodos os processos terminaram.")


if __name__ == "__main__":
    main()