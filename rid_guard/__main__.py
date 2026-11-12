"""JSON satır oku, her satır için bir karar yaz.

  python3 -m rid_guard --file kayit.jsonl
  python3 -m rid_guard --only-screen --file kayit.jsonl

Tanınmayan satır stderr'e düşer ve ekrana drone eklemez.
Sahte, şüpheli ve sürü kimliği ekrana girer, uçak iğnesi almaz.
--show-hold şüpheli kaydın iddia edilen yerini de basar.
"""

import argparse
import json
import sys

from rid_guard.decide import Guard
from rid_guard.parse import ParseError, read_line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MT303 Remote ID karar katmanı")
    parser.add_argument("--file", help="JSONL kayıt. Yoksa stdin.")
    parser.add_argument(
        "--show-hold",
        action="store_true",
        help="Yapısı düzgün Remote ID kaydını da çiz. Varsayılan kapalı.",
    )
    parser.add_argument(
        "--only-screen",
        action="store_true",
        help="Yalnız ekrana girecek satırı bas.",
    )
    args = parser.parse_args(argv)
    guard = Guard()
    stream = open(args.file, encoding="utf-8") if args.file else sys.stdin
    try:
        for line in stream:
            if not line.strip():
                continue
            try:
                sighting = read_line(line)
            except ParseError as exc:
                print(
                    json.dumps({"verdict": "reject", "display": False, "reason": str(exc)}),
                    file=sys.stderr,
                )
                continue
            if sighting is None:
                continue
            decision = guard.observe(sighting)
            payload = decision.as_dict()
            if args.show_hold and decision.verdict == "hold":
                payload["display"] = True
                payload["lat"] = sighting.lat
                payload["lon"] = sighting.lon
            if args.only_screen and not payload["display"]:
                continue
            print(json.dumps(payload, ensure_ascii=False))
    finally:
        if args.file:
            stream.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
