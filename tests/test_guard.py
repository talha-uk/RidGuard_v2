import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rid_guard.cta2063 import check_serial
from rid_guard.decide import Guard
from rid_guard.models import Sighting
from rid_guard.parse import ParseError, parse_line, read_line
from rid_guard.template import known_templates, matches_template


LAB = Sighting(
    ts=1_700_000_000.0,
    source="remote_id",
    serial="1581F5YHRID01XXXXXXX",
    model="DJI Mini 3",
    lat=39.8132,
    lon=32.4318,
    pilot_lat=39.8132,
    pilot_lon=32.4318,
    operator_id="DJI Mini 3",
    speed_mps=2.0,
)

CLEAN = "1581FA23456789ABCDEF"


def _clean(serial: str, ts: float, source: str = "remote_id") -> Sighting:
    return Sighting(
        ts=ts,
        source=source,
        serial=serial,
        model="DJI Mini 3",
        lat=39.8132,
        lon=32.4318,
        pilot_lat=39.8132,
        pilot_lon=32.4318,
        operator_id="TR-OP-1001",
        speed_mps=3.0,
    )


class SerialTests(unittest.TestCase):
    def test_lab_serial_fails_alphabet(self):
        ok, code = check_serial("1581F5YHRID01XXXXXXX")
        self.assertFalse(ok)
        self.assertEqual(code, "serial_alphabet")

    def test_padded_name_fails(self):
        ok, _code = check_serial("DJIMINISEXXXXXXXXXXX")
        self.assertFalse(ok)

    def test_cta_shape_passes(self):
        ok, code = check_serial(CLEAN)
        self.assertTrue(ok)
        self.assertEqual(code, "serial_ok")

    def test_parrot_example_passes(self):
        ok, code = check_serial("1588E040452P3001126")
        self.assertTrue(ok, code)

    def test_length_code_mismatch(self):
        ok, code = check_serial("1581A5YH23456789ABCD")
        self.assertFalse(ok)
        self.assertEqual(code, "serial_length_code")


