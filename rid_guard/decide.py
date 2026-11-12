"""Remote ID kaydını operasyon ekranına alıp almamaya karar verir.

Ekrana OcuSync, RF parmak izi, sahte ve şüpheli kimlik düşer.
Sahte ve şüpheli kayıt uçak iğnesi almaz.
"""

from dataclasses import dataclass, field
import math
import re

from rid_guard.cta2063 import check_serial
from rid_guard.models import LINK_SOURCES, Sighting, normalize_source
from rid_guard.template import is_catalog_label, matches_template, template_model

MAX_SPEED_MPS = 45.0
MAX_VERTICAL_MPS = 15.0
MOTION_WINDOW_S = 5.0
MOTION_HISTORY_S = 20.0
SPEED_LIE_MPS = 3.0
MOTION_FRACTION = 0.25
HEADING_MIN_MOVE_M = 20.0
HEADING_TOLERANCE_DEG = 60.0
CLUSTER_MIN = 4
CLUSTER_WINDOW_S = 15.0
CLUSTER_RADIUS_M = 80.0
LINK_MEMORY_S = 120.0
MIN_DT_S = 0.05
_PADDING = re.compile(r"(.)\1{6,}")


@dataclass
class Decision:
    serial: str
    verdict: str
    display: bool
    reasons: list[str]
    lat: float | None = None
    lon: float | None = None
    pilot_lat: float | None = None
    pilot_lon: float | None = None
    model: str = ""
    source: str = ""
    mark: str = ""

    def as_dict(self) -> dict:
        return {
            "serial": self.serial,
            "verdict": self.verdict,
            "display": self.display,
            "mark": self.mark,
            "reasons": list(self.reasons),
            "lat": self.lat,
            "lon": self.lon,
            "pilot_lat": self.pilot_lat,
            "pilot_lon": self.pilot_lon,
            "model": self.model,
            "source": self.source,
        }


@dataclass
class _Mark:
    ts: float
    lat: float | None
    lon: float | None


@dataclass
class _Fix:
    ts: float
    lat: float
    lon: float
    alt: float | None


