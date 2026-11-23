"""
emoji_python - Пользовательская кодировка и загрузчик для эмодзи в Python.
"""

import importlib.machinery
import os
import sys
from .codec import register, EMOJI_CODEC_INFO, transform_source

__all__ = ["register", "EMOJI_CODEC_INFO", "transform_source"]


class EmojiLoader(importlib.machinery.SourceFileLoader):
    """Кастомный загрузчик, трансформирующий эмодзи в импортируемых модулях на лету."""
    def source_to_code(self, data, path, *, _optimize=-1):
        try:
            source_text = data.decode("utf-8")
            transformed = transform_source(source_text)
            return super().source_to_code(transformed.encode("utf-8"), path, _optimize=_optimize)
        except Exception:
            return super().source_to_code(data, path, _optimize=_optimize)


def install_import_hook():
    """Устанавливает хук в sys.path_hooks для прозрачного импорта файлов с эмодзи."""
    loader_details = (EmojiLoader, importlib.machinery.SOURCE_SUFFIXES)
    sys.path_hooks.insert(0, importlib.machinery.FileFinder.path_hook(loader_details))
    sys.path_importer_cache.clear()


def auto_intercept():
    """Перехватывает запуск скриптов, начинающихся с #emoji или # emoji."""
    if not sys.argv or not sys.argv[0]:
        return
    target = sys.argv[0]
    if not os.path.isfile(target) or not target.endswith(('.py', '.pyw')):
        return
    try:
        with open(target, 'rb') as f:
            first_line = f.readline()
        stripped = first_line.strip()
        if stripped.startswith((b'#emoji', b'# emoji', b'#EMOJI', b'# EMOJI')):
            with open(target, 'rb') as f:
                content = f.read().decode('utf-8')
            transformed = transform_source(content)
            code_obj = compile(transformed, os.path.abspath(target), 'exec')
            script_dir = os.path.dirname(os.path.abspath(target))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            globs = {
                '__name__': '__main__',
                '__file__': os.path.abspath(target),
                '__doc__': None,
                '__package__': None,
            }
            exec(code_obj, globs)
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(0)
    except SystemExit as e:
        code_val = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(code_val)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)


# 1. Автоматическая регистрация кодека (# coding: emoji_python и # coding: emoji)
register()

# 2. Автоматическая установка хука импорта
install_import_hook()

# 3. Автоматический перехват при прямом запуске скрипта с #emoji
auto_intercept()
