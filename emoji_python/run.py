"""
run.py - CLI утилита для запуска emoji_python скриптов.
"""

import os
import runpy
import sys
from .codec import register


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Использование: emoji-run <скрипт.py> [аргументы...]")
        print("           или: python -m emoji_python <скрипт.py> [аргументы...]")
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 1)

    target_script = sys.argv[1]
    if not os.path.isfile(target_script):
        print(f"Ошибка: Файл '{target_script}' не найден.", file=sys.stderr)
        sys.exit(1)

    register()

    sys.argv = sys.argv[1:]
    script_dir = os.path.dirname(os.path.abspath(target_script))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    runpy.run_path(target_script, run_name="__main__")


if __name__ == "__main__":
    main()
