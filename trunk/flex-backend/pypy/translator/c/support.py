from pypy.rpython.lltypesystem import lltype
from pypy.translator.gensupp import NameManager

#
# use __slots__ declarations for node classes etc
# possible to turn it off while refactoring, experimenting
#
USESLOTS = True

PyObjPtr = lltype.Ptr(lltype.PyObject)


class ErrorValue:
    def __init__(self, TYPE):
        self.TYPE = TYPE


#
# helpers
#
def cdecl(ctype, cname, is_thread_local=False):
    """
    Produce a C declaration from a 'type template' and an identifier.
    The type template must contain a '@' sign at the place where the
    name should be inserted, according to the strange C syntax rules.
    """
    # the (@) case is for functions, where if there is a plain (@) around
    # the function name, we don't need the very confusing parenthesis
    __thread = ""
    if is_thread_local:
        __thread = "__thread "
    return __thread + ctype.replace('(@)', '@').replace('@', cname).strip()

def forward_cdecl(ctype, cname, standalone, is_thread_local=False):
    __thread = ""
    if is_thread_local:
        __thread = "__thread "

    cdecl_str = __thread + cdecl(ctype, cname)
    if standalone:
        return 'extern ' + cdecl_str
    else:
        return cdecl_str
    
def somelettersfrom(s):
    upcase = [c for c in s if c.isupper()]
    if not upcase:
        upcase = [c for c in s.title() if c.isupper()]
    locase = [c for c in s if c.islower()]
    if locase and upcase:
        return ''.join(upcase).lower()
    else:
        return s[:2].lower()

def is_pointer_to_forward_ref(T):
    if not isinstance(T, lltype.Ptr):
        return False
    return isinstance(T.TO, lltype.ForwardReference)

def llvalue_from_constant(c):
    try:
        T = c.concretetype
    except AttributeError:
        T = PyObjPtr
    if T == PyObjPtr and not isinstance(c.value, lltype._ptr):
        return lltype.pyobjectptr(c.value)
    else:
        if T == lltype.Void:
            return None
        else:
            ACTUAL_TYPE = lltype.typeOf(c.value)
            # If the type is still uncomputed, we can't make this
            # check.  Something else will blow up instead, probably
            # very confusingly.
            if not is_pointer_to_forward_ref(ACTUAL_TYPE):
                assert ACTUAL_TYPE == T
            return c.value


class CNameManager(NameManager):
    def __init__(self, global_prefix='pypy_'):
        NameManager.__init__(self, global_prefix=global_prefix)
        # keywords cannot be reused.  This is the C99 draft's list.
        self.make_reserved_names('''
           auto      enum      restrict  unsigned
           break     extern    return    void
           case      float     short     volatile
           char      for       signed    while
           const     goto      sizeof    _Bool
           continue  if        static    _Complex
           default   inline    struct    _Imaginary
           do        int       switch
           double    long      typedef
           else      register  union
           ''')

def _char_repr(c):
    if c in '\\"': return '\\' + c
    if ' ' <= c < '\x7F': return c
    return '\\%03o' % ord(c)

def _line_repr(s):
    return ''.join([_char_repr(c) for c in s])


def c_string_constant(s):
    '''Returns a " "-delimited string literal for C.'''
    lines = []
    for i in range(0, len(s), 64):
        lines.append('"%s"' % _line_repr(s[i:i+64]))
    return '\n'.join(lines)


def c_char_array_constant(s):
    '''Returns an initializer for a constant char[N] array,
    where N is exactly len(s).  This is either a " "-delimited
    string or a { }-delimited array of small integers.
    '''
    if s.endswith('\x00') and len(s) < 1024:
        # C++ is stricted than C: we can only use a " " literal
        # if the last character is NULL, because such a literal
        # always has an extra implicit NULL terminator.
        return c_string_constant(s[:-1])
    else:
        lines = []
        for i in range(0, len(s), 20):
            lines.append(','.join([str(ord(c)) for c in s[i:i+20]]))
        if len(lines) > 1:
            return '{\n%s}' % ',\n'.join(lines)
        else:
            return '{%s}' % ', '.join(lines)


##def gen_assignments(assignments):
##    # Generate a sequence of assignments that is possibly reordered
##    # to avoid clashes -- i.e. do the equivalent of a tuple assignment,
##    # reading all sources first, writing all targets next, but optimized

##    allsources = []
##    src2dest = {}
##    types = {}
##    for typename, dest, src in assignments:
##        if src != dest:   # ignore 'v=v;'
##            allsources.append(src)
##            src2dest.setdefault(src, []).append(dest)
##            types[dest] = typename

##    for starting in allsources:
##        # starting from some starting variable, follow a chain of assignments
##        #     'vn=vn-1; ...; v3=v2; v2=v1; v1=starting;'
##        v = starting
##        srcchain = []
##        while src2dest.get(v):
##            srcchain.append(v)
##            v = src2dest[v].pop(0)
##            if v == starting:
##                break    # loop
##        if not srcchain:
##            continue   # already done in a previous chain
##        srcchain.reverse()   # ['vn-1', ..., 'v2', 'v1', 'starting']
##        code = []
##        for pair in zip([v] + srcchain[:-1], srcchain):
##            code.append('%s = %s;' % pair)
##        if v == starting:
##            # assignment loop 'starting=vn-1; ...; v2=v1; v1=starting;'
##            typename = types[starting]
##            tmpdecl = cdecl(typename, 'tmp')
##            code.insert(0, '{ %s = %s;' % (tmpdecl, starting))
##            code[-1] = '%s = tmp; }' % (srcchain[-2],)
##        yield ' '.join(code)

def gen_assignments(assignments):
    # Generate a sequence of assignments that is possibly reordered
    # to avoid clashes -- i.e. do the equivalent of a tuple assignment,
    # reading all sources first, writing all targets next, but optimized

    srccount = {}
    dest2src = {}
    for typename, dest, src in assignments:
        if src != dest:   # ignore 'v=v;'
            srccount[src] = srccount.get(src, 0) + 1
            dest2src[dest] = src, typename

    while dest2src:
        progress = False
        for dst in dest2src.keys():
            if dst not in srccount:
                src, typename = dest2src.pop(dst)
                yield '%s = %s;' % (dst, src)
                srccount[src] -= 1
                if not srccount[src]:
                    del srccount[src]
                progress = True
        if not progress:
            # we are left with only pure disjoint cycles; break them
            while dest2src:
                dst, (src, typename) = dest2src.popitem()
                assert srccount[dst] == 1
                startingpoint = dst
                tmpdecl = cdecl(typename, 'tmp')
                code = ['{ %s = %s;' % (tmpdecl, dst)]
                while src is not startingpoint:
                    code.append('%s = %s;' % (dst, src))
                    dst = src
                    src, typename = dest2src.pop(dst)
                    assert srccount[dst] == 1
                code.append('%s = tmp; }' % (dst,))
                yield ' '.join(code)

# logging

import py
from pypy.tool.ansi_print import ansi_log
log = py.log.Producer("c")
py.log.setconsumer("c", ansi_log)
