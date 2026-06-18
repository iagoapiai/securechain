# SecureChain Audit

Plataforma de Auditoria Baseada em Blockchain — desenvolvida para a disciplina **Segurança de Sistemas com Blockchain, Criptografia e Auditoria de Eventos**, em ambiente **Linux Debian 13**, com **Python 3** e **Bash Script**.

O sistema resolve os problemas identificados na empresa fictícia *SecureData Solutions*: controle de usuários com separação de funções, monitoramento de integridade por hash, blockchain imutável para registro de eventos, backup criptografado e auditoria contínua do sistema operacional.

---

## Estrutura do projeto

```
securechain/
├── blockchain/
│   ├── blockchain.py        # Blocos, encadeamento, validação (RF04, RF07)
│   └── chain.json           # Persistência da blockchain
├── auditoria/
│   ├── auditor.py           # Coleta who, last, ss -tulpn, ip a (RF06)
│   └── relatorios/          # Relatórios datados gerados automaticamente
├── backup/
│   └── backup.sh            # tar.gz + AES-256 + log + bloco (RF05)
├── logs/                    # Logs locais (integridade, backup)
├── documentos/              # Arquivos monitorados por hash (RF03)
├── usuarios/                # usuarios.json (senhas em hash SHA-256+salt)
├── auth.py                  # Cadastro, login, sessão e perfis (RF02)
├── monitor.py               # Monitor de integridade SHA-256 (RF03)
├── main.py                  # Aplicação principal com menu e RBAC
├── setup_usuarios.sh        # Usuários/grupos/permissões do SO (RF01)
├── demo_adulteracao.py      # Demonstração de detecção de corrupção
└── README.md
```

## Requisitos

| Item | Detalhe |
|---|---|
| Sistema | Debian 13 (VM) — funciona em qualquer Linux com Bash |
| Python | Python 3 (somente biblioteca padrão: hashlib, json, secrets, etc.) |
| Pacotes do SO | `openssl`, `tar`, `iproute2` (ss/ip), `nmap` (hacking ético) |

Instalação dos pacotes (caso falte algum):

```bash
sudo apt update
sudo apt install -y openssl tar iproute2 nmap git
```

> Nenhuma biblioteca Python externa é necessária — o hash de senhas usa
> `hashlib.pbkdf2_hmac` (SHA-256 + salt), conforme permitido pelo enunciado.

## Como executar

### 1) Configurar usuários e permissões do SO (RF01) — uma única vez

```bash
sudo bash setup_usuarios.sh "$(pwd)"
```

Cria `administrador`, `analista` e `visitante`, os grupos `sc_admin`, `sc_analista`, `sc_visitante`, e aplica `chown`/`chmod` segundo o princípio do menor privilégio.

### 2) Criar a baseline de integridade (RF03)

Coloque os arquivos a proteger em `documentos/` e rode:

```bash
python3 monitor.py init        # gera os hashes SHA-256 de referência
python3 monitor.py verificar   # compara com a baseline
python3 monitor.py watch 30    # verificação contínua a cada 30s (opcional)
```

### 3) Aplicação principal (login, sessão, menu por perfil)

```bash
python3 main.py
```

- No primeiro uso, o sistema solicita a criação do **administrador inicial**.
- Após o login, o menu exibe apenas as ações permitidas ao perfil ativo:
  - **admin**: tudo (usuários, monitor, auditoria, validação, backup);
  - **analista**: verificar integridade, gerar auditoria, validar/listar blockchain, ler relatórios;
  - **visitante**: somente ler relatórios.
- Logins (sucesso **e** falha), logouts, criação/remoção de usuários e tentativas de ação sem permissão geram blocos na blockchain.

### 4) Auditoria do sistema operacional (RF06)

```bash
python3 auditoria/auditor.py
```

Gera `auditoria/relatorios/auditoria_AAAAMMDD_HHMMSS.txt` com a saída de `who`, `last`, `ss -tulpn` e `ip a`, e registra o evento na blockchain.

### 5) Backup seguro (RF05)

```bash
bash backup/backup.sh
# ou, para automação (cron):
BACKUP_SENHA="SenhaForte123" bash backup/backup.sh
```

Fluxo: compacta `documentos/` → criptografa com **AES-256-CBC (openssl, PBKDF2 + salt)** → registra bloco na blockchain → grava `logs/backup.log` com data, tamanho e status. O `.tar.gz` em claro é removido; permanece apenas o `.enc`.

Restauração:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in backup/backup_documentos_XXX.tar.gz.enc -out restaurado.tar.gz
tar -xzf restaurado.tar.gz
```

### 6) Blockchain — uso direto (RF04 / RF07)

```bash
python3 blockchain/blockchain.py listar    # lista todos os blocos
python3 blockchain/blockchain.py validar   # valida toda a cadeia
python3 blockchain/blockchain.py add "Evento manual de teste"
```

### 7) Demonstração de detecção de adulteração

```bash
cp blockchain/chain.json blockchain/chain.json.bak   # backup da cadeia
python3 demo_adulteracao.py 2                        # adultera o bloco 2
# A validação detecta e identifica o bloco corrompido
cp blockchain/chain.json.bak blockchain/chain.json   # restaura
```

## Segurança aplicada (resumo)

- **Senhas**: SHA-256 + salt individual via PBKDF2 (200.000 iterações), arquivo `usuarios.json` com permissão `600`; comparação em tempo constante.
- **Integridade**: SHA-256 de arquivos (`documentos/`) e de blocos.
- **Backup**: criptografia simétrica AES-256-CBC com PBKDF2 + salt.
- **Zero Trust**: identidade verificada a cada sessão; toda ação é checada contra a matriz de permissões; acessos negados também são registrados de forma imutável.
- **Menor privilégio**: perfis na aplicação + usuários/grupos/chmod no SO.
- **Validação de entrada**: regex para nomes de usuário, política de senha mínima, timeout em comandos do SO.

## Equipe

| Integrante | Módulo(s) responsável(is) | Arquivos |
|---|---|---|
| **Iago Armelin Piai** | Autenticação + criação do repo | auth.py, .gitignore, .gitattributes |
| **Pedro Afonso Zanão** | Auditoria SO + integração (main.py) | setup_usuarios.sh, main.py, auditoria/auditor.py |
| **Pedro Henrique Municelli** | Monitor de integridade + Blockchain | monitor.py, documentos/, blockchain/blockchain.py, demo_adulteracao.py |
| **David Teixeira Ferraz** | Backup seguro | backup/backup.sh |
| **Yuri Alves Bordin** | Ajustes + fechamento com documentação | README.md |