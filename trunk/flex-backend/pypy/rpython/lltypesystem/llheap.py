# only for the LLInterpreter.  Don't use directly.

from pypy.rpython.lltypesystem.lltype import pyobjectptr, malloc, free
from pypy.rpython.lltypesystem.llmemory import raw_malloc, raw_free
from pypy.rpython.lltypesystem.llmemory import raw_memclear, raw_memcopy
from pypy.rpython.lltypesystem.llmemory import raw_malloc_usage
