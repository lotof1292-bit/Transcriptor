#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
umask 077

if [[ ! -x .venv/bin/python ]]; then
  python3.12 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt
if [[ ! -s server-token.txt ]]; then
  .venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))' > server-token.txt
fi
chmod 600 server-token.txt
export STUDIO_TOKEN
STUDIO_TOKEN="$(<server-token.txt)"
if command -v ollama >/dev/null; then
  ollama pull "${STUDIO_TEXT_MODEL:-qwen3:4b}" || printf '%s\n' 'Ollama no está listo. Revisa su servicio antes de usar traducción y reescritura.' >&2
else
  printf '%s\n' 'Instala Ollama para habilitar traducción y reescritura.' >&2
fi
printf '%s\n' "Token privado: $(pwd)/server-token.txt" 'En el VPS usa un proxy HTTPS para llegar al puerto local 8790.'
exec .venv/bin/python -m uvicorn server:app --host "${STUDIO_BIND:-127.0.0.1}" --port "${STUDIO_PORT:-8790}" --workers 1
