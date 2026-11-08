// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp
// Based on DOOM source code, Copyright (C) 1993-1996 id Software, Inc.

// System, timer, video, input and network layer.
//
// DOOM95.EXE: i_w95gdk.cpp (158 symbols) holds the I_* functions built on the Windows 95
// Game SDK (DirectDraw, DirectInput, DirectPlay). Skeleton: just enough to run the engine
// headless. A real timer and single-player networking; video and input do nothing yet.

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
// doomtype.h defines these too (same values); let DOOM's definitions win.
#undef MAXCHAR
#undef MAXSHORT
#undef MAXINT
#undef MAXLONG
#undef MINCHAR
#undef MINSHORT
#undef MININT
#undef MINLONG

#include "doomdef.h"
#include "doomstat.h"
#include "d_main.h"
#include "d_net.h"
#include "g_game.h"
#include "m_argv.h"
#include "m_misc.h"
#include "i_net.h"
#include "i_sound.h"
#include "i_system.h"
#include "i_video.h"
#include "v_video.h"

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

int mb_used = 6;    // zone heap size in MB (linuxdoom default; check DOOM95's I_ZoneBase)

static ticcmd_t emptycmd;

void I_Init(void)
{
    I_InitSound();
}

byte *I_ZoneBase(int *size)
{
    *size = mb_used * 1024 * 1024;
    return (byte *)malloc(*size);
}

int I_GetTime(void)
{
    static LARGE_INTEGER freq, base;
    LARGE_INTEGER now;

    if (!freq.QuadPart)
    {
        QueryPerformanceFrequency(&freq);
        QueryPerformanceCounter(&base);
    }
    QueryPerformanceCounter(&now);
    return (int)((now.QuadPart - base.QuadPart) * TICRATE / freq.QuadPart);
}

void I_StartFrame(void)
{
}

void I_StartTic(void)
{
    // TODO: pump the Windows message queue and post keyboard/mouse events (i_dinput.c).
}

ticcmd_t *I_BaseTiccmd(void)
{
    return &emptycmd;
}

void I_Tactile(int on, int off, int total)
{
    (void)on; (void)off; (void)total;
}

byte *I_AllocLow(int length)
{
    byte *mem = (byte *)malloc(length);
    memset(mem, 0, length);
    return mem;
}

void I_Quit(void)
{
    D_QuitNetGame();
    I_ShutdownSound();
    I_ShutdownMusic();
    M_SaveDefaults();
    I_ShutdownGraphics();
    exit(0);
}

void I_Error(char *error, ...)
{
    va_list argptr;

    va_start(argptr, error);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, error, argptr);
    fprintf(stderr, "\n");
    va_end(argptr);
    fflush(stderr);

    if (demorecording)
        G_CheckDemoStatus();

    D_QuitNetGame();
    I_ShutdownGraphics();
    exit(-1);
}

// ---------------------------------------------------------------------------
// Video
// ---------------------------------------------------------------------------

void I_InitGraphics(void)
{
    // TODO: create the window and DirectDraw surface (doom95.cpp CreateWindowMode/
    // CreateFullscreenMode). The engine already draws into screens[0], 320x200 8-bit.
}

void I_ShutdownGraphics(void)
{
}

void I_SetPalette(byte *palette)
{
    (void)palette;
}

void I_UpdateNoBlit(void)
{
}

void I_FinishUpdate(void)
{
    // TODO: blit screens[0] to the DirectDraw surface.
}

void I_WaitVBL(int count)
{
    Sleep(count * 1000 / 70);
}

void I_ReadScreen(byte *scr)
{
    memcpy(scr, screens[0], SCREENWIDTH * SCREENHEIGHT);
}

void I_BeginRead(void)
{
}

void I_EndRead(void)
{
}

// ---------------------------------------------------------------------------
// Network: single player only. Multiplayer in DOOM95 goes through DOOMIPX/DOOMSER/DOOMMDM.DLL
// and DirectPlay; see d_net.c and i_xband.cpp in the symbol list.
// ---------------------------------------------------------------------------

void I_InitNetwork(void)
{
    int i;

    doomcom = malloc(sizeof(*doomcom));
    memset(doomcom, 0, sizeof(*doomcom));

    i = M_CheckParm("-dup");
    if (i && i < myargc - 1)
    {
        doomcom->ticdup = myargv[i + 1][0] - '0';
        if (doomcom->ticdup < 1)
            doomcom->ticdup = 1;
        if (doomcom->ticdup > 9)
            doomcom->ticdup = 9;
    }
    else
        doomcom->ticdup = 1;

    doomcom->extratics = M_CheckParm("-extratic") ? 1 : 0;

    if (M_CheckParm("-net"))
        I_Error("Network play is not implemented yet");

    netgame = false;
    doomcom->id = DOOMCOM_ID;
    doomcom->numplayers = doomcom->numnodes = 1;
    doomcom->deathmatch = false;
    doomcom->consoleplayer = 0;
}

void I_NetCmd(void)
{
    I_Error("I_NetCmd: network play is not implemented yet");
}
