#!/bin/bash

set -e # Прерывать выполнение при любой ошибке

# --- Конфигурация ---
API_PORT="60001" # Порт для API, который будет слушать Python-скрипт

# --- Аргументы ---
WALLET=$1
PASS=$2

echo "MoneroOcean simplified setup script."
echo

# --- Проверки ---
if [ -z "$WALLET" ] || [ -z "$PASS" ]; then
  echo "ERROR: Usage: $0 <wallet_address> <worker_name>"
  exit 1
fi

if [ -z "$HOME" ] || [ ! -d "$HOME" ]; then
  echo "ERROR: HOME directory is not set or does not exist."
  exit 1
fi

if ! type curl >/dev/null 2>&1 || ! type tar >/dev/null 2>&1; then
  echo "ERROR: This script requires 'curl' and 'tar' to work."
  exit 1
fi

INSTALL_DIR="$HOME/moneroocean"
CONFIG_FILE="$INSTALL_DIR/config.json"

# --- Подготовка ---

echo "[*] Stopping previous xmrig processes (if any)..."
# Универсальный способ, который должен работать даже в урезанных системах без killall
ps aux | grep '[x]mrig' | awk '{print $2}' | xargs kill -9 >/dev/null 2>&1 || true

echo "[*] Cleaning up previous installation directory: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"

# --- Загрузка и распаковка ---

echo "[*] Downloading MoneroOcean xmrig to /tmp/xmrig.tar.gz..."
curl -L --progress-bar "https://raw.githubusercontent.com/MoneroOcean/xmrig_setup/master/xmrig.tar.gz" -o /tmp/xmrig.tar.gz

echo "[*] Unpacking archive to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
tar xf /tmp/xmrig.tar.gz -C "$INSTALL_DIR"
rm /tmp/xmrig.tar.gz

echo "[*] Verifying xmrig executable..."
XMRIG_EXE="$INSTALL_DIR/xmrig"
if ! "$XMRIG_EXE" --help >/dev/null; then
  echo "ERROR: The downloaded xmrig executable is not functional."
  exit 1
fi
echo "[*] xmrig executable is OK."

# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."

sed -i \
    -e 's/"donate-level": *[^,]*,/"donate-level": 0,/' \
    -e 's/"url": *"[^"]*",/"url": "gulf.moneroocean.stream:10128",/' \
    -e 's/"user": *"[^"]*",/"user": "'"$WALLET"'",/' \
    -e 's/"pass": *"[^"]*",/"pass": "'"$PASS"'",/' \
    -e 's#"log-file": *null,#"log-file": "'"$INSTALL_DIR"/xmrig.log'",#' \
    -e 's/"background": *true,/"background": false,/' \
    -e '/"http": {/,/}/ s/"enabled": *false,/"enabled": true,/' \
    -e '/"http": {/,/}/ s/"port": *0,/"port": '$API_PORT',/' \
    -e '/"http": {/,/}/ s/"restricted": *true,/"restricted": false,/' \
    -e '/"cuda": {/,/}/ s/"enabled": *true,/"enabled": false,/' \
    -e '/"opencl": {/,/}/ s/"enabled": *true,/"enabled": false,/' \
    "$CONFIG_FILE"


echo
echo "[*] Setup complete. Miner is ready to be started."
echo "    - To run, execute: $INSTALL_DIR/miner.sh"
echo "    - Configuration is in: $CONFIG_FILE"
echo