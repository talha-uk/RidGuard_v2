import json
import socket
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rid_guard.ekran import Board, Live, serve

RID = (
    "$RID,protocol:beacon,channel:6,uav_id:1581F6N8RID06XXXXXXX,yaw_angle:69,"
    "speed:24.50,latitude:39.8124946,longitude:32.4321041,altitude_qne:-1000.0,"
    "altitude_geo:251.0,height:171.0,latitude_polit:39.8130019,"
    "longitude_polit:32.4321008,timestamp1:0.0,timestamp2:708224640,rssi:-11,$end"
)
OTHER = (
    "$RID,protocol:beacon,channel:6,uav_id:1581F6Z9RID03XXXXXXX,yaw_angle:0,"
    "speed:0.00,latitude:0.0000000,longitude:0.0000000,altitude_qne:0.0,"
    "altitude_geo:0.0,height:0.0,latitude_polit:39.8134019,"
    "longitude_polit:32.4313008,timestamp1:0.0,timestamp2:708224640,rssi:-69,$end"
)


class BoardTests(unittest.TestCase):
    def test_rid_becomes_an_active_fake(self):
        board = Board()
        board.ingest(RID, now=10)
        row = board.snapshot(now=11)["fakes"][0]
        self.assertEqual(row["serial"], "1581F6N8RID06XXXXXXX")
        self.assertEqual(row["model"], "DJI Air 3")
        self.assertEqual(row["mark"], "sahte")
        self.assertEqual(row["rssi"], -11)
        self.assertEqual(row["protocol"], "beacon")
        self.assertEqual(row["channel"], "6")
        self.assertEqual(row["pilot_lat"], 39.8130019)
        self.assertEqual(row["count"], 1)
        self.assertEqual(row["age_s"], 1)

    def test_repeat_updates_the_same_row(self):
        board = Board()
        board.ingest(RID, now=10)
        board.ingest(RID.replace("rssi:-11", "rssi:-8"), now=12)
        rows = board.snapshot(now=13)["fakes"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["count"], 2)
        self.assertEqual(rows[0]["rssi"], -8)

    def test_two_serials_stay_listed(self):
        board = Board()
        board.ingest(RID, now=10)
        board.ingest(OTHER, now=11)
        serials = [row["serial"] for row in board.snapshot(now=12)["fakes"]]
        self.assertEqual(serials, ["1581F6Z9RID03XXXXXXX", "1581F6N8RID06XXXXXXX"])

    def test_quiet_serial_leaves_the_active_list(self):
        board = Board(active_s=20)
        board.ingest(RID, now=0)
        self.assertEqual(board.snapshot(now=20)["fakes"][0]["serial"], "1581F6N8RID06XXXXXXX")
        self.assertEqual(board.snapshot(now=20.1)["fakes"], [])

    def test_heartbeat_and_feature_stay_on_the_left_only(self):
        board = Board()
        board.ingest("$heartbeat,serial:3844BE214DAC,lat:0.0,lng:0.0,$end", now=1)
        board.ingest("$Feature,protocol:O3,freq:5796.00MHz,rssi:-3.1,$end", now=2)
        body = board.snapshot(now=3)
        self.assertEqual(len(body["lines"]), 2)
        self.assertEqual(body["fakes"], [])


