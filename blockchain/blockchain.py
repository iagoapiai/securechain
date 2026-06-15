#!/usr/bin/env python3


import hashlib
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAIN_PATH = os.path.join(BASE_DIR, "chain.json")


class Bloco:

    def __init__(self, bloco_id, timestamp, evento, hash_anterior, hash_atual=None):
        self.id = bloco_id
        self.timestamp = timestamp
        self.evento = evento
        self.hash_anterior = hash_anterior
        self.hash_atual = hash_atual if hash_atual else self.calcular_hash()

    def calcular_hash(self):
        """Calcula SHA-256 sobre TODOS os campos do bloco (exceto o próprio hash)."""
        conteudo = f"{self.id}|{self.timestamp}|{self.evento}|{self.hash_anterior}"
        return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()

    def para_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "evento": self.evento,
            "hash_anterior": self.hash_anterior,
            "hash_atual": self.hash_atual,
        }

    @staticmethod
    def de_dict(d):
        return Bloco(
            bloco_id=d["id"],
            timestamp=d["timestamp"],
            evento=d["evento"],
            hash_anterior=d["hash_anterior"],
            hash_atual=d["hash_atual"],
        )


class Blockchain:

    def __init__(self, caminho=CHAIN_PATH):
        self.caminho = caminho
        self.blocos = []
        self._carregar()

    def _carregar(self):
        if os.path.exists(self.caminho):
            try:
                with open(self.caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.blocos = [Bloco.de_dict(b) for b in dados]
            except (json.JSONDecodeError, KeyError):
                print("[ERRO] chain.json corrompido ou em formato inválido.")
                self.blocos = []
        if not self.blocos:
            self._criar_genesis()

    def _salvar(self):
        with open(self.caminho, "w", encoding="utf-8") as f:
            json.dump([b.para_dict() for b in self.blocos], f, indent=2, ensure_ascii=False)

    def _criar_genesis(self):
        """Cria o bloco inicial (gênesis) da cadeia."""
        genesis = Bloco(
            bloco_id=0,
            timestamp=datetime.now().isoformat(),
            evento="GENESIS - Inicializacao da blockchain SecureChain Audit",
            hash_anterior="0" * 64,
        )
        self.blocos = [genesis]
        self._salvar()
        print("[OK] Bloco gênesis criado.")

    def adicionar_evento(self, evento):
        ultimo = self.blocos[-1]
        novo = Bloco(
            bloco_id=ultimo.id + 1,
            timestamp=datetime.now().isoformat(),
            evento=evento,
            hash_anterior=ultimo.hash_atual,
        )
        self.blocos.append(novo)
        self._salvar()
        return novo

    def listar(self):
        for b in self.blocos:
            print(f"[{b.id:04d}] {b.timestamp} | {b.evento}")
            print(f"       hash_anterior: {b.hash_anterior[:32]}...")
            print(f"       hash_atual:    {b.hash_atual[:32]}...")


def registrar_evento(evento):
    chain = Blockchain()
    bloco = chain.adicionar_evento(evento)
    return bloco

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == "add" and len(sys.argv) >= 3:
        bloco = registrar_evento(" ".join(sys.argv[2:]))
        print(f"[OK] Bloco {bloco.id} registrado: {bloco.evento}")
    elif comando == "listar":
        Blockchain().listar()
    else:
        print(__doc__)
        sys.exit(1)