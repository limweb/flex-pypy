
#include <stdlib.h>
#include <limits.h>
#include <assert.h>
#include <math.h>

#ifndef PYPY_NOT_MAIN_FILE
#ifdef AVR
   #ifndef NO_OBMALLOC
     #define NO_OBMALLOC
   #endif
#endif
#ifdef NO_OBMALLOC
void *PyObject_Malloc(size_t n) { return malloc(n); }
void *PyObject_Realloc(void *p, size_t n) { return realloc(p, n); }
void PyObject_Free(void *p) { if (p) { *((int*)p) = 0xDDDDDDDD; } free(p); }
#else
#  ifndef WITH_PYMALLOC
#    define WITH_PYMALLOC
#  endif
#  include "obmalloc.c"
#endif

#endif