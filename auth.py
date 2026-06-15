#!/usr/bin/env python3

import getpass
import hashlib
import json
import os
import re
import secrets
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = BASE_DIR
sys.path.insert(0, os.path.join(RAIZ, "blockchain"))
from blockchain import registrar_evento  # noqa: E402

ARQ_USUARIOS = os.path.join(RAIZ, "usuarios", "usuarios.json")
PERFIS_VALIDOS = ("admin", "analista", "visitante")
ITERACOES = 200_000

def _carregar_usuarios():
    if os.path.exists(ARQ_USUARIOS):
        with open(ARQ_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _salvar_usuarios(usuarios):
    os.makedirs(os.path.dirname(ARQ_USUARIOS), exist_ok=True)
    with open(ARQ_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(ARQ_USUARIOS, 0o600)
    except PermissionError:
        pass

def gerar_hash_senha(senha, salt=None):
    if salt is None:
        salt = secrets.token_hex(16) 
    h = hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), bytes.fromhex(salt), ITERACOES
    )
    return salt, h.hex()


def verificar_senha(senha, salt, hash_armazenado):
    _, h = gerar_hash_senha(senha, salt)
    return secrets.compare_digest(h, hash_armazenado)

def usuario_valido(nome):
    return bool(re.fullmatch(r"[a-zA-Z0-9._]{3,32}", nome))


def senha_valida(senha):
    return (
        len(senha) >= 8
        and re.search(r"[a-zA-Z]", senha)
        and re.search(r"[0-9]", senha)
    )

def cadastrar(nome, senha, perfil, executor="sistema"):
    usuarios = _carregar_usuarios()

    if not usuario_valido(nome):
        raise ValueError("Nome de usuário inválido (3-32 caracteres: a-z, 0-9, '.', '_').")
    if nome in usuarios:
        raise ValueError(f"Usuário '{nome}' já existe.")
    if perfil not in PERFIS_VALIDOS:
        raise ValueError(f"Perfil inválido. Use: {', '.join(PERFIS_VALIDOS)}")
    if not senha_valida(senha):
        raise ValueError("Senha fraca: mínimo 8 caracteres, com letras e números.")

    salt, hash_senha = gerar_hash_senha(senha)
    usuarios[nome] = {"salt": salt, "hash": hash_senha, "perfil": perfil}
    _salvar_usuarios(usuarios)
    registrar_evento(f"USUARIO_CRIADO: '{nome}' (perfil={perfil}) por '{executor}'")
    return True


def remover(nome, executor="sistema"):
    usuarios = _carregar_usuarios()
    if nome not in usuarios:
        raise ValueError(f"Usuário '{nome}' não existe.")
    del usuarios[nome]
    _salvar_usuarios(usuarios)
    registrar_evento(f"USUARIO_REMOVIDO: '{nome}' por '{executor}'")
    return True


def login(nome, senha):
    usuarios = _carregar_usuarios()
    dados = usuarios.get(nome)

    if dados and verificar_senha(senha, dados["salt"], dados["hash"]):
        registrar_evento(f"LOGIN_SUCESSO: usuario '{nome}' (perfil={dados['perfil']})")
        return {"usuario": nome, "perfil": dados["perfil"]}

    registrar_evento(f"ACESSO_NEGADO: tentativa de login para usuario '{nome}'")
    return None


def listar_usuarios():
    usuarios = _carregar_usuarios()
    return {nome: d["perfil"] for nome, d in usuarios.items()}


if __name__ == "__main__":
    print("== SecureChain Audit :: Autenticação ==")
    print("1) Cadastrar usuário   2) Login   3) Listar usuários")
    opcao = input("Opção: ").strip()

    if opcao == "1":
        nome = input("Usuário: ").strip()
        perfil = input(f"Perfil {PERFIS_VALIDOS}: ").strip()
        senha = getpass.getpass("Senha: ")
        try:
            cadastrar(nome, senha, perfil)
            print(f"[OK] Usuário '{nome}' cadastrado e registrado na blockchain.")
        except ValueError as e:
            print(f"[ERRO] {e}")
    elif opcao == "2":
        nome = input("Usuário: ").strip()
        senha = getpass.getpass("Senha: ")
        sessao = login(nome, senha)
        if sessao:
            print(f"[OK] Bem-vindo, {sessao['usuario']} (perfil: {sessao['perfil']})")
        else:
            print("[ERRO] Usuário ou senha inválidos. Tentativa registrada na blockchain.")
    elif opcao == "3":
        for nome, perfil in listar_usuarios().items():
            print(f"  {nome:<20} {perfil}")
