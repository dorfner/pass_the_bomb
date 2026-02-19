import random
import unicodedata


def load_dictionary_from_file(filename):
    """Load words from a json file, return a set."""
    import json
    import os

    filepath = os.path.join(os.path.dirname(__file__), "data", filename)

    with open(filepath, "r", encoding="utf-8") as f:
        d = json.load(f)

    return d


def remove_accents(text):
    """Remove diacritics (é → e, ê → e, …)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

