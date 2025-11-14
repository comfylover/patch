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

if ! type curl >/dev/null 2>&1 || ! type tar >/dev/null 2>&1; then
  echo "ERROR: This script requires 'curl' and 'tar' to work."
  exit 1
fi

INSTALL_DIR=$(dirname "$BINARY_PATH")
CONFIG_FILE="$INSTALL_DIR/config_x.json"
LOG_FILE_PATH="$INSTALL_DIR/$LOG_FILE_NAME"

# --- Подготовка ---
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
# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."


API_TOKEN='xmrig_secret'
# Используем cat для создания файла с многострочным содержимым
# и вставляем нужные значения напрямую
cat << EOF > "$CONFIG_FILE"
{
    "autosave": true,
    "cpu-affinity": true,
    "cpu-priority": 2,
    "donate-level": 0,
    "log-file": "$LOG_FILE_PATH",
    "print-time": 60,
    "retries": 3,
    "retry-pause": 5,
    "safe": false,
    "syslog": false,
    "threads": null,
    "pools": [
        {
            "url": "gulf.moneroocean.stream:10128",
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
    "cpu": {
        "enabled": true,
        "huge-pages": true,
        "memory-pool": false,
        "yield": true,
        "priority": null,
        "asm": true,
        "argon2-impl": null,
        "astrobwt-max-size": 550,
        "astrobwt-avx2": false,
        "cn/0": false,
        "cn-lite/0": false,
        "rx/0": false,
        "rx/arq": false,
        "rx/keva": false,
        "rx/sfx": false,
        "cn-half": false,
        "cn-trtl": false,
        "cn/ccx": false,
        "randomx": {
            "init": -1,
            "mode": "auto",
            "1gb-pages": false,
            "rdmsr": true,
            "wrmsr": true,
            "numa": true,
            "affinity": -1
        },
        "astrobwt": false,
        "kawpow": false,
        "ghostrider": false
    },
    "opencl": {
        "enabled": false,
        "cache": true,
        "loader": null,
        "platform": "AMD",
        "adl": true,
        "device": null,
        "threads": null,
        "raw-intensity": null,
        "intensity": null,
        "worksize": null,
        "strided-index": 0,
        "mem-chunk": 0,
        "comp-mode": null,
        "dual-mode": null,
        "grid-factor": 1,
        "grid-affinity": false
    },
    "cuda": {
        "enabled": false,
        "loader": null,
        "nvml": true,
        "cupti": false,
        "device": null,
        "sm": null,
        "threads": null,
        "blocks": null,
        "bfactor": 0,
        "bsleep": 0,
        "sync-mode": 3,
        "affinity": -1,
        "max-threads": 100,
        "strided-index": 2,
        "mem-chunk": 4,
        "comp-mode": null,
        "dual-mode": null,
        "grid-factor": 1,
        "grid-affinity": false
    },
    "cc-client": {
        "enabled": false,
        "socket": null,
        "password": null,
        "max-failures": 5
    },
    "network": {
        "http": {
            "enabled": true,
            "max-threads": 16,
            "keep-alive": true,
            "content-type": "application/json",
            "access-token": null,
            "host": "127.0.0.1",
            "port": 3333,
            "restricted-port": 3334,
            "ipv6": false,
            "restricted-ipv6": false,
            "port-hua": 0
        }
    }
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
nohup "$BINARY_PATH" -c "$CONFIG_FILE" > /dev/null 2>&1 &

echo "[*] XMRig miner started in background."
echo "    You can check the logs with: tail -f $LOG_FILE_PATH"
echo "    You can check the API status with: curl http://127.0.0.1:$API_PORT/"
