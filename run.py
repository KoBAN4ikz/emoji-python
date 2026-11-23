"""
run.py - Скрипт-запускатель для Python-файлов с поддержкой кодировки emoji_python.

Автоматически регистрирует кодек emoji_codec и запускает указанный файл через runpy,
что избавляет от необходимости модифицировать системный sitecustomize.py.
"""

import os
import runpy
import sys

# Регистрируем пользовательский кодек emoji_python
import emoji_codec


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Использование:")
        print("  python run.py <целевой_скрипт.py> [аргументы...]")
        print("\nПример:")
        print("  python run.py example.py")
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 1)

    target_script = sys.argv[1]

    if not os.path.isfile(target_script):
        print(f"Ошибка: Файл '{target_script}' не найден.", file=sys.stderr)
        sys.exit(1)

    # Убеждаемся, что кодек зарегистрирован
    emoji_codec.register()

    # Сдвигаем sys.argv, чтобы целевой скрипт видел корректные аргументы
    # sys.argv[0] становится путем к целевому скрипту
    sys.argv = sys.argv[1:]

    # Добавляем каталог целевого скрипта в sys.path,
    # чтобы скрипт мог импортировать соседние модули
    script_dir = os.path.dirname(os.path.abspath(target_script))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Запускаем целевой скрипт в пространстве __main__
    runpy.run_path(target_script, run_name="__main__")


if __name__ == "__main__":
    main()
