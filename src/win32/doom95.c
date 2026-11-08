// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp

// Program entry point.
//
// DOOM95.EXE: doom95.cpp (WinMain, window class, DirectDraw setup, message loop, 107 symbols).
// Skeleton: a console main() so startup text and I_Error messages are visible while the
// Windows layer is being rebuilt. Replace with WinMain once the window exists.

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dbghelp.h>
#undef MAXCHAR
#undef MAXSHORT
#undef MAXINT
#undef MAXLONG
#undef MINCHAR
#undef MINSHORT
#undef MININT
#undef MINLONG

#include "doomdef.h"
#include "m_argv.h"
#include "d_main.h"

// Development aid, not part of DOOM95: on a crash, print the faulting function and the
// call stack (file:line from the PDB) instead of exiting silently.
static LONG WINAPI CrashHandler(EXCEPTION_POINTERS *ep)
{
    HANDLE process = GetCurrentProcess();
    HANDLE thread = GetCurrentThread();
    CONTEXT ctx = *ep->ContextRecord;
    STACKFRAME64 frame = {0};
    char buf[sizeof(SYMBOL_INFO) + 256];
    SYMBOL_INFO *sym = (SYMBOL_INFO *)buf;
    IMAGEHLP_LINE64 line = {sizeof(line)};
    DWORD64 disp;
    DWORD ldisp;
    int depth;

    fprintf(stderr, "\nCrash: exception 0x%08lX at %p\n",
            ep->ExceptionRecord->ExceptionCode, ep->ExceptionRecord->ExceptionAddress);

    SymSetOptions(SYMOPT_LOAD_LINES | SYMOPT_UNDNAME);
    SymInitialize(process, NULL, TRUE);
    frame.AddrPC.Offset = ctx.Eip;    frame.AddrPC.Mode = AddrModeFlat;
    frame.AddrFrame.Offset = ctx.Ebp; frame.AddrFrame.Mode = AddrModeFlat;
    frame.AddrStack.Offset = ctx.Esp; frame.AddrStack.Mode = AddrModeFlat;

    for (depth = 0; depth < 32; depth++)
    {
        if (!StackWalk64(IMAGE_FILE_MACHINE_I386, process, thread, &frame, &ctx, NULL,
                         SymFunctionTableAccess64, SymGetModuleBase64, NULL) || !frame.AddrPC.Offset)
            break;
        sym->SizeOfStruct = sizeof(SYMBOL_INFO);
        sym->MaxNameLen = 255;
        if (SymFromAddr(process, frame.AddrPC.Offset, &disp, sym))
            fprintf(stderr, "  %s", sym->Name);
        else
            fprintf(stderr, "  %08llX", frame.AddrPC.Offset);
        if (SymGetLineFromAddr64(process, frame.AddrPC.Offset, &ldisp, &line))
            fprintf(stderr, "  %s:%lu", line.FileName, line.LineNumber);
        fprintf(stderr, "\n");
    }
    fflush(stderr);
    return EXCEPTION_EXECUTE_HANDLER;
}

int main(int argc, char **argv)
{
    SetUnhandledExceptionFilter(CrashHandler);

    // w_wad.c opens WADs without O_BINARY; make binary the CRT default instead.
    _set_fmode(_O_BINARY);

    // linuxdoom's IdentifyVersion() requires $HOME for its .doomrc. DOOM95 uses default.cfg in
    // the game folder instead; until IdentifyVersion is replaced, point HOME at the current dir.
    if (!getenv("HOME"))
        _putenv("HOME=.");

    myargc = argc;
    myargv = argv;

    D_DoomMain();   // never returns: ends in D_DoomLoop, I_Quit or I_Error
    return 0;
}
