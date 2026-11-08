// SPDX-License-Identifier: GPL-2.0-only
// Doom95 decompilation - https://github.com/anteroul/doom95-decomp

// Stand-in for the old SysV <values.h> (m_bbox.h). doomtype.h already defines MAXINT,
// MININT and friends when LINUX is not defined, so take them from there.
#pragma once
#include "doomtype.h"
