// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp

// Stand-in for the POSIX header that d_main.c, m_menu.c, m_misc.c and w_wad.c include.
// Kept out of the force-included doom95_compat.h on purpose: <io.h> declares open() and
// close(), which collide with the door-type enum members of the same names in p_spec.h.
#pragma once

// The CRT's own filelength() must keep its name; doom95_compat.h renames DOOM's to W_filelength.
#undef filelength
#include <io.h>         // open, read, lseek, close, access
#define filelength W_filelength
#include <direct.h>     // _mkdir
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

#define mkdir(path, mode) _mkdir(path)
#ifndef R_OK
#define R_OK 4
#endif
