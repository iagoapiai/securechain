#!/usr/bin/env python3

import hashlib
import json
import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "blockchain"))
from blockchain import registrar_evento  # noqa: E402

DIR_DOCUMENTOS = os.path.join(BASE_DIR, "documentos")
ARQ_BASELINE = os.path.join(BASE_DIR, "logs", "hashes_baseline.json")
ARQ_LOG = os.path.join(BASE_DIR, "logs", "integridade.log")


def _log(msg):
    linha = f"[{datetime.now().isoformat()}] {msg}"
    print(linha)
    os.makedirs(os.path.dirname(ARQ_LOG), exist_ok=True)
    with open(ARQ_LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def hash_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def escanear_diretorio():
    hashes = {}
    for raiz, _, arquivos in os.walk(DIR_DOCUMENTOS):
        for nome in arquivos:
            caminho = os.path.join(raiz, nome)
            relativo = os.path.relpath(caminho, DIR_DOCUMENTOS)
            try:
                hashes[relativo] = hash_arquivo(caminho)
            except (PermissionError, FileNotFoundError) as e:
                _log(f"[AVISO] Não foi possível ler '{relativo}': {e}")
    return hashes


def inicializar():
    os.makedirs(DIR_DOCUMENTOS, exist_ok=True)
    hashes = escanear_diretorio()
    os.makedirs(os.path.dirname(ARQ_BASELINE), exist_ok=True)
    with open(ARQ_BASELINE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)
    _log(f"Baseline criada com {len(hashes)} arquivo(s) monitorado(s).")
    registrar_evento(f"MONITOR_INIT: baseline de integridade criada ({len(hashes)} arquivos)")


def verificar():
    if not os.path.exists(ARQ_BASELINE):
        _log("[ERRO] Baseline não encontrada. Execute: python3 monitor.py init")
        return False

    with open(ARQ_BASELINE, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    atual = escanear_diretorio()
    alteracoes = []

    for arq, h_ref in baseline.items():
        if arq not in atual:
            alteracoes.append(("EXCLUIDO", arq))
        elif atual[arq] != h_ref:
            alteracoes.append(("ALTERADO", arq))

    for arq in atual:
        if arq not in baseline:
            alteracoes.append(("INCLUIDO", arq))

    if not alteracoes:
        _log(f"[OK] Integridade verificada: {len(atual)} arquivo(s) sem alterações.")
        return True

    _log("⚠ " * 10)
    _log("⚠ ALERTA DE INTEGRIDADE: inconsistências detectadas em documentos/")
    for tipo, arq in alteracoes:
        msg = f"INTEGRIDADE_{tipo}: arquivo '{arq}' em documentos/"
        _log(f"  -> {tipo}: {arq}")
        registrar_evento(msg)
    _log("⚠ Eventos registrados na blockchain de auditoria.")
    return False


def watch(intervalo=30):
    _log(f"Monitoramento contínuo iniciado (intervalo: {intervalo}s). Ctrl+C para sair.")
    try:
        while True:
            verificar()
            time.sleep(intervalo)
    except KeyboardInterrupt:
        _log("Monitoramento encerrado pelo usuário.")


if __name__ == "__main__":
    comando = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if comando == "init":
        inicializar()
    elif comando == "verificar":
        ok = verificar()
        sys.exit(0 if ok else 2)
    elif comando == "watch":
        segundos = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        watch(segundos)
    else:
        print(__doc__)
        sys.exit(1)