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

    def validar(self):
        problemas = []
        for i, bloco in enumerate(self.blocos):
            if bloco.calcular_hash() != bloco.hash_atual:
                problemas.append(
                    f"Bloco {bloco.id}: hash recalculado difere do armazenado (conteúdo ADULTERADO)."
                )
            if i > 0:
                anterior = self.blocos[i - 1]
                if bloco.hash_anterior != anterior.hash_atual:
                    problemas.append(
                        f"Bloco {bloco.id}: hash_anterior não corresponde ao hash_atual "
                        f"do bloco {anterior.id} (ENCADEAMENTO QUEBRADO)."
                    )
            if i > 0 and bloco.id != self.blocos[i - 1].id + 1:
                problemas.append(
                    f"Bloco {bloco.id}: identificador fora de sequência (possível remoção/inserção de blocos)."
                )
        return (len(problemas) == 0, problemas)

    def listar(self):
        for b in self.blocos:
            print(f"[{b.id:04d}] {b.timestamp} | {b.evento}")
            print(f"       hash_anterior: {b.hash_anterior[:32]}...")
            print(f"       hash_atual:    {b.hash_atual[:32]}...")


def registrar_evento(evento):
    chain = Blockchain()
    bloco = chain.adicionar_evento(evento)
    return bloco


def validar_cadeia(verbose=True):
    chain = Blockchain()
    ok, problemas = chain.validar()
    if verbose:
        if ok:
            print(f"[OK] Blockchain íntegra. Total de blocos: {len(chain.blocos)}")
        else:
            print("=" * 70)
            print("⚠  ALERTA DE SEGURANÇA: BLOCKCHAIN CORROMPIDA  ⚠")
            print("   Notifique o ADMINISTRADOR imediatamente.")
            print("=" * 70)
            for p in problemas:
                print(f"  -> {p}")
    return ok, problemas


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 blockchain.py [add <evento> | listar | validar]")
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == "add" and len(sys.argv) >= 3:
        bloco = registrar_evento(" ".join(sys.argv[2:]))
        print(f"[OK] Bloco {bloco.id} registrado: {bloco.evento}")
    elif comando == "listar":
        Blockchain().listar()
    elif comando == "validar":
        ok, _ = validar_cadeia()
        sys.exit(0 if ok else 2)
    else:
        print("Uso: python3 blockchain.py [add <evento> | listar | validar]")
        sys.exit(1)