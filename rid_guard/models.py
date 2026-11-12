"""Karar motoruna giren kayıt ve kaynaktan gelen etiket."""

from dataclasses import dataclass

LINK_SOURCES = frozenset({"ocusync", "fingerprint"})


def normalize_source(raw: str) -> str:
    """Boş ve tanınmayan etiket Remote ID sayılır. `protocol` tek başına bağ değildir."""
    text = " ".join((raw or "").lower().replace("_", " ").replace("-", " ").split())
    if "fingerprint" in text:
        return "fingerprint"
    tokens = text.split()
    if "ocusync" in text:
        return "ocusync"
    if any(token in {"o2", "o3", "o4"} for token in tokens):
        return "ocusync"
    paired = zip(tokens, tokens[1:])
    if any(left == "drone" and right == "id" for left, right in paired):
        return "ocusync"
    return "remote_id"


@dataclass(frozen=True)
class Sighting:
    ts: float
    source: str
    serial: str
    model: str = ""
    lat: float | None = None
    lon: float | None = None
    alt_m: float | None = None
    speed_mps: float | None = None
    pilot_lat: float | None = None
    pilot_lon: float | None = None
    operator_id: str = ""
    self_id: str = ""
    ssid: str = ""

    @property
    def from_link(self) -> bool:
        return normalize_source(self.source) in LINK_SOURCES
