"""Cut the original executable into one file of bytes per function, grouped by source module.

Usage:  python tools/split.py

Writes build/split/<module>/<function>.bin and build/split/functions.csv
(address, size, module, name). These are the targets your compiled code is compared against.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doom95  # noqa: E402


def safe(name):
    return re.sub(r"[^A-Za-z0-9_.@-]", "_", name)


def main():
    data = doom95.load_orig()
    funcs = doom95.functions(data, doom95.load_symbols())
    out = doom95.BUILD / "split"
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for sym, size in funcs:
        off = doom95.va_to_offset(data, sym.address)
        module = sym.module or "_unknown"
        folder = out / safe(module) if sym.is_project else out / "_lib" / safe(module)
        target = folder / f"{safe(sym.name)}.bin"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data[off:off + size])
        rows.append({"address": f"{sym.address:08X}", "size": size, "module": module, "name": sym.name,
                     "library": "no" if sym.is_project else "yes"})

    with open(out / "functions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["address", "size", "module", "name", "library"])
        w.writeheader()
        w.writerows(rows)

    game = [r for r in rows if r["library"] == "no"]
    lib = [r for r in rows if r["library"] == "yes"]
    print(f"Doom95: {len(game)} functions in {len({r['module'] for r in game})} modules, "
          f"{sum(r['size'] for r in game):,} bytes")
    print(f"Watcom runtime (build/split/_lib): {len(lib)} functions, {sum(r['size'] for r in lib):,} bytes")
    print(f"-> {out.relative_to(doom95.ROOT)}")


if __name__ == "__main__":
    main()
