import random
import string

_ALPHABET = string.ascii_letters + string.digits  # 62 chars → 62^7 ≈ 3.5 trillion combos
_CODE_LENGTH = 7


def generate_short_code() -> str:
    return "".join(random.choices(_ALPHABET, k=_CODE_LENGTH))
