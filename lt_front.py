import subprocess
import time
import shutil
import sys
import os

PORT = "4200"
SUBDOMAIN = "mushroomsgribcarf"

def find_lt_cmd():
    # Сначала пробуем найти глобальный lt (Windows — lt.cmd, Unix — lt)
    for cmd in ("lt", "lt.cmd"):
        path = shutil.which(cmd)
        if path:
            return [path]
    # Если не нашли, попробуем npx
    npx = shutil.which("npx")
    if npx:
        return [npx, "lt"]
    # Ничего не нашли
    return None

def start_localtunnel():
    base_cmd = find_lt_cmd()
    if not base_cmd:
        print("❌ Не удалось найти ни lt, ни npx в PATH. Установите localtunnel глобально: npm install -g localtunnel")
        sys.exit(1)

    cmd = base_cmd + ["--port", PORT, "--subdomain", SUBDOMAIN]
    print(f"Запуск localtunnel: {' '.join(cmd)}")
    # На Windows лучше не использовать shell=True, если у вас полный путь к lt.cmd
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc

def monitor_localtunnel():
    while True:
        proc = start_localtunnel()
        # читаем вывод в реальном времени, чтобы знать, что происходит
        try:
            for line in proc.stdout:
                print(line.rstrip())
        except Exception:
            pass
        ret = proc.wait()
        print(f"localtunnel завершился с кодом {ret}, перезапуск через 5 секунд...")
        time.sleep(5)

if __name__ == "__main__":
    # Убедимся, что мы в виртуальном окружении, если нужно
    print(f"Python: {sys.executable}")
    monitor_localtunnel()