class LiveTests(unittest.TestCase):
    def test_button_connects_and_fills_both_sides(self):
        stop = threading.Event()
        ready = []

        def box() -> None:
            srv = socket.socket()
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            ready.append(srv.getsockname()[1])
            srv.settimeout(0.3)
            while not stop.is_set():
                try:
                    conn, _addr = srv.accept()
                except TimeoutError:
                    continue
                payload = (RID + "\n$heartbeat,serial:3844BE214DAC,lat:0.0,lng:0.0,$end\n").encode()
                try:
                    while not stop.is_set():
                        conn.sendall(payload)
                        time.sleep(0.2)
                except OSError:
                    return
                finally:
                    conn.close()
            srv.close()

        thread = threading.Thread(target=box, daemon=True)
        thread.start()
        while not ready:
            time.sleep(0.01)
        live = Live("127.0.0.1", ready[0], Path("/tmp/ridguard-ekran-test.log"))
        httpd = serve(live, 0)
        port = httpd.server_address[1]
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        try:
            page = urllib.request.urlopen(f"http://127.0.0.1:{port}/").read().decode()
            self.assertIn("MT303", page)
            self.assertIn("Sahte ve şüpheli", page)
            self.assertIn('id="connect"', page)
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/connect", method="POST"))
            deadline = time.monotonic() + 3
            body = {}
            while time.monotonic() < deadline:
                body = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state"))
                if (
                    body["status"] == "bağlı"
                    and body["fakes"]
                    and any(line.startswith("$heartbeat") for line in body["lines"])
                ):
                    break
                time.sleep(0.05)
            self.assertEqual(body["status"], "bağlı")
            self.assertTrue(any(line.startswith("$heartbeat") for line in body["lines"]))
            self.assertEqual(body["fakes"][0]["model"], "DJI Air 3")
            self.assertEqual(body["fakes"][0]["mark"], "sahte")
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/disconnect", method="POST"))
            closed = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state"))
            self.assertEqual(closed["status"], "kapalı")
            self.assertEqual(closed["lines"], [])
            self.assertEqual(closed["fakes"], [])
        finally:
            stop.set()
            live.disconnect()
            httpd.shutdown()

    def test_connect_keeps_only_lines_from_this_link(self):
        stop = threading.Event()
        ready = []

        def box() -> None:
            srv = socket.socket()
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            ready.append(srv.getsockname()[1])
            srv.settimeout(0.3)
            while not stop.is_set():
                try:
                    conn, _addr = srv.accept()
                except TimeoutError:
                    continue
                try:
                    conn.sendall(b"$heartbeat,serial:YENI,lat:0.0,lng:0.0,$end\n")
                    while not stop.is_set():
                        time.sleep(0.1)
                except OSError:
                    return
                finally:
                    conn.close()
            srv.close()

        threading.Thread(target=box, daemon=True).start()
        while not ready:
            time.sleep(0.01)
        live = Live("127.0.0.1", ready[0], Path("/tmp/ridguard-ekran-test.log"), idle_s=5)
        live.board.ingest("$heartbeat,serial:ESKI,lat:0.0,lng:0.0,$end", now=1)
        live.connect()
        try:
            deadline = time.monotonic() + 3
            body = {}
            while time.monotonic() < deadline:
                body = live.snapshot()
                if body["status"] == "bağlı" and any("YENI" in line for line in body["lines"]):
                    break
                time.sleep(0.05)
            self.assertEqual(body["status"], "bağlı")
            self.assertTrue(all("ESKI" not in line for line in body["lines"]))
            self.assertTrue(any("YENI" in line for line in body["lines"]))
        finally:
            stop.set()
            live.disconnect()

    def test_silence_clears_the_log(self):
        stop = threading.Event()
        ready = []

        def box() -> None:
            srv = socket.socket()
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            ready.append(srv.getsockname()[1])
            srv.settimeout(0.3)
            while not stop.is_set():
                try:
                    conn, _addr = srv.accept()
                except TimeoutError:
                    continue
                try:
                    conn.sendall(b"$heartbeat,serial:YENI,lat:0.0,lng:0.0,$end\n")
                    while not stop.is_set():
                        time.sleep(0.1)
                except OSError:
                    return
                finally:
                    conn.close()
            srv.close()

        threading.Thread(target=box, daemon=True).start()
        while not ready:
            time.sleep(0.01)
        live = Live("127.0.0.1", ready[0], Path("/tmp/ridguard-ekran-test.log"), idle_s=0.4)
        live.connect()
        try:
            deadline = time.monotonic() + 4
            body = {}
            while time.monotonic() < deadline:
                body = live.snapshot()
                if body["status"] == "hata":
                    break
                time.sleep(0.05)
            self.assertEqual(body["status"], "hata")
            self.assertEqual(body["error"], "bağlantı koptu")
            self.assertEqual(body["lines"], [])
            self.assertEqual(body["fakes"], [])
        finally:
            stop.set()
            live.disconnect()


if __name__ == "__main__":
    unittest.main()
