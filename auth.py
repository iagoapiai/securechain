import hashlib
import json
import os
import re
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQ_USUARIOS = os.path.join(BASE_DIR, "usuarios", "usuarios.json")
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

def usuario_valido(nome):
    return bool(re.fullmatch(r"[a-zA-Z0-9._]{3,32}", nome))


def senha_valida(senha):
    return (
        len(senha) >= 8
        and re.search(r"[a-zA-Z]", senha) is not None
        and re.search(r"[0-9]", senha) is not None
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
        raise ValueError("Senha fraca: mínimo 8 caracteres com letras e números.")

    salt, hash_senha = gerar_hash_senha(senha)
    usuarios[nome] = {"salt": salt, "hash": hash_senha, "perfil": perfil}
    _salvar_usuarios(usuarios)
    print(f"[OK] Usuário '{nome}' cadastrado com perfil '{perfil}'.")
    print(f"     Salt gerado:  {salt}")
    print(f"     Hash gerado:  {hash_senha[:32]}...  (truncado)")
    print("     Senha NUNCA armazenada em texto puro.")
    return True


def listar_usuarios():
    usuarios = _carregar_usuarios()
    return {nome: d["perfil"] for nome, d in usuarios.items()}


if __name__ == "__main__":
    import getpass

    print("=" * 55)
    print(" SecureChain Audit :: Autenticação (versão parcial)")
    print("=" * 55)
    print("1) Cadastrar usuário   2) Listar usuários")
    opcao = input("Opção: ").strip()

    if opcao == "1":
        nome   = input("Usuário: ").strip()
        perfil = input(f"Perfil {PERFIS_VALIDOS}: ").strip()
        senha  = getpass.getpass("Senha: ")
        try:
            cadastrar(nome, senha, perfil)
        except ValueError as e:
            print(f"[ERRO] {e}")

    elif opcao == "2":
        usuarios = listar_usuarios()
        if not usuarios:
            print("Nenhum usuário cadastrado ainda.")
        else:
            for nome, perfil in usuarios.items():
                print(f"  {nome:<20} {perfil}")