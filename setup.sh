#!/bin/bash
set -e

echo "==== Instalando navegadores y dependencias del sistema ===="
if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y chromium chromium-browser chromium-chromedriver || apt-get install -y chromium-browser chromium-chromedriver || true
fi

echo "==== Instalando dependencias Python ===="
pip install -r requirements.txt

echo "==== Instalando navegador Playwright (Chromium) ===="
python -m playwright install chromium || true

echo "==== Rutas detectadas ===="
command -v chromium || true
command -v chromium-browser || true
command -v chromedriver || true

echo "==== Setup finalizado ===="
