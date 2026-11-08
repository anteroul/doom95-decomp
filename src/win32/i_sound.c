// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp
// Based on DOOM source code, Copyright (C) 1993-1996 id Software, Inc.

// Sound effects and music.
//
// DOOM95.EXE: i_sound.c (DirectSound, 37 symbols) and i_winmus.c (MIDI music, 12 symbols).
// Skeleton: silent. Every call succeeds and nothing plays.

#include <stdio.h>

#include "doomdef.h"
#include "i_sound.h"
#include "w_wad.h"
#include "z_zone.h"

// linuxdoom's "UNIX hack" globals: m_misc.c saves sndserver to the config file (SNDSERV is
// defined in doomdef.h). Remove these along with SNDSERV once m_misc.c follows DOOM95.
FILE *sndserver = 0;
char *sndserver_filename = "";

void I_InitSound(void)
{
    int i;

    // s_sound.c expects every effect to be cached here (S_sfx[].data), as linuxdoom's driver
    // did. Sounds missing from the IWAD (shareware) fall back to dspistol, like linuxdoom.
    for (i = 1; i < NUMSFX; i++)
    {
        if (!S_sfx[i].link)
        {
            char name[9];
            int lump;

            sprintf(name, "ds%s", S_sfx[i].name);
            lump = W_CheckNumForName(name);
            if (lump == -1)
                lump = W_GetNumForName("dspistol");
            S_sfx[i].data = W_CacheLumpNum(lump, PU_STATIC);
        }
        else
            S_sfx[i].data = S_sfx[i].link->data;
    }
}

void I_UpdateSound(void)
{
}

void I_SubmitSound(void)
{
}

void I_ShutdownSound(void)
{
}

void I_SetChannels(void)
{
}

void I_SetSfxVolume(int volume)
{
    (void)volume;
}

int I_GetSfxLumpNum(sfxinfo_t *sfx)
{
    char namebuf[9];
    sprintf(namebuf, "ds%s", sfx->name);
    return W_GetNumForName(namebuf);
}

int I_StartSound(int id, int vol, int sep, int pitch, int priority)
{
    (void)vol; (void)sep; (void)pitch; (void)priority;
    return id;
}

void I_StopSound(int handle)
{
    (void)handle;
}

int I_SoundIsPlaying(int handle)
{
    (void)handle;
    return 0;
}

void I_UpdateSoundParams(int handle, int vol, int sep, int pitch)
{
    (void)handle; (void)vol; (void)sep; (void)pitch;
}

void I_InitMusic(void)
{
}

void I_ShutdownMusic(void)
{
}

void I_SetMusicVolume(int volume)
{
    (void)volume;
}

void I_PauseSong(int handle)
{
    (void)handle;
}

void I_ResumeSong(int handle)
{
    (void)handle;
}

int I_RegisterSong(void *data)
{
    (void)data;
    return 1;
}

void I_PlaySong(int handle, int looping)
{
    (void)handle; (void)looping;
}

void I_StopSong(int handle)
{
    (void)handle;
}

void I_UnRegisterSong(int handle)
{
    (void)handle;
}
