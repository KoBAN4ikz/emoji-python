"""
codec.py - Реализация кодека emoji_python.
"""

import codecs
import io
import re
import tokenize

_REGIONAL_INDICATOR = r'[\U0001F1E6-\U0001F1FF]'
_FLAG_SEQUENCE = rf'{_REGIONAL_INDICATOR}{{2}}'
_TAG_SEQUENCE = r'\U0001F3F4[\U000E0020-\U000E007E]+\U000E007F'
_MODIFIERS = r'[\U0001F3FB-\U0001F3FF\uFE0E\uFE0F]'
_BASE_CHAR = r'[\U0001F000-\U0001FAFF\u2000-\u32FF\u00A9\u00AE\u2122\u2139]'
_SINGLE_EMOJI = rf'(?:{_BASE_CHAR}{_MODIFIERS}*)'
_ZWJ = r'\u200D'
_EMOJI_CORE = rf'(?:{_FLAG_SEQUENCE}|{_TAG_SEQUENCE}|{_SINGLE_EMOJI})'
_EMOJI_SEQUENCE = rf'{_EMOJI_CORE}(?:{_ZWJ}{_EMOJI_CORE})*'

_EMOJI_RE = re.compile(_EMOJI_SEQUENCE)


def emoji_to_identifier(match: re.Match) -> str:
    codepoints = "_".join(f"{ord(c):x}" for c in match.group(0))
    return f"_emoji_{codepoints}_"


def transform_token_string(token_str: str) -> str:
    if token_str.isidentifier():
        return token_str

    transformed = _EMOJI_RE.sub(emoji_to_identifier, token_str)

    if not transformed.isidentifier():
        parts = []
        for ch in transformed:
            parts.append(ch if ch.isalnum() or ch == '_' else f"_u{ord(ch):x}_")
        transformed = "".join(parts)
        if transformed and transformed[0].isdigit():
            transformed = "_" + transformed

    return transformed


def transform_source(source_code: str) -> str:
    target_types = {tokenize.NAME}
    if hasattr(tokenize, "ERRORTOKEN"):
        target_types.add(tokenize.ERRORTOKEN)

    reader = io.StringIO(source_code).readline
    try:
        tokens = list(tokenize.generate_tokens(reader))
    except tokenize.TokenError:
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


def emoji_decode(input_bytes, errors="strict"):
    raw_text = bytes(input_bytes).decode("utf-8", errors)
    transformed_text = transform_source(raw_text)
    return transformed_text, len(input_bytes)


class EmojiIncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, input, errors, final):
        if final:
            raw_text = bytes(input).decode("utf-8", errors)
            return transform_source(raw_text), len(input)
        return "", 0


class EmojiStreamReader(codecs.StreamReader):
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
    normalized = encoding.lower().replace("-", "_").replace(".", "_")
    if normalized == "emoji_python":
        return EMOJI_CODEC_INFO
    return None


def register():
    """Регистрирует кодек emoji_python в реестре codecs."""
    codecs.register(search_function)
