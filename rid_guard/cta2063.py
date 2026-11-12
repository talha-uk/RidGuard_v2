"""ANSI/CTA-2063-A seri yapısı. Yalnız kontrol eder."""

ALPHABET = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"

_LENGTH = {str(n): n for n in range(1, 10)}
_LENGTH.update({chr(ord("A") + i): 10 + i for i in range(6)})


def check_serial(serial: str) -> tuple[bool, str]:
    text = (serial or "").strip().upper()
    if not text:
        return False, "serial_empty"
    if any(ch not in ALPHABET for ch in text):
        return False, "serial_alphabet"
    if len(text) < 6 or len(text) > 20:
        return False, "serial_length"
    expected = _LENGTH.get(text[4])
    if expected is None or len(text[5:]) != expected:
        return False, "serial_length_code"
    return True, "serial_ok"
