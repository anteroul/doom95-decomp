"""Check that orig/DOOM95.EXE is the supported Doom95 v3.0 build.

Usage:  python tools/verify_orig.py
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doom95  # noqa: E402


def main():
    data = doom95.load_orig(check=False)
    got = hashlib.sha1(data).hexdigest()
    if got == doom95.expected_sha1():
        print(f"OK: orig/DOOM95.EXE is Doom95 v3.0 ({len(data):,} bytes, SHA-1 {got})")
        return 0
    print(f"MISMATCH: orig/DOOM95.EXE has SHA-1 {got}, expected {doom95.expected_sha1()}")
    print("Only the unmodified v3.0 executable (775,117 bytes) is supported.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
