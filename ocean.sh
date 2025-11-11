#!/bin/bash

set -e # Прерывать выполнение при любой ошибке

# --- Аргументы ---
BINARY_PATH=$1
LOG_FILE_NAME=$2
WALLET=$3
WORKER_NAME=$4

# --- Конфигурация ---
API_PORT="60001" # Порт для API, который будет слушать Python-скрипт

echo "MoneroOcean simplified setup script."
echo "Arguments: BINARY_PATH=$BINARY_PATH, LOG_FILE_NAME=$LOG_FILE_NAME, WALLET=$WALLET, WORKER_NAME=$WORKER_NAME"
echo

# --- Проверки ---
if [ -z "$BINARY_PATH" ] || [ -z "$LOG_FILE_NAME" ] || [ -z "$WALLET" ] || [ -z "$WORKER_NAME" ]; then
  echo "ERROR: Usage: $0 <binary_path> <log_file_name> <wallet_address> <worker_name>"
  echo "Example: $0 /home/user/.local/bin/xmr_inst xmrig.log 4Ab...123.123.123.123 123.123.123.123"
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

INSTALL_DIR=$(dirname "$BINARY_PATH")
CONFIG_FILE="$INSTALL_DIR/config.json"
LOG_FILE_PATH="$INSTALL_DIR/$LOG_FILE_NAME"

# --- Подготовка ---

echo "[*] Stopping previous xmrig processes (if any)..."
# Универсальный способ, который должен работать даже в урезанных системах без killall
ps aux | grep '[x]mrig' | awk '{print $2}' | xargs kill -9 >/dev/null 2>&1 || true

# Удаляем старый бинарник, если он есть (новая версия будет загружена)
rm -f "$BINARY_PATH"

# --- Загрузка и распаковка ---

echo "[*] Downloading MoneroOcean xmrig to /tmp/xmrig.tar.gz..."
# Обрати внимание: используем фиксированную ссылку, как в оригинальном скрипте
curl -L --progress-bar "https://raw.githubusercontent.com/MoneroOcean/xmrig_setup/master/xmrig.tar.gz" -o /tmp/xmrig.tar.gz

echo "[*] Creating install directory $INSTALL_DIR and unpacking archive..."
mkdir -p "$INSTALL_DIR"
tar xf /tmp/xmrig.tar.gz -C "$INSTALL_DIR"
rm /tmp/xmrig.tar.gz

# --- Перемещение бинарника ---
XMRIG_EXE_ORIG="$INSTALL_DIR/xmrig" # Предполагаемое имя в архиве
if [ -f "$XMRIG_EXE_ORIG" ]; then
    mv "$XMRIG_EXE_ORIG" "$BINARY_PATH"
    echo "[*] XMRig binary moved to $BINARY_PATH"
else
    echo "ERROR: Original XMRig binary not found at $XMRIG_EXE_ORIG after unpacking."
    exit 1
fi

echo "[*] Verifying xmrig binary at $BINARY_PATH..."
if ! "$BINARY_PATH" --help >/dev/null; then
  echo "ERROR: The installed xmrig binary is not functional or not found at $BINARY_PATH."
  exit 1
fi
echo "[*] XMRig binary is OK."

# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."

sed -i \
    -e 's/"donate-level": *[^,]*,/"donate-level": 0,/' \
    -e 's/"url": *"[^"]*",/"url": "gulf.moneroocean.stream:10128",/' \
    -e 's/"user": *"[^"]*",/"user": "'"$WALLET"'",/' \
    -e 's/"pass": *"[^"]*",/"pass": "'"$WORKER_NAME"'",/' \
    -e 's#"log-file": *null,#"log-file": "'"$LOG_FILE_PATH"'",#' \
    -e 's/"background": *true,/"background": false,/' \
    -e '/"http": {/,/}/ s/"enabled": *false,/"enabled": true,/' \
    -e '/"http": {/,/}/ s/"port": *0,/"port": '$API_PORT',/' \
    -e '/"http": {/,/}/ s/"restricted": *true,/"restricted": false,/' \
    e '/"http": {/,/}/ s/}/,"access-token": "my_secret_token"/' \
    -e '/"cuda": {/,/}/ s/"enabled": *true,/"enabled": false,/' \
    -e '/"opencl": {/,/}/ s/"enabled": *true,/"enabled": false,/' \
    "$CONFIG_FILE"


echo
echo "[*] Setup complete. Miner is ready to be started."
echo "    - Executable: $BINARY_PATH"
echo "    - Config: $CONFIG_FILE"
echo "    - Log: $LOG_FILE_PATH"
echo "    - API: http://127.0.0.1:$API_PORT/"
echo

# --- Запуск ---
# Запускаем XMRig в фоне, передав ему путь к конфигурационному файлу
# и убедившись, что он запускается в нужной директории (для логов)
cd "$INSTALL_DIR"
nohup "$BINARY_PATH" -c "$CONFIG_FILE" > /dev/null 2>&1 &

echo "[*] XMRig miner started in background."
echo "    You can check the logs with: tail -f $LOG_FILE_PATH"
echo "    You can check the API status with: curl http://127.0.0.1:$API_PORT/"
