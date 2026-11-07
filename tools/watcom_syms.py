"""Extract the global symbol table from the Watcom v3 debug info appended to DOOM95.EXE.

Usage:  python tools/watcom_syms.py orig/DOOM95.EXE config/symbols.csv

Layout (all little-endian), as found in DOOM95.EXE:
  end of file - 14 bytes : master header
      u16 signature (0x8386), u8 exe_major, u8 exe_minor, u8 obj_major, u8 obj_minor,
      u16 lang_size, u16 segment_size, u32 debug_size
  debug start = file size - debug_size
      lang_size bytes    : NUL-separated language names ("C", "CPP")
      segment_size bytes : u16 segment numbers
      section header     : u32 mod_offset, u32 gbl_offset, u32 addr_offset, u32 section_size, u16 id
  modules  (section + mod_offset .. gbl_offset):
      u16 language, 3 x (u32 offset, u16 count) demand info, u8 name_len, name
  globals  (section + gbl_offset .. addr_offset):
      u32 offset, u16 segment, u16 module, u8 kind, u8 name_len, name
      kind bits: 1 = static (file-local), 2 = data, 4 = code
"""
import csv
import struct
import sys

WATCOM_SIGNATURE = 0x8386
MASTER_HEADER_SIZE = 14
SECTION_HEADER_SIZE = 18
MODULE_FIXED_SIZE = 20

# Symbols flagged as code (they live in BEGTEXT) that are really data. Disassembling them
# as code corrupts the functions that follow.
#   ___begtext          Watcom start-of-code marker (padding)
#   _english_shiftxform 256-byte character table from hu_stuff.c
NOT_CODE = {"___begtext", "_english_shiftxform"}


def pe_section_bases(data):
    """Return {1-based section number: (name, virtual address)} using the PE image base."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    count = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    image_base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    first = pe + 24 + opt_size
    bases = {}
    for i in range(count):
        s = first + 40 * i
        name = data[s:s + 8].rstrip(b"\0").decode("ascii")
        rva = struct.unpack_from("<I", data, s + 12)[0]
        bases[i + 1] = (name, image_base + rva)
    return bases


def read_debug_info(data):
    sig, exe_maj, exe_min, _obj_maj, _obj_min, lang_size, seg_size, debug_size = struct.unpack_from(
        "<HBBBBHHI", data, len(data) - MASTER_HEADER_SIZE)
    if sig != WATCOM_SIGNATURE:
        raise ValueError("no Watcom debug info signature at end of file")
    if exe_maj != 3:
        raise ValueError(f"unsupported Watcom debug format {exe_maj}.{exe_min}")
    start = len(data) - debug_size
    section = start + lang_size + seg_size
    mod_off, gbl_off, addr_off, _size, _sid = struct.unpack_from("<IIIIH", data, section)

    modules = []
    pos, end = section + mod_off, section + gbl_off
    while pos < end:
        pos += MODULE_FIXED_SIZE
        n = data[pos]
        modules.append(data[pos + 1:pos + 1 + n].decode("latin-1"))
        pos += 1 + n

    symbols = []
    pos, end = section + gbl_off, section + addr_off
    while pos < end:
        offset, segment, module, kind, n = struct.unpack_from("<IHHBB", data, pos)
        name = data[pos + 10:pos + 10 + n].decode("latin-1")
        symbols.append((offset, segment, module, kind, name))
        pos += 10 + n
    if pos != end:
        raise ValueError("global table did not end on a record boundary")
    return modules, symbols


def clean_name(name, is_code):
    """Watcom: 'Foo_' = register-calling function, '_Foo' = cdecl function or data,
    'W?Foo$n(args)ret' = mangled C++ name (keep just 'Foo'),
    'W?$Wsi0var$n...:?Func$n(...)...' = static local 'var' inside 'Func' (-> 'Func_var')."""
    if name.startswith("W?$Wsi0") and ":?" in name:
        # The first character after 'W?$Wsi0' is a mangling code, not part of the name.
        var = name[len("W?$Wsi0") + 1:].split("$", 1)[0]
        func = name.split(":?", 1)[1].split("$", 1)[0]
        return f"{func}_{var}"
    if name.startswith("W?"):
        base = name[2:].split("$", 1)[0].lstrip(".")
        return base or name
    if is_code and name.endswith("_") and not name.startswith("_"):
        return name[:-1]
    if name.startswith("_") and len(name) > 1:
        return name[1:]
    return name


def main(exe_path, out_path):
    with open(exe_path, "rb") as f:
        data = f.read()
    bases = pe_section_bases(data)
    modules, symbols = read_debug_info(data)

    rows = []
    for offset, segment, module, kind, name in symbols:
        if segment not in bases:
            raise ValueError(f"{name}: unknown segment {segment}")
        section_name, base = bases[segment]
        is_code = bool(kind & 4) and name not in NOT_CODE
        rows.append({
            "address": f"{base + offset:08X}",
            "type": "code" if is_code else "data",
            "static": "yes" if kind & 1 else "no",
            "name": clean_name(name, is_code),
            "raw_name": name,
            "section": section_name,
            "source": modules[module] if module < len(modules) else "",
        })
    rows.sort(key=lambda r: r["address"])

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    code = sum(r["type"] == "code" for r in rows)
    print(f"{len(modules)} modules, {len(rows)} symbols ({code} code, {len(rows) - code} data) -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
