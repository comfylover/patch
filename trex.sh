#!/bin/bash

set -e # Прерывать выполнение при любой ошибке

# --- Конфигурация ---
API_PORT="60000" # Порт для API, который будет слушать Python-скрипт
TREX_VERSION="0.26.8"
TREX_URL="https://github.com/trexminer/T-Rex/releases/download/$TREX_VERSION/t-rex-$TREX_VERSION-linux.tar.gz"
# Обрати внимание: в оригинальном скрипте использовался IP как имя воркера
WALLET_KAWPOW=$1
WORKER_NAME=$2

echo "T-Rex simplified setup script."
echo

# --- Проверки ---
if [ -z "$WALLET_KAWPOW" ] || [ -z "$WORKER_NAME" ]; then
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

# --- Аргументы ---
WALLET=$WALLET_KAWPOW
PASS="x" # Обычно для KawPow используется "x" как пароль

INSTALL_DIR="$HOME/trex"
CONFIG_FILE="$INSTALL_DIR/config.json"
TREX_EXE="$INSTALL_DIR/t-rex"

# --- Подготовка ---

echo "[*] Stopping previous t-rex processes (if any)..."
# Универсальный способ, который должен работать даже в урезанных системах без killall
ps aux | grep '[t]rex' | awk '{print $2}' | xargs kill -9 >/dev/null 2>&1 || true

echo "[*] Cleaning up previous installation directory: $INSTALL_DIR"
rm -rf "$INSTALL_DIR"

# --- Загрузка и распаковка ---

echo "[*] Downloading T-Rex from $TREX_URL to /tmp/trex.tar.gz..."
curl -L --progress-bar "$TREX_URL" -o /tmp/trex.tar.gz

echo "[*] Creating install directory $INSTALL_DIR and unpacking archive..."
mkdir -p "$INSTALL_DIR"
tar xf /tmp/trex.tar.gz -C "$INSTALL_DIR"
rm /tmp/trex.tar.gz

echo "[*] Verifying t-rex executable..."
if ! "$TREX_EXE" --help >/dev/null 2>&1; then
  echo "ERROR: The downloaded t-rex executable is not functional or not found at $TREX_EXE."
  exit 1
fi
echo "[*] t-rex executable is OK."

# --- Конфигурирование ---

echo "[*] Creating config file $CONFIG_FILE..."

# Используем cat для создания файла с многострочным содержимым
# и заменяем нужные поля с помощью sed
cat << 'EOF' > "$CONFIG_FILE"
{
  "pools": [
    {
      "user": "RBX1G6nYDMHVtyaZiQWySMZw1Bb2DEDpT8",
      "url": "stratum+ssl://rvn.kryptex.network:8031",
      "pass": "x",
      "worker": "default_worker_name"
    }
  ],
  "coin" : "",
  "worker" : "default_worker_name",
  "pci-indexing" : false,
  "ab-indexing" : false,
  "gpu-init-mode" : 0,
  "keep-gpu-busy" : false,
  "api-bind-http": "127.0.0.1:4067",
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
  "log-path": "t-rex.log",
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

# Теперь используем sed для замены конкретных значений
sed -i \
    -e 's/"RBX1G6nYDMHVtyaZiQWySMZw1Bb2DEDpT8"/"'$WALLET'"/' \
    -e 's/"default_worker_name"/"'$WORKER_NAME'"/' \
    -e 's/"127.0.0.1:4067"/"127.0.0.1:'$API_PORT'"/' \
    -e 's/"log-path": "t-rex.log"/"log-path": "'"$INSTALL_DIR"'\/t-rex.log"/' \
    "$CONFIG_FILE"

echo "[*] Config file $CONFIG_FILE created and configured."

# --- Запуск ---
echo
echo "[*] Setup complete. Starting t-rex miner..."
echo "    - Executable: $TREX_EXE"
echo "    - Config: $CONFIG_FILE"
echo "    - Log: $INSTALL_DIR/t-rex.log"
echo "    - API: http://127.0.0.1:$API_PORT/"
echo