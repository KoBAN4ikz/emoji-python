"""
emoji_python - Пользовательская кодировка для эмодзи-идентификаторов в Python.
"""

from .codec import register, EMOJI_CODEC_INFO, transform_source

__all__ = ["register", "EMOJI_CODEC_INFO", "transform_source"]

# Автоматическая регистрация при `import emoji_python`
register()
