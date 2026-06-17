#!/usr/bin/env python3

import getpass
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "blockchain"))

import auth
import monitor
from blockchain import Blockchain, validar_cadeia, registrar_evento

DIR_RELATORIOS = os.path.join(BASE_DIR, "auditoria", "relatorios")

PERMISSOES = {
    "gerenciar_usuarios": ("admin",),
    "monitor_init": ("admin",),
    "monitor_verificar": ("admin", "analista"),
    "auditoria_gerar": ("admin", "analista"),
    "blockchain_validar": ("admin", "analista"),
    "blockchain_listar": ("admin", "analista"),
    "backup_executar": ("admin",),
    "relatorios_ler": ("admin", "analista", "visitante"),
}


def autorizado(sessao, acao):
    ok = sessao["perfil"] in PERMISSOES.get(acao, ())
    if not ok:
        registrar_evento(
            f"ACESSO_NEGADO: usuario '{sessao['usuario']}' "
            f"(perfil={sessao['perfil']}) tentou executar '{acao}'"
        )
        print("[NEGADO] Seu perfil não possui permissão para esta ação. "
              "Tentativa registrada na blockchain.")
    return ok


def acao_gerenciar_usuarios(sessao):
    print("\n  1) Cadastrar usuário  2) Remover usuário  3) Listar usuários")
    op = input("  Opção: ").strip()
    if op == "1":
        nome = input("  Novo usuário: ").strip()
        perfil = input(f"  Perfil {auth.PERFIS_VALIDOS}: ").strip()
        senha = getpass.getpass("  Senha: ")
        try:
            auth.cadastrar(nome, senha, perfil, executor=sessao["usuario"])
            print(f"  [OK] Usuário '{nome}' criado e registrado na blockchain.")
        except ValueError as e:
            print(f"  [ERRO] {e}")
    elif op == "2":
        nome = input("  Usuário a remover: ").strip()
        try:
            auth.remover(nome, executor=sessao["usuario"])
            print(f"  [OK] Usuário '{nome}' removido e registrado na blockchain.")
        except ValueError as e:
            print(f"  [ERRO] {e}")
    elif op == "3":
        for nome, perfil in auth.listar_usuarios().items():
            print(f"    {nome:<20} {perfil}")


def acao_ler_relatorios():
    if not os.path.isdir(DIR_RELATORIOS) or not os.listdir(DIR_RELATORIOS):
        print("  Nenhum relatório disponível ainda.")
        return
    arquivos = sorted(os.listdir(DIR_RELATORIOS))
    for i, nome in enumerate(arquivos, 1):
        print(f"    {i}) {nome}")
    escolha = input("  Número do relatório (Enter para voltar): ").strip()
    if escolha.isdigit() and 1 <= int(escolha) <= len(arquivos):
        caminho = os.path.join(DIR_RELATORIOS, arquivos[int(escolha) - 1])
        with open(caminho, "r", encoding="utf-8") as f:
            print("\n" + f.read())


def acao_backup(sessao):
    script = os.path.join(BASE_DIR, "backup", "backup.sh")
    registrar_evento(f"BACKUP_SOLICITADO: por usuario '{sessao['usuario']}'")
    subprocess.run(["bash", script])


MENU = [
    ("Gerenciar usuários (cadastrar/remover/listar)", "usuarios", "gerenciar_usuarios"),
    ("Criar baseline de integridade (monitor init)", "minit", "monitor_init"),
    ("Verificar integridade dos documentos", "mver", "monitor_verificar"),
    ("Gerar relatório de auditoria do SO (who/last/ss/ip)", "audit", "auditoria_gerar"),
    ("Validar integridade da blockchain", "bval", "blockchain_validar"),
    ("Listar blocos da blockchain", "blist", "blockchain_listar"),
    ("Executar backup seguro (tar.gz + AES-256)", "backup", "backup_executar"),
    ("Ler relatórios de auditoria", "rel", "relatorios_ler"),
]


def loop_principal(sessao):
    while True:
        print("\n" + "=" * 60)
        print(f" SecureChain Audit | usuário: {sessao['usuario']} "
              f"| perfil: {sessao['perfil']}")
        print("=" * 60)

        visiveis = [
            (i, rotulo, codigo, perm)
            for i, (rotulo, codigo, perm) in enumerate(MENU, 1)
            if sessao["perfil"] in PERMISSOES[perm]
        ]
        for i, rotulo, _, _ in visiveis:
            print(f"  {i}) {rotulo}")
        print("  0) Sair (logout)")

        escolha = input("Opção: ").strip()
        if escolha == "0":
            registrar_evento(f"LOGOUT: usuario '{sessao['usuario']}'")
            print("Sessão encerrada. Logout registrado na blockchain.")
            break

        selecionado = next(
            ((codigo, perm) for i, _, codigo, perm in visiveis if str(i) == escolha),
            None,
        )
        if not selecionado:
            print("Opção inválida.")
            continue

        codigo, perm = selecionado
        if not autorizado(sessao, perm):
            continue

        if codigo == "usuarios":
            acao_gerenciar_usuarios(sessao)
        elif codigo == "minit":
            monitor.inicializar()
        elif codigo == "mver":
            monitor.verificar()
        elif codigo == "audit":
            from auditoria.auditor import gerar_relatorio
            gerar_relatorio()
        elif codigo == "bval":
            validar_cadeia()
        elif codigo == "blist":
            Blockchain().listar()
        elif codigo == "backup":
            acao_backup(sessao)
        elif codigo == "rel":
            acao_ler_relatorios()


def main():
    print("=" * 60)
    print(" SecureChain Audit - Plataforma de Auditoria com Blockchain")
    print("=" * 60)

    if not auth.listar_usuarios():
        print("\nNenhum usuário cadastrado. Vamos criar o ADMINISTRADOR inicial.")
        nome = input("Usuário admin: ").strip()
        senha = getpass.getpass("Senha (mín. 8 caracteres, letras e números): ")
        try:
            auth.cadastrar(nome, senha, "admin", executor="bootstrap")
            print(f"[OK] Administrador '{nome}' criado.\n")
        except ValueError as e:
            print(f"[ERRO] {e}")
            sys.exit(1)

    for tentativa in range(3):
        nome = input("Usuário: ").strip()
        senha = getpass.getpass("Senha: ")
        sessao = auth.login(nome, senha)
        if sessao:
            loop_principal(sessao)
            return
        print(f"[ERRO] Credenciais inválidas ({tentativa + 1}/3). "
              "Tentativa registrada na blockchain.")

    print("[BLOQUEADO] Número máximo de tentativas excedido.")
    registrar_evento("ALERTA: 3 tentativas de login consecutivas falharam")
    sys.exit(1)


if __name__ == "__main__":
    main()