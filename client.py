import argparse
import random
import socket
import time
from datetime import datetime
from pathlib import Path

from protocol import GRANT, RELEASE, REQUEST, enviar_socket, ler_socket

RESULTADO = Path("resultado.txt")


def regiao_critica(process_id: int) -> None:
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    linha = f"{process_id} {agora}\n"

    with RESULTADO.open("a", encoding="utf-8") as f:
        f.write(linha)

    tempo = random.uniform(1, 5)

    print(f"[proc {process_id}] RC: {agora} (sleep {tempo:.2f}s)")

    time.sleep(tempo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Processo cliente")

    parser.add_argument(
        "--id",
        type=int,
        required=True,
        help="Identificador do processo"
    )

    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)

    parser.add_argument(
        "-r",
        type=int,
        default=3,
        help="Repetições na região crítica"
    )

    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((args.host, args.port))

    print(f"[proc {args.id}] conectado")

    try:
        for i in range(1, args.r + 1):

            print(f"[proc {args.id}] {i}/{args.r} REQUEST")

            enviar_socket(sock, REQUEST, args.id)

            msg_id, pid = ler_socket(sock)

            if msg_id != GRANT or pid != args.id:
                print(
                    f"[proc {args.id}] erro: esperava GRANT, veio {msg_id}|{pid}"
                )
                break

            regiao_critica(args.id)

            print(f"[proc {args.id}] RELEASE")

            enviar_socket(sock, RELEASE, args.id)

    finally:
        sock.close()
        print(f"[proc {args.id}] terminou")


if __name__ == "__main__":
    main()