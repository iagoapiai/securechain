#!/usr/bin/env python3

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "blockchain"))
from blockchain import CHAIN_PATH, validar_cadeia

if not os.path.exists(CHAIN_PATH):
    print("[ERRO] chain.json não encontrado. Gere alguns eventos primeiro.")
    sys.exit(1)

with open(CHAIN_PATH, "r", encoding="utf-8") as f:
    blocos = json.load(f)

if len(blocos) < 2:
    print("[ERRO] A cadeia precisa de pelo menos 2 blocos para a demonstração.")
    sys.exit(1)

alvo = int(sys.argv[1]) if len(sys.argv) > 1 else 1
alvo = min(alvo, len(blocos) - 1)

print(f"[] Bloco {alvo} ANTES do ataque:")
print(f"    evento: {blocos[alvo]['evento']}")

blocos[alvo]["evento"] = "EVENTO FALSIFICADO PELO INVASOR"
with open(CHAIN_PATH, "w", encoding="utf-8") as f:
    json.dump(blocos, f, indent=2, ensure_ascii=False)

print(f"[] Bloco {alvo} foi ADULTERADO diretamente no chain.json.\n")
print("[] Executando validação da blockchain (RF07)...\n")

validar_cadeia()

print("\n[] Para restaurar a cadeia original:")
print("    cp blockchain/chain.json.bak blockchain/chain.json")