"""Report decompilation progress: functions and bytes listed in config/matched.txt.

Usage:  python tools/progress.py            (summary + per-module table)
        python tools/progress.py --module w_wad.c   (list one module's functions)
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doom95  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", help="list the functions of one module, e.g. w_wad.c")
    args = ap.parse_args()

    data = doom95.load_orig()
    # Only Doom95's own source counts; the Watcom C runtime library is not decompiled.
    funcs = [(s, n) for s, n in doom95.functions(data, doom95.load_symbols()) if s.is_project]
    matched = doom95.load_matched()

    known = {s.name for s, _ in funcs}
    for name in sorted(matched - known):
        print(f"warning: matched.txt lists unknown function {name!r}")

    if args.module:
        rows = [(s, n) for s, n in funcs if s.module.lower() == args.module.lower()]
        if not rows:
            raise SystemExit(f"no functions in module {args.module!r}")
        for s, n in rows:
            mark = "x" if s.name in matched else " "
            print(f"[{mark}] {s.address:08X} {n:6d}  {s.name}")
        return

    per = defaultdict(lambda: [0, 0, 0, 0])  # functions, matched, bytes, matched bytes
    for s, n in funcs:
        m = per[s.module or "_unknown"]
        m[0] += 1
        m[2] += n
        if s.name in matched:
            m[1] += 1
            m[3] += n

    tf = sum(v[0] for v in per.values())
    tm = sum(v[1] for v in per.values())
    tb = sum(v[2] for v in per.values())
    tmb = sum(v[3] for v in per.values())
    print(f"Matched {tm}/{tf} functions, {tmb:,}/{tb:,} bytes ({100 * tmb / tb:.2f}%)\n")
    print(f"{'module':<16}{'functions':>12}{'bytes':>18}")
    for mod, (f, m, b, mb) in sorted(per.items(), key=lambda kv: -kv[1][2]):
        print(f"{mod:<16}{f'{m}/{f}':>12}{f'{mb:,}/{b:,}':>18}")


if __name__ == "__main__":
    main()
