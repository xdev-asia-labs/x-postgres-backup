"""Internationalization (i18n) module for x-postgres-backup.

Cookie-based language detection supporting: en, vi, zh, ja.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
SUPPORTED_LANGUAGES = ["en", "vi", "zh", "ja"]
DEFAULT_LANGUAGE = "en"
LANGUAGE_COOKIE = "xpb_lang"

LANGUAGE_NAMES = {
    "en": "English",
    "vi": "Tiếng Việt",
    "zh": "中文",
    "ja": "日本語",
}


@lru_cache(maxsize=8)
def _load_translations(lang: str) -> dict:
    """Load translation file for a given language."""
    path = LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        logger.warning("Translation file not found: %s, falling back to English", path)
        path = LOCALES_DIR / "en.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_lang_from_request(request) -> str:
    """Extract language from request cookie, falling back to default."""
    lang = request.cookies.get(LANGUAGE_COOKIE, DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return lang


def translate(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Translate a dot-notation key (e.g. 'nav.dashboard') to the given language.

    Falls back to English, then returns the key itself if not found.
    """
    translations = _load_translations(lang)

    # Support dot-notation: "nav.dashboard" -> translations["nav"]["dashboard"]
    parts = key.split(".")
    value = translations
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            # Fallback to English
            if lang != DEFAULT_LANGUAGE:
                return translate(key, DEFAULT_LANGUAGE)
            return key
    return value if isinstance(value, str) else key


def make_translate_func(lang: str):
    """Create a translation function bound to a specific language."""
    def _(key: str) -> str:
        return translate(key, lang)
    return _
