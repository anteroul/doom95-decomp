"""Write an analysis copy of DOOM95.EXE that Ghidra can fully parse.

The Watcom linker left VirtualSize = 0 in every section header. Windows tolerates that,
but Ghidra then cannot map the import, resource and relocation directories into a
section ("Invalid file index"). This copy sets each VirtualSize to the section's
SizeOfRawData. The original file is never modified, and the copy is for analysis only.

Usage:  python tools/fix_pe_for_ghidra.py orig/DOOM95.EXE build/DOOM95_analysis.exe
"""
import struct
import sys


def main(src, dst):
    if src == dst:
        sys.exit("refusing to overwrite the input file")
    data = bytearray(open(src, "rb").read())
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        sys.exit("not a PE file")
    count = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    first = pe + 24 + opt_size
    for i in range(count):
        s = first + 40 * i
        name = data[s:s + 8].rstrip(b"\0").decode("ascii")
        vsize, rva, raw_size = struct.unpack_from("<III", data, s + 8)
        if vsize == 0 and raw_size:
            struct.pack_into("<I", data, s + 8, raw_size)
            print(f"{name:8s} RVA {rva:06X}: VirtualSize 0 -> {raw_size:X}")
    open(dst, "wb").write(data)
    print(f"wrote {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