class GuardTests(unittest.TestCase):
    def test_lab_broadcast_is_marked_fake(self):
        decision = Guard().observe(LAB)
        self.assertEqual(decision.verdict, "spoof")
        self.assertTrue(decision.display)
        self.assertEqual(decision.mark, "sahte")
        self.assertEqual(
            decision.reasons,
            ["esp8266_template", "serial_alphabet", "serial_placeholder", "operator_is_model"],
        )
        self.assertIsNone(decision.lat)
        self.assertEqual(decision.pilot_lat, 39.8132)
        self.assertEqual(decision.pilot_lon, 32.4318)

    def test_every_firmware_serial_is_marked_fake(self):
        guard = Guard()
        serials = known_templates()
        self.assertGreaterEqual(len(serials), 18)
        for index, serial in enumerate(serials):
            self.assertTrue(matches_template(serial), serial)
            decision = guard.observe(
                Sighting(
                    ts=1000.0 + index,
                    source="ocusync",
                    serial=serial,
                    model="DJI Mini 3",
                    lat=39.8132,
                    lon=32.4318,
                    pilot_lat=39.8132,
                    pilot_lon=32.4318,
                    operator_id="DJI Mini 3",
                    self_id="DJI Mini 3",
                    ssid="DJI Mini 3",
                )
            )
            self.assertEqual(decision.verdict, "spoof", serial)
            self.assertTrue(decision.display, serial)
            self.assertEqual(decision.mark, "sahte", serial)
            self.assertIsNone(decision.lat, serial)
            self.assertIn("esp8266_template", decision.reasons)

    def test_changed_rid_slot_still_matches(self):
        serial = "1581F5YHRID99XXXXXXX"
        self.assertTrue(matches_template(serial))
        decision = Guard().observe(_clean(serial, 10.0, source="ocusync"))
        self.assertEqual(decision.verdict, "spoof")
        self.assertTrue(decision.display)
        self.assertEqual(decision.mark, "sahte")
        self.assertIsNone(decision.lat)
        self.assertEqual(decision.source, "ocusync")

    def test_clean_remote_id_stays_off_the_picture(self):
        decision = Guard().observe(_clean(CLEAN, 10.0))
        self.assertEqual(decision.verdict, "hold")
        self.assertFalse(decision.display)
        self.assertEqual(decision.reasons, ["remote_id_only"])
        self.assertIsNone(decision.lat)

    def test_speed_limit_is_strict(self):
        under = Sighting(
            ts=10.0,
            source="remote_id",
            serial=CLEAN,
            lat=39.8132,
            lon=32.4318,
            speed_mps=45.0,
            operator_id="TR-OP-1001",
        )
        over = Sighting(
            ts=10.0,
            source="remote_id",
            serial=CLEAN,
            lat=39.8132,
            lon=32.4318,
            speed_mps=45.1,
            operator_id="TR-OP-1001",
        )
        self.assertEqual(Guard().observe(under).verdict, "hold")
        self.assertIn("reported_speed", Guard().observe(over).reasons)

    def test_ocusync_is_displayed(self):
        decision = Guard().observe(_clean(CLEAN, 10.0, source="ocusync"))
        self.assertEqual(decision.verdict, "confirmed")
        self.assertTrue(decision.display)
        self.assertEqual(decision.lat, 39.8132)

    def test_fingerprint_is_displayed(self):
        decision = Guard().observe(_clean(CLEAN, 10.0, source="fingerprint"))
        self.assertTrue(decision.display)
        self.assertEqual(decision.source, "fingerprint")

    def test_remote_id_does_not_move_a_link_pin(self):
        guard = Guard()
        link = guard.observe(_clean(CLEAN, 10.0, source="ocusync"))
        echo = Sighting(
            ts=11.0,
            source="remote_id",
            serial=CLEAN,
            lat=39.8132,
            lon=32.4318,
            pilot_lat=39.8132,
            pilot_lon=32.4318,
            operator_id="TR-OP-1001",
        )
        decision = guard.observe(echo)
        self.assertEqual(decision.verdict, "hold")
        self.assertFalse(decision.display)
        self.assertIsNone(decision.lat)
        self.assertIn("remote_id_position_ignored", decision.reasons)
        self.assertEqual(link.lat, 39.8132)

    def test_impossible_jump_is_spoof(self):
        guard = Guard()
        guard.observe(_clean(CLEAN, 10.0))
        jumped = Sighting(
            ts=11.0,
            source="remote_id",
            serial=CLEAN,
            lat=39.8232,
            lon=32.4318,
            operator_id="TR-OP-1001",
        )
        decision = guard.observe(jumped)
        self.assertEqual(decision.verdict, "spoof")
        self.assertIn("implied_speed", decision.reasons)
        self.assertIsNone(decision.lat)

    def test_four_aircraft_one_pilot_become_spoof(self):
        guard = Guard()
        serials = [
            "1581FA23456789ABCDEF",
            "1581FB23456789ABCDEF",
            "1581FC23456789ABCDEF",
            "1581FD23456789ABCDEF",
        ]
        decisions = [guard.observe(_clean(serial, 100.0 + index)) for index, serial in enumerate(serials)]
        self.assertEqual(decisions[0].verdict, "hold")
        self.assertEqual(decisions[3].verdict, "spoof")
        self.assertIn("pilot_cluster", decisions[3].reasons)
        again = guard.observe(_clean(serials[0], 104.0))
        self.assertEqual(again.verdict, "spoof")
        self.assertFalse(again.display)
        later = guard.observe(_clean(serials[0], 120.0))
        self.assertEqual(later.verdict, "hold")

    def test_catalog_operator_on_a_clean_serial_is_spoof(self):
        sighting = _clean(CLEAN, 10.0)
        sighting = Sighting(
            ts=10.0,
            source="remote_id",
            serial=CLEAN,
            lat=39.8132,
            lon=32.4318,
            operator_id="dji  mini   3",
        )
        decision = Guard().observe(sighting)
        self.assertEqual(decision.verdict, "spoof")
        self.assertIn("operator_is_model", decision.reasons)


