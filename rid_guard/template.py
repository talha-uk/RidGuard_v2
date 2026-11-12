"""ESP8266 ridSerial() şablonunu tanır. Paket üretmez, yayın açmaz.

Ürün kodu: 1581F + 3 karakter + RID + iki hane + yedi X.
Kod yoksa model adındaki boşluk ve '+' atılır, 20 karaktere X ile doldurulur.
RID hanesi değişse de aynı kalıp yeter.
"""

import re

TABLE: tuple[tuple[str, str], ...] = (
    ("DJI Mini 3", "1581F5YH"),
    ("DJI Mini 3 Pro", "1581F4XF"),
    ("DJI Mini 4 Pro", "1581F6Z9"),
    ("DJI Mini SE", ""),
    ("DJI Air 2S", "1581F3YT"),
    ("DJI Air 3", "1581F6N8"),
    ("DJI Mavic Air 2", ""),
    ("DJI Mavic 3", "1581F45T"),
    ("DJI Mavic 3 Classic", "1581F67P"),
    ("DJI Avata", "1581F4QW"),
    ("DJI Avata 2", "1581F6W8"),
    ("DJI FPV", ""),
    ("Autel EVO Nano+", ""),
    ("Autel EVO II Pro", ""),
    ("Parrot Anafi", ""),
)

LEGACY = (
    "DJI Mini 2",
    "Skydio 2+",
    "Holy Stone HS720E",
)

_PRODUCT = re.compile(r"^1581F[0-9A-Z]{3}RID[0-9]{2}X{7}$")


def _compact(name: str) -> str:
    return "".join(ch for ch in name.upper() if ch not in " +")


def _padded(name: str) -> str:
    return _compact(name)[:20].ljust(20, "X")


def _at(index: int) -> str:
    name, prefix = TABLE[index]
    if prefix:
        return f"{prefix}RID{index + 1:02d}XXXXXXX"
    return _padded(name)


def known_templates() -> tuple[str, ...]:
    current = tuple(_at(index) for index in range(len(TABLE)))
    legacy = tuple(_padded(name) for name in LEGACY)
    return current + legacy


_PADDED = frozenset(_padded(name) for name, prefix in TABLE if not prefix)
_PADDED = _PADDED | frozenset(_padded(name) for name in LEGACY)

_CATALOG = frozenset(
    " ".join(name.lower().split()) for name in [item[0] for item in TABLE] + list(LEGACY)
)


def matches_template(serial: str) -> bool:
    text = (serial or "").strip().upper()
    return bool(_PRODUCT.fullmatch(text)) or text in _PADDED


def template_model(serial: str) -> str:
    """Şablondaki ürün adını döndürür. Eşleşme yoksa boş metin."""
    text = (serial or "").strip().upper()
    for name, prefix in TABLE:
        if prefix and text.startswith(prefix):
            return name
        if not prefix and text == _padded(name):
            return name
    for name in LEGACY:
        if text == _padded(name):
            return name
    return ""


def is_catalog_label(value: str) -> bool:
    text = " ".join((value or "").lower().split())
    return bool(text) and text in _CATALOG
