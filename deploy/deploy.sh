#!/usr/bin/env bash
# Ship the app to the demo box. SSH must already be open for this machine's /32.
set -euo pipefail
HOST=${SNIFF_HOST:-ec2-user@3.219.133.78}
KEY=${SNIFF_SSH_KEY:-$HOME/.ssh/quant-mcp-key.pem}
cd "$(dirname "$0")/.."
PATHS=(); for p in app requirements.txt deploy build queries README.md docs; do [ -e "$p" ] && PATHS+=("$p"); done
rsync -az --delete -e "ssh -i $KEY" --exclude __pycache__ --exclude out "${PATHS[@]}" "$HOST":/opt/lineage/app/src/
ssh -i "$KEY" "$HOST" 'set -e
  cd /opt/lineage/app
  [ -x .venv/bin/python ] || python3.12 -m venv .venv
  .venv/bin/pip install -q -r src/requirements.txt
  sudo install -m 644 src/deploy/sniff-app.service /etc/systemd/system/sniff-app.service
  sudo systemctl daemon-reload
  if systemctl is-active -q lineage-placeholder; then sudo systemctl disable --now lineage-placeholder; fi
  sudo systemctl enable -q sniff-app; sudo systemctl restart sniff-app
  sleep 2; curl -fsS 127.0.0.1:8080/healthz'
