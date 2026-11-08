// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp

// Force-included into every game file (see CMakeLists.txt) so that id's linuxdoom-1.10
// sources build with MSVC unchanged. Keeping src/game identical to upstream makes it easy
// to diff each file against DOOM95.EXE later and see only what Doom95 really changed.

#ifndef DOOM95_COMPAT_H
#define DOOM95_COMPAT_H

#ifndef _CRT_SECURE_NO_WARNINGS
#define _CRT_SECURE_NO_WARNINGS
#endif
#ifndef _CRT_NONSTDC_NO_DEPRECATE
#define _CRT_NONSTDC_NO_DEPRECATE
#endif

// Pull in the CRT declarations first, so the renames below only affect DOOM's own code.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>     // alloca
// Not <io.h>: see unistd.h.

// POSIX names the engine uses.
#define strcasecmp  _stricmp
#define strncasecmp _strnicmp

// w_wad.c defines its own strupr() and filelength(), which clash with the CRT's.
#define strupr     W_strupr
#define filelength W_filelength

// Note: w_wad.c defines O_BINARY as 0 under NORMALUNIX. doom95.c switches the CRT's default
// file mode to binary (_set_fmode) so WAD and savegame reads are not text-translated.

#endif
