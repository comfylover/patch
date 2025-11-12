#!/bin/bash

set -e # Прерывать выполнение при любой ошибке

# --- Аргументы ---
BINARY_PATH=$1
LOG_FILE_NAME=$2
WALLET=$3
WORKER_NAME=$4

# --- Конфигурация ---
API_PORT="60000" # Порт для API, который будет слушать Python-скрипт
TREX_VERSION="0.26.8"
TREX_URL="https://github.com/trexminer/T-Rex/releases/download/$TREX_VERSION/t-rex-$TREX_VERSION-linux.tar.gz"

echo "T-Rex simplified setup script."
echo "Arguments: BINARY_PATH=$BINARY_PATH, LOG_FILE_NAME=$LOG_FILE_NAME, WALLET=$WALLET, WORKER_NAME=$WORKER_NAME"
echo

# --- Проверки ---
if [ -z "$BINARY_PATH" ] || [ -z "$LOG_FILE_NAME" ] || [ -z "$WALLET" ] || [ -z "$WORKER_NAME" ]; then
  echo "ERROR: Usage: $0 <binary_path> <log_file_name> <wallet_address> <worker_name>"
  echo "Example: $0 /home/user/.local/bin/t_rex_inst t_rex.log krxXJ6QJPW.123.123.123.123 123.123.123.123"
  exit 1
fi

if ! type curl >/dev/null 2>&1 || ! type tar >/dev/null 2>&1; then
  echo "ERROR: This script requires 'curl' and 'tar' to work."
  exit 1
fi

# --- Переменные ---
INSTALL_DIR=$(dirname "$BINARY_PATH")
CONFIG_FILE="$INSTALL_DIR/config.json"
LOG_FILE_PATH="$INSTALL_DIR/$LOG_FILE_NAME"

# Удаляем старый бинарник, если он есть
rm -f "$BINARY_PATH"

# --- Загрузка и распаковка ---

echo "[*] Downloading T-Rex from $TREX_URL to /tmp/trex.tar.gz..."
curl -L --progress-bar "$TREX_URL" -o /tmp/trex.tar.gz

echo "[*] Creating install directory $INSTALL_DIR and unpacking archive..."
mkdir -p "$INSTALL_DIR"
tar xf /tmp/trex.tar.gz -C "$INSTALL_DIR"
rm /tmp/trex.tar.gz

# --- Перемещение бинарника ---
TREX_EXE_ORIG="$INSTALL_DIR/t-rex" # Предполагаемое имя в архиве
if [ -f "$TREX_EXE_ORIG" ]; then
    mv "$TREX_EXE_ORIG" "$BINARY_PATH"
    echo "[*] T-Rex binary moved to $BINARY_PATH"
else
    echo "ERROR: Original T-Rex binary not found at $TREX_EXE_ORIG after unpacking."
    exit 1
fi

echo "[*] Verifying t-rex binary at $BINARY_PATH..."
if ! "$BINARY_PATH" --help >/dev/null 2>&1; then
  echo "ERROR: The installed t-rex binary is not functional or not found at $BINARY_PATH."
  exit 1
fi
echo "[*] T-Rex binary is OK."

# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."

# Используем cat для создания файла с многострочным содержимым
cat << 'EOF' > "$CONFIG_FILE"
{
  "pools": [
    {
      "user": "$WALLET",
      "url": "stratum+ssl://rvn.kryptex.network:8031",
      "pass": "x",
      "worker": "$WORKER_NAME"
    }
  ],
  "coin" : "",
  "worker" : "$WORKER_NAME",
  "pci-indexing" : false,
  "ab-indexing" : false,
  "gpu-init-mode" : 0,
  "keep-gpu-busy" : false,
  "api-bind-http": "127.0.0.1:$API_PORT",
  "api-https": false,
  "api-key": "",
  "api-webserver-cert" : "",
  "api-webserver-pkey" : "",
  "kernel" : 0,
  "retries": 3,
  "retry-pause": 10,
  "timeout": 300,
  "algo": "kawpow",
  "devices": 0,
  "intensity": 20,
  "dag-build-mode": 0,
  "dataset-mode": 0,
  "extra-dag-epoch": -1,
  "low-load": 0,
  "lhr-tune": -1,
  "lhr-autotune-mode": "down",
  "lhr-autotune-step-size": 0.1,
  "lhr-autotune-interval": "5:120",
  "lhr-low-power": 0,
  "hashrate-avr": 60,
  "sharerate-avr": 600,
  "gpu-report-interval": 30,
  "log-path": "$LOG_FILE_NAME",
  "cpu-priority": 2,
  "autoupdate": false,
  "exit-on-cuda-error": true,
  "exit-on-connection-lost": false,
  "exit-on-high-power": 0,
  "reconnect-on-fail-shares": 10,
  "protocol-dump": false,
  "no-color": false,
  "hide-date": false,
  "send-stales": false,
  "validate-shares": false,
  "no-nvml": false,
  "no-strict-ssl": false,
  "no-sni": false,
  "no-hashrate-report": false,
  "no-watchdog": false,
  "quiet": false,
  "mt": 4,
  "fan": "t:65",
  "pl": 100,
  "cclock": 50,
  "mclock": 100,
  "cv": 0,
  "lock-cv": 0,
  "pstate": "p0",
  "lock-cclock": 1000,
  "fork-at": "",
  "time-limit": 0,
  "temperature-color": "67,77",
  "temperature-color-mem": "80,100",
  "temperature-limit": 0,
  "temperature-start": 0,
  "back-to-main-pool-sec": 600,
  "script-start": "",
  "script-exit": "",
  "script-epoch-change": "",
  "script-crash": "",
  "script-low-hash": "",
  "monitoring-page" : {
     "graph_interval_sec" : 3600,
     "update_timeout_sec" : 10
  }
}
EOF

echo "[*] Config file $CONFIG_FILE created and configured."

# --- Запуск ---
echo
echo "[*] Setup complete. Starting t-rex miner..."
echo "    - Executable: $BINARY_PATH"
echo "    - Config: $CONFIG_FILE"
echo "    - Log: $LOG_FILE_PATH"
echo "    - API: http://127.0.0.1:$API_PORT/"
echo

# Запускаем T-Rex в фоне, передав ему путь к конфигурационному файлу
# и убедившись, что он запускается в нужной директории (для логов)
cd "$INSTALL_DIR"
nohup "$BINARY_PATH" -c "$CONFIG_FILE" > /dev/null 2>&1 &

echo "[*] T-Rex miner started in background."
echo "    You can check the logs with: tail -f $LOG_FILE_PATH"
echo "    You can check the API status with: curl http://127.0.0.1:$API_PORT/"