#!/usr/bin/env bash

set -euo pipefail

DIR_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(dirname "$DIR_SCRIPT")"
DIR_DOCS="$RAIZ/documentos"
DIR_LOGS="$RAIZ/logs"
ARQ_LOG="$DIR_LOGS/backup.log"
DATA="$(date +%Y%m%d_%H%M%S)"
ARQ_TAR="$DIR_SCRIPT/backup_documentos_${DATA}.tar.gz"

mkdir -p "$DIR_LOGS"

log() {
    local msg="[$(date --iso-8601=seconds)] $1"
    echo "$msg"
    echo "$msg" >> "$ARQ_LOG"
}

falha() {
    log "STATUS=FALHA | $1"
    exit 1
}

[ -d "$DIR_DOCS" ] || falha "Diretório documentos/ não encontrado."

log "Iniciando backup de documentos/ ..."

tar -czf "$ARQ_TAR" -C "$RAIZ" documentos \
    || falha "Erro na compactação tar.gz."

TAMANHO_TAR="$(du -h "$ARQ_TAR" | cut -f1)"
log "Compactação concluída: $(basename "$ARQ_TAR") (${TAMANHO_TAR})"

python3 "$RAIZ/blockchain/blockchain.py" \
    add "BACKUP_EXECUTADO: $(basename "$ARQ_TAR") | tamanho=${TAMANHO_TAR}" \
    || falha "Erro ao registrar o evento na blockchain."

log "STATUS=SUCESSO | arquivo=$(basename "$ARQ_TAR") | tamanho=${TAMANHO_TAR}"