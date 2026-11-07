# Doom95 decompilation

A work-in-progress decompilation of **Doom95 v3.0** (`DOOM95.EXE`, 1996), the Windows 95 port of
DOOM. The goal is C/C++ source that compiles back to the original executable.

This repository contains **no game files**. You need your own copy of `DOOM95.EXE` v3.0.

## Status

0 of 821 functions matched (207,099 bytes of Doom95 code in 55 modules; the 298 functions of
the Watcom C runtime are not counted). The compiler question is still open. See [Next step](#next-step).

```
python tools/progress.py
```

## What we start from

`DOOM95.EXE` still carries its Watcom debug info. That gives every function's original name,
address and source file, so the decomp starts with a complete map
([config/symbols.csv](config/symbols.csv)): 2,526 symbols from 58 source modules.

- **Game code** (`src/game/`): 46 of the modules have a counterpart in id Software's released
  linuxdoom 1.10 source (GPL). Doom95 follows the older DOS file layout, so some code moved:
  cheats and the screen wipe are in `dutils.c`, `M_Random` is in `m_misc.c`, savegames are in `p_tick.c`.
- **Windows layer** (`src/win32/`): Microsoft's port, with no public source. `doom95.cpp`,
  `i_w95gdk.cpp`, `i_win32.cpp`, `i_launch.cpp`, `i_dinput.c`, `i_vkey.c`, `i_winmus.c`,
  `i_config.c`, `i_xband.cpp`, `dither.c`, `wadread.c`.

Built with **WATCOM C/C++32**: the runtime says 1988-1995, so probably Watcom 10.0 or 10.5.
Functions named `Foo_` use Watcom's register calling convention (EAX, EDX, EBX, ECX).

## Layout

```
config/       doom95.sha1   supported executable
              symbols.csv   all original symbols (address, type, name, source file)
              matched.txt   functions that compile to the original bytes
src/game/     modules based on the linuxdoom source
src/win32/    Microsoft's Windows layer
include/      headers
tools/        verify_orig.py  check orig/DOOM95.EXE
              split.py        cut the exe into per-function .bin files under build/split/
              progress.py     matched functions/bytes, overall and per module
              watcom_syms.py  regenerate symbols.csv from the exe's debug info
              fix_pe_for_ghidra.py, ghidra/ImportDoom95Symbols.java   Ghidra setup
orig/         your DOOM95.EXE (git-ignored)
build/        generated files (git-ignored)
```

## Getting started

1. Copy your `DOOM95.EXE` into `orig/` and check it:
   ```
   python tools/verify_orig.py
   ```
2. Split it into per-function targets:
   ```
   python tools/split.py
   ```
3. For Ghidra: `python tools/fix_pe_for_ghidra.py orig/DOOM95.EXE build/DOOM95_analysis.exe`,
   import `build/DOOM95_analysis.exe`, then run `tools/ghidra/ImportDoom95Symbols.java` with
   `config/symbols.csv`.
4. Keep id's source (github.com/id-Software/DOOM) next to you as a reference. It isn't vendored here.

## Next step

Find out whether a byte-identical (matching) decomp is possible:

1. Install Open Watcom 2.0.
2. Compile small, unchanged linuxdoom functions such as `M_ClearBox` and `W_GetNumForName` with
   register calling (`-4r`/`-5r`) and a range of `-o...` optimisation settings.
3. Compare against `build/split/<module>/<function>.bin`.

If Open Watcom can match, aim for a matching decomp and add a `diff.py` that compiles a function
and compares it with relocations masked. If not, the original Watcom 10.x compiler may be needed,
or the project becomes a functional (non-matching) decomp.

## License

**GPL-2.0** ([LICENSE](LICENSE), SPDX `GPL-2.0-only`), the same license id Software used for its
DOOM source release (github.com/id-Software/DOOM). Most of `src/game/` is derived from that code, so
the GPL applies to the whole project. The tools are covered by it too.

Start new source files with:

```c
// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp
// Based on DOOM source code, Copyright (C) 1993-1996 id Software, Inc.
```

For files written from scratch, such as `src/win32/` and `tools/`, the last line can be left out.

## Legal

DOOM is a trademark of id Software. Doom95 was published by id Software and Microsoft. This
project is not affiliated with or endorsed by either. The repository contains no original game
files: never commit `DOOM95.EXE`, its DLLs, WAD files or DirectX files.
