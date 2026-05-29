import argparse
import random
import socket
import time
import threading
from datetime import datetime
from pathlib import Path

from protocol import GRANT, RELEASE, REQUEST, enviar_socket, ler_socket

RESULTADO = Path("resultado.txt")


def gerar_tempo(perfil: str) -> float:
    """
    Define o tempo aleatório de retenção da RC
    conforme o perfil do processo.
    """

    if perfil == "normal":
        return 2

    if perfil == "guloso":
        return random.uniform(3, 6)

    if perfil == "misto":
        # às vezes curto, às vezes muito longo
        if random.random() < 0.7:
            return 2
        return random.uniform(3, 6)

    raise ValueError("Perfil inválido")


def regiao_critica(process_id: int) -> None:

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    linha = f"{process_id} {agora}\n"

    with RESULTADO.open("a", encoding="utf-8") as f:
        f.write(linha)


def thread_processo(
    process_id: int,
    host: str,
    port: int,
    repeticoes: int,
    perfil: str
) -> None:
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print(
        f"[proc {process_id}] conectado "
        f"(perfil={perfil})"
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

            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            tempo = gerar_tempo(perfil)
            print(
                f"[proc {process_id}] "
                f"RC ({perfil}): {agora} "
                f"(sleep {tempo:.2f}s)"
            )
            
            time.sleep(tempo)

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

    parser.add_argument(
        "--perfil",
        nargs="+",
        choices=["normal", "guloso", "misto"],
        default=["normal"],
        help="Lista perfis de retenção da região crítica (repete o último para preencher até n)"
    )

    args = parser.parse_args()

    # repete o último para preencher
    perfis = list(args.perfil)
    while len(perfis) < args.n:
        perfis.append(perfis[-1])

    threads = []

    for process_id in range(1, args.n + 1):

        t = threading.Thread(
            target=thread_processo,
            args=(
                process_id,
                args.host,
                args.port,
                args.r,
                perfis[process_id - 1]
            )
        )

        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("\nTodos os processos terminaram.")


if __name__ == "__main__":
    main()