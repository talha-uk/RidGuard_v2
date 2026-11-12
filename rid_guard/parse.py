"""JSON satırını veya MT303 `$...$end` cümlesini Sighting yapar.

Heartbeat ve Feature uçak değildir. Tanınmayan satır drone olmaz.
"""

import json

from rid_guard.models import Sighting, normalize_source


class ParseError(ValueError):
    pass


_SKIP = frozenset({"heartbeat", "Feature"})


def read_line(line: str) -> Sighting | None:
    """Uçak kaydı döner. Heartbeat ve Feature için None."""
    text = line.strip()
    if not text:
        raise ParseError("empty")
    if text.startswith("$"):
        return _parse_mt(text)
    return parse_line(text)


def parse_line(line: str) -> Sighting:
    text = line.strip()
    if not text:
        raise ParseError("empty")
    if text.startswith("$"):
        sighting = _parse_mt(text)
        if sighting is None:
            raise ParseError("not_aircraft")
        return sighting
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseError("not_json") from exc
    if not isinstance(payload, dict):
        raise ParseError("not_object")
    serial = _text(payload, "serial", "serial_number", "sn", "uas_id")
    if not serial:
        raise ParseError("serial_missing")
    try:
        ts = float(payload.get("ts"))
    except (TypeError, ValueError) as exc:
        raise ParseError("ts_missing") from exc
    raw_source = _text(payload, "source", "mode", "detect_mode")
    return Sighting(
        ts=ts,
        source=normalize_source(raw_source),
        serial=serial,
        model=_text(payload, "model", "drone_model"),
        lat=_number(payload, "lat", "latitude"),
        lon=_number(payload, "lon", "longitude", "long"),
        alt_m=_number(payload, "alt_m", "altitude", "alt"),
        speed_mps=_number(payload, "speed_mps", "airspeed", "speed"),
        pilot_lat=_number(payload, "pilot_lat", "pilot_latitude"),
        pilot_lon=_number(payload, "pilot_lon", "pilot_longitude"),
        operator_id=_text(payload, "operator_id", "operator"),
        self_id=_text(payload, "self_id", "selfid"),
        ssid=_text(payload, "ssid", "wifi_name"),
    )


def _parse_mt(text: str) -> Sighting | None:
    body = text.strip()
    if body.endswith("$end"):
        body = body[: -len("$end")].rstrip(",").strip()
    if not body.startswith("$"):
        raise ParseError("not_mt")
    parts = [part for part in body.split(",") if part]
    kind = parts[0][1:]
    if kind in _SKIP:
        return None
    if kind != "RID":
        raise ParseError("unknown_mt")
    fields: dict[str, str] = {}
    for part in parts[1:]:
        if ":" not in part:
            raise ParseError("mt_field")
        key, value = part.split(":", 1)
        fields[key] = value.strip()
    serial = fields.get("uav_id", "")
    if not serial:
        raise ParseError("serial_missing")
    return Sighting(
        ts=_mt_number(fields, "timestamp2", "timestamp1"),
        source=normalize_source(fields.get("protocol", "")),
        serial=serial,
        lat=_optional_number(fields, "latitude"),
        lon=_optional_number(fields, "longitude"),
        alt_m=_optional_number(fields, "altitude_geo", "altitude_qne"),
        speed_mps=_optional_number(fields, "speed"),
        # MT303 operatör enlemini latitude_polit diye yazar.
        pilot_lat=_optional_number(fields, "latitude_polit"),
        pilot_lon=_optional_number(fields, "longitude_polit"),
    )


def _mt_number(fields: dict[str, str], *keys: str) -> float:
    for key in keys:
        if key not in fields or fields[key] == "":
            continue
        try:
            return float(fields[key])
        except ValueError as exc:
            raise ParseError(f"{key}_bad") from exc
    raise ParseError("ts_missing")


def _optional_number(fields: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        if key not in fields or fields[key] == "":
            continue
        try:
            return float(fields[key])
        except ValueError as exc:
            raise ParseError(f"{key}_bad") from exc
    return None


def _text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _number(payload: dict, *keys: str) -> float | None:
    for key in keys:
        if key not in payload:
            continue
        value = payload.get(key)
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ParseError(f"{key}_bad") from exc
    return None
