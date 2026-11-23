"""
emoji_python - Пользовательская кодировка и загрузчик для эмодзи в Python.
"""

import importlib.machinery
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


# 1. Автоматическая регистрация кодека (# coding: emoji_python)
register()

# 2. Автоматическая установка хука импорта (для импорта файлов даже БЕЗ # coding)
install_import_hook()