class ParseTests(unittest.TestCase):
    def test_unknown_source_is_remote_id(self):
        sighting = parse_line('{"ts": 1, "serial": "ABC", "source": "wifi"}')
        self.assertEqual(sighting.source, "remote_id")

    def test_mt303_field_names(self):
        sighting = parse_line(
            '{"ts": 1, "serial_number": "1581F5YHRID01XXXXXXX",'
            ' "latitude": 39.81, "longitude": 32.43, "altitude": 12,'
            ' "airspeed": 2, "pilot_latitude": 39.81, "pilot_longitude": 32.43,'
            ' "operator": "DJI Mini 3", "self_id": "DJI Mini 3",'
            ' "ssid": "DJI Mini 3", "mode": "Remote ID"}'
        )
        self.assertEqual(sighting.source, "remote_id")
        self.assertEqual(sighting.lat, 39.81)
        self.assertEqual(sighting.alt_m, 12)
        self.assertEqual(sighting.speed_mps, 2)
        decision = Guard().observe(sighting)
        self.assertTrue(decision.display)
        self.assertEqual(decision.mark, "sahte")
        self.assertIsNone(decision.lat)
        self.assertIn("esp8266_template", decision.reasons)
        self.assertIn("self_id_is_model", decision.reasons)
        self.assertIn("ssid_is_model", decision.reasons)

    def test_ocusync_mode_label(self):
        sighting = parse_line(
            '{"ts": 1, "serial": "1581FA23456789ABCDEF", "mode": "OcuSync O3",'
            ' "latitude": 39.82, "longitude": 32.44}'
        )
        self.assertEqual(sighting.source, "ocusync")
        self.assertTrue(Guard().observe(sighting).display)

    def test_o4_token_is_a_link(self):
        sighting = parse_line('{"ts": 1, "serial": "1581FA23456789ABCDEF", "mode": "O4"}')
        self.assertEqual(sighting.source, "ocusync")

    def test_bare_protocol_is_not_a_link(self):
        sighting = parse_line('{"ts": 1, "serial": "1581FA23456789ABCDEF", "mode": "protocol"}')
        self.assertEqual(sighting.source, "remote_id")
        self.assertFalse(Guard().observe(sighting).display)

    def test_missing_serial(self):
        with self.assertRaises(ParseError):
            parse_line('{"ts": 1}')

    def test_not_json_rejected(self):
        with self.assertRaises(ParseError):
            parse_line("model=DJI")

    def test_live_rid_line_is_marked_fake(self):
        line = (
            "$RID,protocol:beacon,channel:6,uav_id:1581F6Z9RID03XXXXXXX,yaw_angle:0,"
            "speed:0.00,latitude:0.0000000,longitude:0.0000000,altitude_qne:0.0,"
            "altitude_geo:0.0,height:0.0,latitude_polit:39.8134019,"
            "longitude_polit:32.4313008,timestamp1:0.0,timestamp2:708224640,rssi:-69,$end"
        )
        sighting = read_line(line)
        self.assertIsNotNone(sighting)
        decision = Guard().observe(sighting)
        self.assertEqual(decision.serial, "1581F6Z9RID03XXXXXXX")
        self.assertEqual(decision.mark, "sahte")
        self.assertTrue(decision.display)
        self.assertIsNone(decision.lat)
        self.assertEqual(decision.pilot_lat, 39.8134019)
        self.assertEqual(decision.pilot_lon, 32.4313008)
        self.assertEqual(decision.model, "DJI Mini 4 Pro")
        self.assertEqual(decision.source, "remote_id")

    def test_heartbeat_and_feature_are_not_aircraft(self):
        self.assertIsNone(read_line("$heartbeat,serial:3844BE214DAC,lat:0.0,lng:0.0,$end"))
        self.assertIsNone(read_line("$Feature,protocol:O3,freq:5796.00MHz,rssi:-3.1,$end"))


class CliTests(unittest.TestCase):
    def test_replay_hides_lab_and_shows_link(self):
        sample = ROOT / "fixtures" / "lab_and_link.jsonl"
        proc = subprocess.run(
            [sys.executable, "-m", "rid_guard", "--file", str(sample)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        rows = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertTrue(rows[0]["display"])
        self.assertEqual(rows[0]["verdict"], "spoof")
        self.assertEqual(rows[0]["mark"], "sahte")
        self.assertIsNone(rows[0]["lat"])
        self.assertTrue(rows[1]["display"])
        self.assertEqual(rows[1]["verdict"], "confirmed")
        self.assertEqual(rows[1]["mark"], "")

    def test_only_screen_keeps_the_fake_mark(self):
        sample = ROOT / "fixtures" / "lab_and_link.jsonl"
        proc = subprocess.run(
            [sys.executable, "-m", "rid_guard", "--only-screen", "--file", str(sample)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        rows = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["mark"], "sahte")
        self.assertIsNone(rows[0]["lat"])
        self.assertEqual(rows[1]["verdict"], "confirmed")
        self.assertEqual(rows[1]["serial"], CLEAN)

    def test_bad_line_stays_off_stdout(self):
        proc = subprocess.run(
            [sys.executable, "-m", "rid_guard"],
            cwd=ROOT,
            input="model=DJI\n",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(proc.stdout, "")
        note = json.loads(proc.stderr.strip())
        self.assertEqual(note["verdict"], "reject")
        self.assertFalse(note["display"])

    def test_show_hold_draws_a_clean_remote_id(self):
        payload = {
            "ts": 10,
            "serial": CLEAN,
            "source": "remote_id",
            "lat": 39.8132,
            "lon": 32.4318,
            "operator_id": "TR-OP-1001",
        }
        proc = subprocess.run(
            [sys.executable, "-m", "rid_guard", "--show-hold"],
            cwd=ROOT,
            input=json.dumps(payload) + "\n",
            capture_output=True,
            text=True,
            check=True,
        )
        row = json.loads(proc.stdout.strip())
        self.assertEqual(row["verdict"], "hold")
        self.assertTrue(row["display"])
        self.assertEqual(row["lat"], 39.8132)


if __name__ == "__main__":
    unittest.main()
