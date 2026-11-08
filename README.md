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
include/compat/  shims so the linuxdoom code builds with MSVC (functional build only)
tools/        verify_orig.py  check orig/DOOM95.EXE
              split.py        cut the exe into per-function .bin files under build/split/
              progress.py     matched functions/bytes, overall and per module
              watcom_syms.py  regenerate symbols.csv from the exe's debug info
              fix_pe_for_ghidra.py, ghidra/ImportDoom95Symbols.java,
              ghidra/ApplyWatcomCallingConvention.java   Ghidra setup
CMakeLists.txt  functional MSVC build (see below)
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
   `config/symbols.csv`. Then run `tools/ghidra/ApplyWatcomCallingConvention.java` with the
   same CSV. Ghidra has no Watcom register convention, so without this step calls lose their
   arguments (`M_CheckParm()` instead of `M_CheckParm("-nomonsters")`). The script adds a
   `__watcall` prototype and applies it:
   - to the ~925 `Foo_` and `W?...` functions
   - `__stdcall` stays on the Windows callbacks
   - `__cdecl` goes on the C library varargs functions (`printf_`, ...)

   It then re-runs parameter detection, which takes a few minutes. A few C library signatures
   still need setting by hand, for example `int printf(char *, ...)`.
4. Keep id's source (github.com/id-Software/DOOM) next to you as a reference. It isn't vendored
   here; `src/game/` and `include/` start as copies of its linuxdoom-1.10 files (commit `a77dfb9`).

## Functional build

Alongside the matching work, `CMakeLists.txt` builds the current sources with MSVC into a
runnable `doom95.exe`. It checks that decompiled code actually works, and it gives the Windows
layer somewhere to grow. It is not byte-matching, and it is not the Watcom build.

Needs Visual Studio 2022 or 2026 with the C++ workload. Only a 32-bit build is supported,
because the engine keeps pointers in `int`s.

```
cmake --preset vs-win32
cmake --build --preset vs-win32-debug
set DOOMWADDIR=orig
build\cmake\Debug\doom95.exe -timedemo demo1
```

In Visual Studio, use **Open Folder** and pick the **x86 Debug** configuration from
`CMakePresets.json`. It builds into `out/build/x86-debug/`. VS's default x64 configuration
stops with "Build 32-bit".

- **What works:** all of startup. The IWAD demos play to the end under `-timedemo`, which
  exits with `timed N gametics in M realtics`. Reaching the end doesn't prove a demo stayed in
  sync; that can only be checked once video works.
- **Still stubs:** `src/win32/` has a console `main()` instead of WinMain, a real timer, and
  single-player networking only. There is no video, input or sound yet.
- **Finding WADs:** IWADs are looked up in `DOOMWADDIR`, and the first of doom2f, doom2,
  plutonia, tnt, doomu, doom, doom1 wins.
- **Crashes** print the call stack with file:line.
- `include/compat/doom95_compat.h` is force-included into every file. With the shim headers
  next to it, it lets the linuxdoom code build without edits.

Every change to a linuxdoom file in `src/game/` or `include/` carries a tag, so a diff
against id's source shows only deliberate changes:

- `DOOM95:` means the decompile shows Doom95 does this differently. Say what showed it.
  - `doomdef.h`: `VERSION` 110 → 109. `D_DoomMain` prints `v%i.%i` with 1, 9, and the 1.9
    IWAD demos play back.
- `DOOM95-SKELETON:` means a workaround for this build that Doom95 does not do.
  - `info.c`/`info.h`: a NULL terminator for `sprnames`. Doom95's table is exactly 138
    pointers. `R_InitSpriteDefs` only stops on the zero that `states[0]` happens to put after
    it, and MSVC's data layout doesn't give that.

Known warnings:

- `g_game.c:459`: an id bug. `gamemode` is compared with `GameMission_t` values, so the
  TNT/Plutonia sky check never matches. Check whether Doom95 has it too.
- `w_wad.c`: `O_BINARY` redefined to 0. `doom95.c` sets binary as the default file mode.

`src/game/` still uses linuxdoom's file split (`m_argv.c`, `f_wipe.c`, `p_saveg.c`, ...).
Doom95's modules merge some of these (see above), which still has to be done.

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
