# SPDX-License-Identifier: GPL-2.0-only
# Doom95 decompilation - https://github.com/anteroul/doom95-decomp
#
# Functional (non-matching) MSVC build: the game code in src/game plus the Windows layer in
# src/win32, to check that decompiled code runs. It is not the matching Watcom build.
#   cmake -S . -B build/cmake -A Win32
#   cmake --build build/cmake --config Debug

cmake_minimum_required(VERSION 3.20)
project(doom95 C)

# The engine stores pointers in ints (m_misc.c defaults, p_saveg.c, info.c), like the
# original 32-bit DOOM95.EXE, so only a 32-bit build is supported.
if(NOT CMAKE_SIZEOF_VOID_P EQUAL 4)
    message(FATAL_ERROR "Build 32-bit. In Visual Studio pick the 'x86 Debug' configuration "
        "(CMakePresets.json; if it isn't listed, close VS, delete .vs/ and out/, reopen). "
        "From the command line: cmake --preset vs-win32")
endif()

# Game code: id's linuxdoom-1.10 files. Changes are tagged DOOM95: / DOOM95-SKELETON: (README).
set(ENGINE_SOURCES
    am_map.c d_items.c d_main.c d_net.c doomdef.c doomstat.c dstrings.c
    f_finale.c f_wipe.c g_game.c hu_lib.c hu_stuff.c info.c
    m_argv.c m_bbox.c m_cheat.c m_fixed.c m_menu.c m_misc.c m_random.c m_swap.c
    p_ceilng.c p_doors.c p_enemy.c p_floor.c p_inter.c p_lights.c p_map.c p_maputl.c
    p_mobj.c p_plats.c p_pspr.c p_saveg.c p_setup.c p_sight.c p_spec.c p_switch.c
    p_telept.c p_tick.c p_user.c
    r_bsp.c r_data.c r_draw.c r_main.c r_plane.c r_segs.c r_sky.c r_things.c
    s_sound.c sounds.c st_lib.c st_stuff.c tables.c v_video.c w_wad.c wi_stuff.c z_zone.c
)
list(TRANSFORM ENGINE_SOURCES PREPEND src/game/)

# The Windows 95 layer, named after DOOM95.EXE's own modules (still stubs).
set(WIN95_SOURCES
    src/win32/doom95.c
    src/win32/i_w95gdk.c
    src/win32/i_sound.c
)

add_executable(doom95 ${ENGINE_SOURCES} ${WIN95_SOURCES})

target_include_directories(doom95 PRIVATE include/compat include)
target_link_libraries(doom95 PRIVATE dbghelp)   # crash handler in doom95.c
target_compile_definitions(doom95 PRIVATE NORMALUNIX _CRT_SECURE_NO_WARNINGS _CRT_NONSTDC_NO_DEPRECATE)

if(MSVC)
    target_compile_options(doom95 PRIVATE
        /FI${CMAKE_CURRENT_SOURCE_DIR}/include/compat/doom95_compat.h
        /W3
        # 1993 code: implicit int casts, pointer/int conversions, unused locals.
        /wd4244 /wd4018 /wd4305 /wd4311 /wd4312 /wd4133 /wd4047 /wd4024 /wd4022
        # info.c's state table stores action functions through actionf_t; -angle on angle_t.
        /wd4113 /wd4146
    )
endif()

# Debug from orig/, where your game files live (set DOOMWADDIR to use another folder).
set_target_properties(doom95 PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/orig)
