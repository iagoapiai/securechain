#!/usr/bin/env bash

set -euo pipefail

DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$DIR_SCRIPT")"
DIR_DOCS="$RAIZ/documentos"
DIR_LOGS="$RAIZ/logs"
ARQ_LOG="$DIR_LOGS/backup.log"
DATA="$(date +%Y%m%d_%H%M%S)"
ARQ_TAR="$DIR_SCRIPT/backup_documentos_${DATA}.tar.gz"
ARQ_ENC="${ARQ_TAR}.enc"

mkdir -p "$DIR_LOGS"

log() {
    local msg="[$(date --iso-8601=seconds)] $1"
    echo "$msg"
    echo "$msg" >> "$ARQ_LOG"
}

falha() {
    log "STATUS=FALHA | $1"
    python3 "$RAIZ/blockchain/blockchain.py" add "BACKUP_FALHA: $1" >/dev/null 2>&1 || true
    exit 1
}

[ -d "$DIR_DOCS" ] || falha "Diretório documentos/ não encontrado."
command -v openssl >/dev/null 2>&1 || falha "openssl não instalado (sudo apt install openssl)."

if [ -z "${BACKUP_SENHA:-}" ]; then
    read -r -s -p "Senha para criptografar o backup: " BACKUP_SENHA
    echo
    [ -n "$BACKUP_SENHA" ] || falha "Senha vazia não é permitida."
fi
export BACKUP_SENHA

log "Iniciando backup seguro de documentos/ ..."

tar -czf "$ARQ_TAR" -C "$RAIZ" documentos \
    || falha "Erro na compactação tar.gz."

TAMANHO_TAR="$(du -h "$ARQ_TAR" | cut -f1)"

log "Compactação concluída: $(basename "$ARQ_TAR") (${TAMANHO_TAR})"

openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
    -in "$ARQ_TAR" -out "$ARQ_ENC" -pass env:BACKUP_SENHA \
    || falha "Erro na criptografia openssl."

rm -f "$ARQ_TAR"
TAMANHO_ENC="$(du -h "$ARQ_ENC" | cut -f1)"
chmod 600 "$ARQ_ENC"
log "Criptografia AES-256-CBC concluída: $(basename "$ARQ_ENC") (${TAMANHO_ENC})"

python3 "$RAIZ/blockchain/blockchain.py" \
    add "BACKUP_EXECUTADO: $(basename "$ARQ_ENC") | tamanho=${TAMANHO_ENC} | AES-256-CBC" \
    || falha "Erro ao registrar o evento na blockchain."

log "STATUS=SUCESSO | arquivo=$(basename "$ARQ_ENC") | tamanho=${TAMANHO_ENC}"
echo
echo "Para restaurar o backup:"
echo "  openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in $(basename "$ARQ_ENC") -out restaurado.tar.gz"
echo "  tar -xzf restaurado.tar.gz"
