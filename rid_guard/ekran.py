"""Yerel ekran. Solda MT303 akışı, sağda aktif sahte listesi.

  python3 -m rid_guard.ekran

MT303 192.168.0.200 port 10123. Bu makine 192.168.0.10 olmalı.
Bağlantı düğmeye basınca açılır. Aynı portu başka bir program tutuyorsa bağlanmaz.
"""

import json
import os
import re
import socket
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from rid_guard.decide import Guard
from rid_guard.parse import ParseError, read_line

HOST = os.environ.get("RIDGUARD_MT_HOST", "192.168.0.200")
PORT = int(os.environ.get("RIDGUARD_MT_PORT", "10123"))
UI_HOST = "127.0.0.1"
UI_PORT = int(os.environ.get("RIDGUARD_UI_PORT", "8765"))
LOG = Path(os.environ.get("RIDGUARD_LOG", "/home/talha/Desktop/MT303/izle/akis.log"))
ACTIVE_S = 20.0
IDLE_S = 3.0
PAGE = Path(__file__).with_name("ekran.html")

_RSSI = re.compile(r"rssi:(-?\d+(?:\.\d+)?)")
_PROTO = re.compile(r"protocol:([^,\s]+)")
_CHAN = re.compile(r"channel:([^,\s]+)")


class Board:
    def __init__(self, active_s: float = ACTIVE_S) -> None:
        self.active_s = active_s
        self.guard = Guard()
        self.lines: deque[str] = deque(maxlen=300)
        self.fakes: dict[str, dict] = {}
        self.lock = threading.Lock()

    def ingest(self, line: str, now: float | None = None) -> None:
        stamp = time.monotonic() if now is None else now
        with self.lock:
            self.lines.append(line)
            self._take(line, stamp)
            self._drop(stamp)

    def clear(self) -> None:
        with self.lock:
            self.lines.clear()
            self.fakes.clear()
            self.guard = Guard()

    def snapshot(self, now: float | None = None) -> dict:
        stamp = time.monotonic() if now is None else now
        with self.lock:
            self._drop(stamp)
            fakes = []
            for item in self.fakes.values():
                row = dict(item)
                row["age_s"] = round(stamp - item["seen"], 1)
                row.pop("seen", None)
                fakes.append(row)
            fakes.sort(key=lambda row: row["age_s"])
            return {"lines": list(self.lines), "fakes": fakes}

    def _take(self, line: str, stamp: float) -> None:
        try:
            sighting = read_line(line)
        except ParseError:
            return
        if sighting is None:
            return
        decision = self.guard.observe(sighting)
        if decision.mark != "sahte":
            return
        previous = self.fakes.get(decision.serial)
        count = 1 if previous is None else previous["count"] + 1
        rssi = _number(_RSSI, line)
        self.fakes[decision.serial] = {
            "serial": decision.serial,
            "model": decision.model,
            "mark": "sahte",
            "rssi": rssi,
            "protocol": _text(_PROTO, line),
            "channel": _text(_CHAN, line),
            "pilot_lat": decision.pilot_lat,
            "pilot_lon": decision.pilot_lon,
            "count": count,
            "seen": stamp,
        }

    def _drop(self, stamp: float) -> None:
        stale = [key for key, item in self.fakes.items() if stamp - item["seen"] > self.active_s]
        for key in stale:
            del self.fakes[key]


