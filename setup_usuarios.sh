#!/usr/bin/env bash

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERRO] Execute como root: sudo bash setup_usuarios.sh <dir_projeto>"
    exit 1
fi

PROJETO="${1:-$(pwd)}"
[ -d "$PROJETO" ] || { echo "[ERRO] Diretório '$PROJETO' não existe."; exit 1; }
echo "[*] Projeto: $PROJETO"

for grupo in sc_admin sc_analista sc_visitante; do
    getent group "$grupo" >/dev/null || groupadd "$grupo"
    echo "[OK] Grupo '$grupo' disponível."
done

criar_usuario() {
    local nome="$1" grupo="$2"
    if ! id "$nome" >/dev/null 2>&1; then
        useradd -m -s /bin/bash -G "$grupo" "$nome"
        echo "[OK] Usuário '$nome' criado (grupo: $grupo). Defina a senha:"
        passwd "$nome"
    else
        usermod -aG "$grupo" "$nome"
        echo "[OK] Usuário '$nome' já existia; adicionado ao grupo '$grupo'."
    fi
}
criar_usuario administrador sc_admin
criar_usuario analista      sc_analista
criar_usuario visitante     sc_visitante

chown -R administrador:sc_analista "$PROJETO"

find "$PROJETO" -type d -exec chmod 750 {} \;

find "$PROJETO" -type f -exec chmod 640 {} \;

chmod 750 "$PROJETO/main.py" "$PROJETO/auth.py" "$PROJETO/monitor.py" \
          "$PROJETO/auditoria/auditor.py" \
          "$PROJETO/blockchain/blockchain.py" 2>/dev/null || true

chmod 700 "$PROJETO/backup/backup.sh"
chown administrador:sc_admin "$PROJETO/backup"
chmod 700 "$PROJETO/backup"
chmod 700 "$PROJETO/usuarios"
[ -f "$PROJETO/usuarios/usuarios.json" ] && chmod 600 "$PROJETO/usuarios/usuarios.json"

chgrp -R sc_visitante "$PROJETO/auditoria/relatorios"
chmod 750 "$PROJETO/auditoria" "$PROJETO/auditoria/relatorios"
find "$PROJETO/auditoria/relatorios" -type f -exec chmod 640 {} \; 2>/dev/null || true
chmod o+x "$PROJETO" "$PROJETO/auditoria" 2>/dev/null || true

chmod 750 "$PROJETO/logs" "$PROJETO/blockchain"
[ -f "$PROJETO/blockchain/chain.json" ] && chmod 640 "$PROJETO/blockchain/chain.json"

echo
echo "================= RESUMO (para o relatório) ================="
echo " administrador : dono de tudo (rwx) — gerencia o sistema"
echo " analista      : grupo sc_analista — lê e executa módulos (sem escrita)"
echo " visitante     : grupo sc_visitante — só lê auditoria/relatorios/"
echo "=============================================================="
ls -la "$PROJETO"
