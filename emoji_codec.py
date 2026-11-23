"""
emoji_codec.py - Пользовательский кодек для поддержки эмодзи в качестве имен
переменных, функций и классов в Python.

Регистрирует кодировку с именем 'emoji_python' (или 'emoji-python').
"""

import codecs
import io
import re
import tokenize

# Регулярные выражения для распознавания эмодзи (включая составные):
# 1. Флаги (Regional Indicator Symbols, пары U+1F1E6 - U+1F1FF)
_REGIONAL_INDICATOR = r'[\U0001F1E6-\U0001F1FF]'
_FLAG_SEQUENCE = rf'{_REGIONAL_INDICATOR}{{2}}'

# 2. Флаги подразделений через теговые последовательности (например, флаг Англии 🏴󠁧󠁢󠁥󠁮󠁧󠁿):
# \U0001F3F4 + теги \U000E0020-\U000E007E + \U000E007F
_TAG_SEQUENCE = r'\U0001F3F4[\U000E0020-\U000E007E]+\U000E007F'

# 3. Модификаторы: тон кожи Фитцпатрика (U+1F3FB-U+1F3FF) и селекторы начертания (\uFE0E, \uFE0F)
_MODIFIERS = r'[\U0001F3FB-\U0001F3FF\uFE0E\uFE0F]'

# 4. Базовые глифы эмодзи (SMP и BMP диапазоны символов/пиктограмм)
_BASE_CHAR = r'[\U0001F000-\U0001FAFF\u2000-\u32FF\u00A9\u00AE\u2122\u2139]'
_SINGLE_EMOJI = rf'(?:{_BASE_CHAR}{_MODIFIERS}*)'

# 5. Составные эмодзи через ZWJ (Zero Width Joiner, \u200D)
_ZWJ = r'\u200D'
_EMOJI_CORE = rf'(?:{_FLAG_SEQUENCE}|{_TAG_SEQUENCE}|{_SINGLE_EMOJI})'
_EMOJI_SEQUENCE = rf'{_EMOJI_CORE}(?:{_ZWJ}{_EMOJI_CORE})*'

_EMOJI_RE = re.compile(_EMOJI_SEQUENCE)


def emoji_to_identifier(match: re.Match) -> str:
    """
    Преобразует найденный эмодзи (простой или составной) в валидную часть
    идентификатора Python на основе шестнадцатеричных Unicode-кодпоинтов.
    Пример: 🚀 -> _emoji_1f680_
            👨‍💻 -> _emoji_1f468_200d_1f4bb_
            👍🏽 -> _emoji_1f44d_1f3fd_
            🇷🇺 -> _emoji_1f1f7_1f1fa_
    """
    codepoints = "_".join(f"{ord(c):x}" for c in match.group(0))
    return f"_emoji_{codepoints}_"


def transform_token_string(token_str: str) -> str:
    """
    Трансформирует строку токена: заменяет эмодзи на валидные идентификаторы.
    Если токен уже является валидным идентификатором (например, обычное имя),
    он возвращается без изменений.
    """
    if token_str.isidentifier():
        return token_str

    # Заменяем составные и одиночные эмодзи
    transformed = _EMOJI_RE.sub(emoji_to_identifier, token_str)

    # Дополнительная страховка: если остались спецсимволы, делающие идентификатор невалидным
    if not transformed.isidentifier():
        parts = []
        for ch in transformed:
            if ch.isalnum() or ch == '_':
                parts.append(ch)
            else:
                parts.append(f"_u{ord(ch):x}_")
        transformed = "".join(parts)
        if transformed and transformed[0].isdigit():
            transformed = "_" + transformed

    return transformed


def transform_source(source_code: str) -> str:
    """
    Лексически анализирует исходный код на Python с помощью tokenize,
    преобразуя эмодзи в именах переменных, функций и классов,
    но ОСТАВЛЯЯ НЕИЗМЕННЫМИ строки (включая f-строки) и комментарии.
    """
    # Токены, которые могут представлять имена идентификаторов
    target_types = {tokenize.NAME}
    if hasattr(tokenize, "ERRORTOKEN"):
        target_types.add(tokenize.ERRORTOKEN)

    reader = io.StringIO(source_code).readline
    try:
        tokens = list(tokenize.generate_tokens(reader))
    except tokenize.TokenError:
        # Если возникла синтаксическая ошибка токенизации, возвращаем исходный код
        return source_code

    new_tokens = []
    for tok in tokens:
        tok_type, tok_str, start, end, line = tok
        if tok_type in target_types:
            new_str = transform_token_string(tok_str)
            new_tokens.append((tokenize.NAME, new_str, start, end, line))
        else:
            new_tokens.append(tok)

    return tokenize.untokenize(new_tokens)


# --- Реализация кодека codecs ---

def emoji_decode(input_bytes, errors="strict"):
    """Функция декодирования байтов исходного кода в валидный Python-текст."""
    raw_text = bytes(input_bytes).decode("utf-8", errors)
    transformed_text = transform_source(raw_text)
    return transformed_text, len(input_bytes)


class EmojiIncrementalDecoder(codecs.BufferedIncrementalDecoder):
    """Инкрементальный декодер для потоковой обработки."""
    def _buffer_decode(self, input, errors, final):
        if final:
            raw_text = bytes(input).decode("utf-8", errors)
            return transform_source(raw_text), len(input)
        # Пока поток не завершен (не final), ждем полный блок кода
        return "", 0


class EmojiStreamReader(codecs.StreamReader):
    """Потоковый ридер для чтения файлов."""
    def decode(self, input, errors="strict"):
        raw_text = bytes(input).decode("utf-8", errors)
        return transform_source(raw_text), len(input)


_utf8 = codecs.lookup("utf-8")

EMOJI_CODEC_INFO = codecs.CodecInfo(
    name="emoji_python",
    encode=_utf8.encode,
    decode=emoji_decode,
    incrementalencoder=_utf8.incrementalencoder,
    incrementaldecoder=EmojiIncrementalDecoder,
    streamreader=EmojiStreamReader,
    streamwriter=_utf8.streamwriter,
)


def search_function(encoding: str):
    """Поисковая функция для реестра codecs."""
    normalized = encoding.lower().replace("-", "_").replace(".", "_")
    if normalized == "emoji_python":
        return EMOJI_CODEC_INFO
    return None


def register():
    """Регистрирует кодек emoji_python в стандартном модуле codecs."""
    codecs.register(search_function)


# Автоматическая регистрация при импорте данного модуля
register()
