#!/usr/bin/env python3

import os
import subprocess
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE_DIR)
sys.path.insert(0, os.path.join(RAIZ, "blockchain"))
from blockchain import registrar_evento

DIR_RELATORIOS = os.path.join(BASE_DIR, "relatorios")

COMANDOS = [
    ("USUÁRIOS CONECTADOS (who)", ["who"]),
    ("HISTÓRICO DE LOGINS (last)", ["last", "-n", "20"]),
    ("PORTAS E SERVIÇOS EM ESCUTA (ss -tulpn)", ["ss", "-tulpn"]),
    ("INTERFACES DE REDE (ip a)", ["ip", "a"]),
]


def executar(comando):
    try:
        resultado = subprocess.run(
            comando, capture_output=True, text=True, timeout=15
        )
        saida = resultado.stdout.strip()
        if resultado.stderr.strip():
            saida += "\n[stderr] " + resultado.stderr.strip()
        return saida if saida else "(sem saída)"
    except FileNotFoundError:
        return f"[ERRO] Comando '{comando[0]}' não encontrado neste sistema."
    except subprocess.TimeoutExpired:
        return f"[ERRO] Comando '{comando[0]}' excedeu o tempo limite."


def gerar_relatorio():
    os.makedirs(DIR_RELATORIOS, exist_ok=True)
    agora = datetime.now()
    nome = f"auditoria_{agora.strftime('%Y%m%d_%H%M%S')}.txt"
    caminho = os.path.join(DIR_RELATORIOS, nome)

    linhas = [
        "=" * 72,
        "SECURECHAIN AUDIT - RELATÓRIO DE AUDITORIA DO SISTEMA OPERACIONAL",
        f"Gerado em: {agora.isoformat()}",
        f"Host: {os.uname().nodename} | Sistema: {os.uname().sysname} {os.uname().release}",
        "=" * 72,
        "",
    ]

    for titulo, comando in COMANDOS:
        linhas.append("-" * 72)
        linhas.append(f"## {titulo}")
        linhas.append(f"$ {' '.join(comando)}")
        linhas.append("-" * 72)
        linhas.append(executar(comando))
        linhas.append("")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    try:
        os.chmod(caminho, 0o644)
    except PermissionError:
        pass

    registrar_evento(f"AUDITORIA_SO: relatório gerado ({nome})")
    print(f"[OK] Relatório de auditoria salvo em: {caminho}")
    print("[OK] Evento registrado na blockchain.")
    return caminho


if __name__ == "__main__":
    gerar_relatorio()