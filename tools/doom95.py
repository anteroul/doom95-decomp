"""Shared helpers: repository paths, the original executable, its sections and the symbol table."""
import csv
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIG_EXE = ROOT / "orig" / "DOOM95.EXE"
SHA1_FILE = ROOT / "config" / "doom95.sha1"
SYMBOLS_CSV = ROOT / "config" / "symbols.csv"
MATCHED_TXT = ROOT / "config" / "matched.txt"
BUILD = ROOT / "build"


def expected_sha1():
    return SHA1_FILE.read_text().split()[0].lower()


def load_orig(check=True):
    if not ORIG_EXE.exists():
        raise SystemExit(f"missing {ORIG_EXE.relative_to(ROOT)}: copy your DOOM95.EXE v3.0 there (see orig/README.md)")
    data = ORIG_EXE.read_bytes()
    if check:
        got = hashlib.sha1(data).hexdigest()
        if got != expected_sha1():
            raise SystemExit(f"{ORIG_EXE.relative_to(ROOT)} has SHA-1 {got}, expected {expected_sha1()} (wrong version?)")
    return data


@dataclass
class Section:
    name: str
    va: int          # absolute virtual address
    raw_offset: int  # file offset
    raw_size: int


def sections(data):
    """PE sections. The Watcom linker left VirtualSize = 0, so SizeOfRawData is used as the size."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    image_base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    first = pe + 24 + opt_size
    result = []
    for i in range(count):
        s = first + 40 * i
        name = data[s:s + 8].rstrip(b"\0").decode("ascii")
        rva, raw_size, raw_offset = struct.unpack_from("<III", data, s + 12)
        result.append(Section(name, image_base + rva, raw_offset, raw_size))
    return result


def section_named(data, name):
    for s in sections(data):
        if s.name == name:
            return s
    raise KeyError(name)


def va_to_offset(data, va):
    for s in sections(data):
        if s.raw_offset and s.va <= va < s.va + s.raw_size:
            return va - s.va + s.raw_offset
    return None


@dataclass
class Symbol:
    address: int
    type: str       # "code" or "data"
    static: bool
    name: str
    raw_name: str
    section: str
    source: str

    @property
    def is_project(self):
        """True for Doom95's own source files (built from D:\\DEV\\...), False for the Watcom runtime."""
        return self.source.upper().startswith("D:\\DEV\\")

    @property
    def module(self):
        """Source file name without the original build path, e.g. 'w_wad.c'."""
        return self.source.replace("\\", "/").rsplit("/", 1)[-1] if self.source else ""


def load_symbols():
    with open(SYMBOLS_CSV, encoding="utf-8", newline="") as f:
        return [Symbol(int(r["address"], 16), r["type"], r["static"] == "yes", r["name"],
                       r["raw_name"], r["section"], r["source"]) for r in csv.DictReader(f)]


def functions(data, symbols):
    """Code symbols in the code section, one per address, with sizes up to the next symbol.

    The size is an upper bound: it includes any alignment padding after the function, and
    file-local (static) functions without a symbol are folded into the function before them.
    """
    text = section_named(data, "BEGTEXT")
    end = text.va + text.raw_size
    code = {}
    for s in symbols:
        if s.type == "code" and text.va <= s.address < end and s.address not in code:
            code[s.address] = s
    addrs = sorted(code)
    result = []
    for i, a in enumerate(addrs):
        nxt = addrs[i + 1] if i + 1 < len(addrs) else end
        result.append((code[a], nxt - a))
    return result


def load_matched():
    if not MATCHED_TXT.exists():
        return set()
    names = set()
    for line in MATCHED_TXT.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.add(line)
    return names