@dataclass
class Guard:
    max_speed_mps: float = MAX_SPEED_MPS
    _track: dict = field(default_factory=dict)
    _history: dict = field(default_factory=dict)
    _pilots: list = field(default_factory=list)
    _link_seen: dict = field(default_factory=dict)
    _cluster_until: dict = field(default_factory=dict)

    def observe(self, sighting: Sighting) -> Decision:
        serial = sighting.serial.strip().upper()
        source = normalize_source(sighting.source)
        self._expire(sighting.ts)
        if matches_template(serial):
            reasons = _identity(serial, sighting)
            if "esp8266_template" not in reasons:
                reasons.insert(0, "esp8266_template")
            return Decision(
                serial=serial,
                verdict="spoof",
                display=True,
                mark="sahte",
                reasons=reasons,
                pilot_lat=sighting.pilot_lat,
                pilot_lon=sighting.pilot_lon,
                model=sighting.model or template_model(serial),
                source=source,
            )
        if source in LINK_SOURCES:
            if _has_fix(sighting):
                self._link_seen[serial] = sighting.ts
            self._track[serial] = _mark(sighting)
            return Decision(
                serial=serial,
                verdict="confirmed",
                display=True,
                reasons=["link"],
                lat=sighting.lat,
                lon=sighting.lon,
                model=sighting.model,
                source=source,
            )
        reasons = _identity(serial, sighting)
        reasons.extend(self._motion(serial, sighting))
        reasons.extend(self._consistency(serial, sighting))
        if self._clustered(serial, sighting):
            reasons.append("pilot_cluster")
        self._track[serial] = _mark(sighting)
        self._remember(serial, sighting)
        if reasons:
            return _spoof(serial, sighting, source, reasons)
        held = ["remote_id_only"]
        if serial in self._link_seen:
            held.append("remote_id_position_ignored")
        if _at_origin(sighting):
            held.append("aircraft_at_origin")
        return Decision(
            serial=serial,
            verdict="hold",
            display=True,
            mark="şüpheli",
            reasons=held,
            pilot_lat=sighting.pilot_lat,
            pilot_lon=sighting.pilot_lon,
            model=sighting.model,
            source="remote_id",
        )

    def _expire(self, now: float) -> None:
        self._pilots = [item for item in self._pilots if now - item[0] <= CLUSTER_WINDOW_S]
        self._link_seen = {
            key: ts for key, ts in self._link_seen.items() if now - ts <= LINK_MEMORY_S
        }
        self._cluster_until = {
            key: until for key, until in self._cluster_until.items() if until >= now
        }

    def _motion(self, serial: str, sighting: Sighting) -> list[str]:
        reasons = []
        if sighting.speed_mps is not None and sighting.speed_mps > self.max_speed_mps:
            reasons.append("reported_speed")
        previous = self._track.get(serial)
        if previous is None or previous.lat is None or previous.lon is None:
            return reasons
        if not _has_fix(sighting):
            return reasons
        dt = sighting.ts - previous.ts
        if dt <= MIN_DT_S:
            return reasons
        moved = _meters(previous.lat, previous.lon, sighting.lat, sighting.lon)
        if moved / dt > self.max_speed_mps:
            reasons.append("implied_speed")
        return reasons

    def _remember(self, serial: str, sighting: Sighting) -> None:
        if not _has_fix(sighting):
            return
        points = self._history.setdefault(serial, [])
        points.append(_Fix(sighting.ts, sighting.lat, sighting.lon, sighting.alt_m))
        self._history[serial] = [item for item in points if sighting.ts - item.ts <= MOTION_HISTORY_S]

    def _consistency(self, serial: str, sighting: Sighting) -> list[str]:
        if not _has_fix(sighting):
            return []
        past = None
        for item in self._history.get(serial, []):
            age = sighting.ts - item.ts
            if MOTION_WINDOW_S <= age <= MOTION_HISTORY_S:
                past = item
                break
        if past is None:
            return []
        reasons = []
        dt = sighting.ts - past.ts
        moved = _meters(past.lat, past.lon, sighting.lat, sighting.lon)
        speed = sighting.speed_mps
        if speed is not None and speed >= SPEED_LIE_MPS and moved < speed * dt * MOTION_FRACTION:
            reasons.append("speed_without_motion")
            if sighting.yaw_deg is not None:
                reasons.append("heading_without_motion")
        elif (
            sighting.yaw_deg is not None
            and speed is not None
            and speed >= SPEED_LIE_MPS
            and moved >= HEADING_MIN_MOVE_M
            and _angle_diff(_bearing(past.lat, past.lon, sighting.lat, sighting.lon), sighting.yaw_deg)
            > HEADING_TOLERANCE_DEG
        ):
            reasons.append("heading_disagrees")
        if past.alt is not None and sighting.alt_m is not None and abs(sighting.alt_m - past.alt) / dt > MAX_VERTICAL_MPS:
            reasons.append("vertical_speed")
        return reasons

    def _clustered(self, serial: str, sighting: Sighting) -> bool:
        if sighting.pilot_lat is None or sighting.pilot_lon is None:
            return serial in self._cluster_until
        self._pilots.append((sighting.ts, serial, sighting.pilot_lat, sighting.pilot_lon))
        members = set()
        for ts, other, plat, plon in self._pilots:
            if sighting.ts - ts > CLUSTER_WINDOW_S:
                continue
            if _meters(sighting.pilot_lat, sighting.pilot_lon, plat, plon) <= CLUSTER_RADIUS_M:
                members.add(other)
        if len(members) < CLUSTER_MIN:
            return serial in self._cluster_until
        until = sighting.ts + CLUSTER_WINDOW_S
        for member in members:
            self._cluster_until[member] = until
        return True


def _spoof(serial: str, sighting: Sighting, source: str, reasons: list[str]) -> Decision:
    return Decision(
        serial=serial,
        verdict="spoof",
        display=True,
        mark="sahte",
        reasons=reasons,
        pilot_lat=sighting.pilot_lat,
        pilot_lon=sighting.pilot_lon,
        model=sighting.model,
        source=source,
    )


def _identity(serial: str, sighting: Sighting) -> list[str]:
    reasons = []
    if matches_template(serial):
        reasons.append("esp8266_template")
    ok, code = check_serial(serial)
    if not ok:
        reasons.append(code)
    if _PADDING.search(serial):
        reasons.append("serial_placeholder")
    if is_catalog_label(sighting.operator_id):
        reasons.append("operator_is_model")
    if is_catalog_label(sighting.self_id):
        reasons.append("self_id_is_model")
    if is_catalog_label(sighting.ssid):
        reasons.append("ssid_is_model")
    return reasons


def _at_origin(sighting: Sighting) -> bool:
    return sighting.lat == 0 and sighting.lon == 0


def _has_fix(sighting: Sighting) -> bool:
    return sighting.lat is not None and sighting.lon is not None


def _mark(sighting: Sighting) -> _Mark:
    return _Mark(sighting.ts, sighting.lat, sighting.lon)


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    east = math.sin(dl) * math.cos(p2)
    north = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(east, north)) + 360.0) % 360.0


def _angle_diff(left: float, right: float) -> float:
    gap = abs(left - right) % 360.0
    return min(gap, 360.0 - gap)


def _meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))
