"""
run.py - Универсальный запускатель emoji_python.
Позволяет запускать скрипты с эмодзи даже БЕЗ строчки '# coding: emoji_python',
а также запускать интерактивную консоль (REPL).
"""

import code
import os
import runpy
import sys
from .codec import register, transform_source


class EmojiInteractiveConsole(code.InteractiveConsole):
    """Интерактивная консоль с автоматической поддержкой эмодзи."""
    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            transformed = transform_source(source)
        except Exception:
            transformed = source
        return super().runsource(transformed, filename, symbol)


def start_repl():
    """Запуск интерактивного Python REPL с поддержкой эмодзи."""
    register()
    banner = "=== Emoji Python Interactive Console 🚀 ===\nПишите код с эмодзи прямо здесь! Для выхода введите exit()"
    console = EmojiInteractiveConsole()
    console.interact(banner=banner)


def run_file(target_script: str):
    """Выполняет файл с поддержкой эмодзи (со строкой # coding или без нее)."""
    register()

    # Сдвигаем sys.argv
    sys.argv = sys.argv[1:]
    script_dir = os.path.dirname(os.path.abspath(target_script))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    with open(target_script, "rb") as f:
        raw_bytes = f.read()

    # Проверяем, есть ли заголовок # coding: emoji_python
    has_codec_header = b"coding: emoji_python" in raw_bytes or b"coding:emoji_python" in raw_bytes

    if has_codec_header:
        # Стандартный путь через runpy
        runpy.run_path(target_script, run_name="__main__")
    else:
        # Если забыли написать # coding: emoji_python - трансформируем на лету!
        source_text = raw_bytes.decode("utf-8")
        transformed = transform_source(source_text)
        compiled = compile(transformed, target_script, "exec")
        globs = {
            "__name__": "__main__",
            "__file__": os.path.abspath(target_script),
            "__doc__": None,
            "__package__": None,
        }
        exec(compiled, globs)


def main():
    if len(sys.argv) == 1:
        # Если запущено без аргументов - открываем интерактивную консоль!
        start_repl()
        return

    if sys.argv[1] in ("-h", "--help"):
        print("Использование:")
        print("  emoji <файл.py> [аргументы...]    - Запустить Python-файл с эмодзи")
        print("  emoji                             - Запустить интерактивную консоль")
        sys.exit(0)

    target_script = sys.argv[1]
    if not os.path.isfile(target_script):
        print(f"Ошибка: Файл '{target_script}' не найден.", file=sys.stderr)
        sys.exit(1)

    run_file(target_script)


if __name__ == "__main__":
    main()
