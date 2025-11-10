# corp_simplify_utils.py
# Utility for normalizing corporate/organization names

import unicodedata

# This translation table replaces a wide range of Unicode punctuation and symbols
# with ASCII equivalents or spaces.
STR_TABLE = str.maketrans({
    "’": "'", "‘": "'", "´": "'", "“": '"', "”": '"',  # smart quotes to normal quotes
    "–": "-", "—": "-", "‐": "-",                      # dashes
    "•": " ", "·": " ", "•": " ", "…": "...",          # bullets and ellipsis
    "®": "", "©": "", "™": "",                         # trademark symbols removed
    "&": " and ",                                      # normalize ampersands
    "/": " ", "\\": " ",                               # slashes to spaces
    "_": " ",                                          # underscores to spaces
    "–": "-", "—": "-",                                # normalize dash variants
    "\xa0": " ", "\u200b": " ", "\u2011": "-",         # non-breaking spaces etc.
})

def normalize_unicode(text):
    """
    Fully normalize unicode characters (accents, ligatures, etc.)
    and apply STR_TABLE replacements.
    """
    if not isinstance(text, str):
        return ""
    # Normalize accented characters (é → e)
    text = unicodedata.normalize("NFKD", text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    # Apply translation map
    return text.translate(STR_TABLE)