class Live:
    def __init__(
        self,
        host: str = HOST,
        port: int = PORT,
        log_path: Path = LOG,
        idle_s: float = IDLE_S,
    ) -> None:
        self.host = host
        self.port = port
        self.log_path = log_path
        self.idle_s = idle_s
        self.board = Board()
        self.status = "kapalı"
        self.error = ""
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._sock: socket.socket | None = None
        self._session = 0
        self._last_rx = 0.0

    def connect(self) -> None:
        with self._lock:
            if self.status in {"bağlı", "bağlanıyor"}:
                return
            self._stop.set()
            self._session += 1
            session = self._session
            stop = threading.Event()
            self._stop = stop
            self.status = "bağlanıyor"
            self.error = ""
        self.board.clear()
        threading.Thread(target=self._run, args=(session, stop), daemon=True).start()

    def disconnect(self) -> None:
        with self._lock:
            self._session += 1
            self._stop.set()
            sock = self._sock
            self._sock = None
            self.status = "kapalı"
            self.error = ""
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        self.board.clear()

    def snapshot(self) -> dict:
        with self._lock:
            status = self.status
            error = self.error
        body = self.board.snapshot()
        body.update(
            {
                "status": status,
                "error": error,
                "host": self.host,
                "port": self.port,
            }
        )
        return body

    def _run(self, session: int, stop: threading.Event) -> None:
        try:
            sock = socket.create_connection((self.host, self.port), timeout=5)
        except TimeoutError:
            self._fail(session, "MT303 ağda yok")
            return
        except OSError as exc:
            self._fail(session, _os_message(exc))
            return
        sock.settimeout(1)
        _keepalive(sock)
        with self._lock:
            if session != self._session or stop.is_set():
                sock.close()
                if session == self._session:
                    self.status = "kapalı"
                return
            self._sock = sock
            self.status = "bağlı"
            self.error = ""
            self._last_rx = time.monotonic()
        self.board.clear()
        buf = b""
        try:
            while not stop.is_set() and session == self._session:
                try:
                    chunk = sock.recv(4096)
                except TimeoutError:
                    if time.monotonic() - self._last_rx > self.idle_s:
                        self._fail(session, "bağlantı koptu")
                        return
                    continue
                if not chunk:
                    if session == self._session and not stop.is_set():
                        self._fail(session, "bağlantı kapandı")
                    return
                self._last_rx = time.monotonic()
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("utf-8", "replace").strip("\r")
                    if not line or session != self._session:
                        continue
                    self.board.ingest(line)
                    _append(self.log_path, line)
        except OSError as exc:
            if session == self._session and not stop.is_set():
                self._fail(session, _os_message(exc))
        finally:
            with self._lock:
                if self._sock is sock:
                    self._sock = None
            try:
                sock.close()
            except OSError:
                pass
            with self._lock:
                if session == self._session and self.status == "bağlı":
                    self.status = "kapalı"
            if session == self._session and self.status == "kapalı":
                self.board.clear()

    def _fail(self, session: int, message: str) -> None:
        with self._lock:
            if session != self._session:
                return
            self.status = "hata"
            self.error = message
        self.board.clear()


def _keepalive(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 2)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)
    except OSError:
        return


def _os_message(exc: OSError) -> str:
    if getattr(exc, "errno", None) in {111, 10061}:
        return "port kapalı"
    text = str(exc).lower()
    if "refused" in text:
        return "port kapalı"
    if "timed out" in text or "timeout" in text:
        return "MT303 ağda yok"
    return "bağlantı kurulamadı"


def _append(path: Path, line: str) -> None:
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        return


def _number(pattern: re.Pattern[str], line: str) -> float | None:
    found = pattern.search(line)
    if found is None:
        return None
    try:
        return float(found.group(1))
    except ValueError:
        return None


def _text(pattern: re.Pattern[str], line: str) -> str:
    found = pattern.search(line)
    return found.group(1) if found else ""


def serve(live: Live, port: int = UI_PORT) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path.split("?", 1)[0] == "/":
                body = PAGE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path.split("?", 1)[0] == "/api/state":
                self._json(self.server.live.snapshot())
                return
            self.send_error(404)

        def do_POST(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/api/connect":
                self.server.live.connect()
                self._json(self.server.live.snapshot())
                return
            if path == "/api/disconnect":
                self.server.live.disconnect()
                self._json(self.server.live.snapshot())
                return
            self.send_error(404)

        def _json(self, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            return

    httpd = ThreadingHTTPServer((UI_HOST, port), Handler)
    httpd.live = live
    return httpd


def main() -> None:
    live = Live(HOST, PORT, LOG)
    httpd = serve(live, UI_PORT)
    print(f"http://{UI_HOST}:{UI_PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        live.disconnect()
        httpd.shutdown()


if __name__ == "__main__":
    main()
