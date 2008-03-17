# implementation of marshalling by multimethods

"""
The idea is to have an effective but flexible
way to implement marshalling for the native types.

The marshal_w operation is called with an object,
a callback and a state variable.
"""

from pypy.interpreter.error import OperationError
from pypy.objspace.std.register_all import register_all
from pypy.rlib.rarithmetic import LONG_BIT
from pypy.objspace.std.inttype import wrapint
from pypy.objspace.std.floatobject import repr__Float as repr_float
from pypy.objspace.std.longobject import SHIFT as long_bits
from pypy.objspace.std.objspace import StdObjSpace
from pypy.interpreter.special import Ellipsis
from pypy.interpreter.pycode import PyCode
from pypy.interpreter import gateway

from pypy.objspace.std.boolobject    import W_BoolObject
from pypy.objspace.std.complexobject import W_ComplexObject
from pypy.objspace.std.intobject     import W_IntObject
from pypy.objspace.std.floatobject   import W_FloatObject
from pypy.objspace.std.tupleobject   import W_TupleObject
from pypy.objspace.std.listobject    import W_ListObject
from pypy.objspace.std.dictobject    import W_DictObject
from pypy.objspace.std.dictmultiobject    import W_DictMultiObject
from pypy.objspace.std.stringobject  import W_StringObject
from pypy.objspace.std.ropeobject    import W_RopeObject
from pypy.objspace.std.typeobject    import W_TypeObject
from pypy.objspace.std.longobject    import W_LongObject
from pypy.objspace.std.noneobject    import W_NoneObject
from pypy.objspace.std.unicodeobject import W_UnicodeObject

import longobject, dictobject

from pypy.module.marshal.interp_marshal import register

TYPE_NULL      = '0'
TYPE_NONE      = 'N'
TYPE_FALSE     = 'F'
TYPE_TRUE      = 'T'
TYPE_STOPITER  = 'S'
TYPE_ELLIPSIS  = '.'
TYPE_INT       = 'i'
TYPE_INT64     = 'I'
TYPE_FLOAT     = 'f'
TYPE_BINARY_FLOAT = 'g'
TYPE_COMPLEX   = 'x'
TYPE_BINARY_COMPLEX = 'y'
TYPE_LONG      = 'l'
TYPE_STRING    = 's'
TYPE_INTERNED  = 't'
TYPE_STRINGREF = 'R'
TYPE_TUPLE     = '('
TYPE_LIST      = '['
TYPE_DICT      = '{'
TYPE_CODE      = 'c'
TYPE_UNICODE   = 'u'
TYPE_UNKNOWN   = '?'
TYPE_SET       = '<'
TYPE_FROZENSET = '>'

"""
simple approach:
a call to marshal_w has the following semantics:
marshal_w receives a marshaller object which contains
state and several methods.


atomic types including typecode:

atom(tc)                    puts single typecode
atom_int(tc, int)           puts code and int
atom_int64(tc, int64)       puts code and int64
atom_str(tc, str)           puts code, len and string
atom_strlist(tc, strlist)   puts code, len and list of strings

building blocks for compound types:

start(typecode)             sets the type character
put(s)                      puts a string with fixed length
put_short(int)              puts a short integer
put_int(int)                puts an integer
put_pascal(s)               puts a short string
put_w_obj(w_obj)            puts a wrapped object
put_list_w(list_w, lng)     puts a list of lng wrapped objects

"""

handled_by_any = []

def raise_exception(space, msg):
    raise OperationError(space.w_ValueError, space.wrap(msg))

def marshal_w__None(space, w_none, m):
    m.atom(TYPE_NONE)

def unmarshal_None(space, u, tc):
    return space.w_None
register(TYPE_NONE, unmarshal_None)

def marshal_w__Bool(space, w_bool, m):
    if w_bool.boolval:
        m.atom(TYPE_TRUE)
    else:
        m.atom(TYPE_FALSE)

def unmarshal_Bool(space, u, tc):
    if tc == TYPE_TRUE:
        return space.w_True
    else:
        return space.w_False
register(TYPE_TRUE + TYPE_FALSE, unmarshal_Bool)

def marshal_w__Type(space, w_type, m):
    if not space.is_w(w_type, space.w_StopIteration):
        raise_exception(space, "unmarshallable object")
    m.atom(TYPE_STOPITER)

def unmarshal_Type(space, u, tc):
    return space.w_StopIteration
register(TYPE_STOPITER, unmarshal_Type)

# not directly supported:
def marshal_w_Ellipsis(space, w_ellipsis, m):
    m.atom(TYPE_ELLIPSIS)

StdObjSpace.MM.marshal_w.register(marshal_w_Ellipsis, Ellipsis)

def unmarshal_Ellipsis(space, u, tc):
    return space.w_Ellipsis
register(TYPE_ELLIPSIS, unmarshal_Ellipsis)

def marshal_w__Int(space, w_int, m):
    if LONG_BIT == 32:
        m.atom_int(TYPE_INT, w_int.intval)
    else:
        y = w_int.intval >> 31
        if y and y != -1:
            m.atom_int64(TYPE_INT64, w_int.intval)
        else:
            m.atom_int(TYPE_INT, w_int.intval)

def unmarshal_Int(space, u, tc):
    return wrapint(space, u.get_int())
register(TYPE_INT, unmarshal_Int)

def unmarshal_Int64(space, u, tc):
    if LONG_BIT >= 64:
        lo = u.get_int() & (2**32-1)
        hi = u.get_int()
        return wrapint(space, (hi << 32) | lo)
    else:
        # fall back to a long
        # XXX at some point, we need to extend longobject
        # by _PyLong_FromByteArray and _PyLong_AsByteArray.
        # I will do that when implementing cPickle.
        # for now, this rare case is solved the simple way.
        lshift = longobject.lshift__Long_Long
        longor = longobject.or__Long_Long
        lo1 = space.newlong(u.get_short() & 0xffff)
        lo2 = space.newlong(u.get_short() & 0xffff)
        res = space.newlong(u.get_int())
        nbits = space.newlong(16)
        res = lshift(space, res, nbits)
        res = longor(space, res, lo2)
        res = lshift(space, res, nbits)
        res = longor(space, res, lo1)
        return res
register(TYPE_INT64, unmarshal_Int64)

# support for marshal version 2:
# we call back into the struct module.
# XXX struct should become interp-level.
# XXX we also should have an rtyper operation
# that allows to typecast between double and char{8}

app = gateway.applevel(r'''
    def float_to_str(fl):
        import struct
        return struct.pack('<d', fl)

    def str_to_float(s):
        import struct
        return struct.unpack('<d', s)[0]
''')

float_to_str = app.interphook('float_to_str')
str_to_float = app.interphook('str_to_float')

def marshal_w__Float(space, w_float, m):
    if m.version > 1:
        m.start(TYPE_BINARY_FLOAT)
        m.put(space.str_w(float_to_str(space, w_float)))
    else:
        m.start(TYPE_FLOAT)
        m.put_pascal(space.str_w(repr_float(space, w_float)))

def unmarshal_Float(space, u, tc):
    if tc == TYPE_BINARY_FLOAT:
        w_ret = str_to_float(space, space.wrap(u.get(8)))
        return W_FloatObject(space.float_w(w_ret))
    else:
        return space.call_function(space.builtin.get('float'),
                                 space.wrap(u.get_pascal()))
register(TYPE_FLOAT + TYPE_BINARY_FLOAT, unmarshal_Float)

def marshal_w__Complex(space, w_complex, m):
    # XXX a bit too wrap-happy
    w_real = space.wrap(w_complex.realval)
    w_imag = space.wrap(w_complex.imagval)
    if m.version > 1:
        m.start(TYPE_BINARY_COMPLEX)
        m.put(space.str_w(float_to_str(space, w_real)))
        m.put(space.str_w(float_to_str(space, w_imag)))
    else:
        m.start(TYPE_COMPLEX)
        m.put_pascal(space.str_w(repr_float(space, w_real)))
        m.put_pascal(space.str_w(repr_float(space, w_imag)))

def unmarshal_Complex(space, u, tc):
    if tc == TYPE_BINARY_COMPLEX:
        w_real = str_to_float(space, space.wrap(u.get(8)))
        w_imag = str_to_float(space, space.wrap(u.get(8)))
    else:
        w_real = space.call_function(space.builtin.get('float'),
                                     space.wrap(u.get_pascal()))
        w_imag = space.call_function(space.builtin.get('float'),
                                     space.wrap(u.get_pascal()))
    w_t = space.builtin.get('complex')
    return space.call_function(w_t, w_real, w_imag)
register(TYPE_COMPLEX + TYPE_BINARY_COMPLEX, unmarshal_Complex)

def marshal_w__Long(space, w_long, m):
    assert long_bits == 15, """if long_bits is not 15,
    we need to write much more general code for marshal
    that breaks things into pieces, or invent a new
    typecode and have our own magic number for pickling"""

    m.start(TYPE_LONG)
    # XXX access internals
    lng = len(w_long.num.digits)
    if w_long.num.sign < 0:
        m.put_int(-lng)
    else:
        m.put_int(lng)
    for digit in w_long.num.digits:
        m.put_short(digit)

def unmarshal_Long(space, u, tc):
    from pypy.rlib import rbigint
    lng = u.get_int()
    if lng < 0:
        sign = -1
        lng = -lng
    elif lng > 0:
        sign = 1
    else:
        sign = 0
    digits = [0] * lng
    i = 0
    while i < lng:
        digit = u.get_short()
        if digit < 0:
            raise_exception(space, 'bad marshal data')
        digits[i] = digit
        i += 1
    # XXX poking at internals
    w_long = W_LongObject(rbigint.rbigint(digits, sign))
    w_long.num._normalize()
    return w_long
register(TYPE_LONG, unmarshal_Long)

# XXX currently, intern() is at applevel,
# and there is no interface to get at the
# internal table.
# Move intern to interplevel and add a flag
# to strings.
def PySTRING_CHECK_INTERNED(w_str):
    return False

def marshal_w__String(space, w_str, m):
    # using the fastest possible access method here
    # that does not touch the internal representation,
    # which might change (array of bytes?)
    s = w_str.unwrap(space)
    if m.version >= 1 and PySTRING_CHECK_INTERNED(w_str):
        # we use a native rtyper stringdict for speed
        idx = m.stringtable.get(s, -1)
        if idx >= 0:
            m.atom_int(TYPE_STRINGREF, idx)
        else:
            idx = len(m.stringtable)
            m.stringtable[s] = idx
            m.atom_str(TYPE_INTERNED, s)
    else:
        m.atom_str(TYPE_STRING, s)

marshal_w__Rope = marshal_w__String

def unmarshal_String(space, u, tc):
    return space.wrap(u.get_str())
register(TYPE_STRING, unmarshal_String)

def unmarshal_interned(space, u, tc):
    w_ret = space.wrap(u.get_str())
    u.stringtable_w.append(w_ret)
    w_intern = space.builtin.get('intern')
    space.call_function(w_intern, w_ret)
    return w_ret
register(TYPE_INTERNED, unmarshal_interned)

def unmarshal_stringref(space, u, tc):
    idx = u.get_int()
    try:
        return u.stringtable_w[idx]
    except IndexError:
        raise_exception(space, 'bad marshal data')
register(TYPE_STRINGREF, unmarshal_stringref)

def marshal_w__Tuple(space, w_tuple, m):
    m.start(TYPE_TUPLE)
    items = w_tuple.wrappeditems
    m.put_list_w(items, len(items))

def unmarshal_Tuple(space, u, tc):
    items_w = u.get_list_w()
    return space.newtuple(items_w)
register(TYPE_TUPLE, unmarshal_Tuple)

def marshal_w__List(space, w_list, m):
    m.start(TYPE_LIST)
    items = w_list.wrappeditems
    m.put_list_w(items, len(items))

def unmarshal_List(space, u, tc):
    items_w = u.get_list_w()
    return space.newlist(items_w)

def finish_List(space, items_w, typecode):
    return space.newlist(items_w)
register(TYPE_LIST, unmarshal_List)

def marshal_w__Dict(space, w_dict, m):
    m.start(TYPE_DICT)
    for w_key, w_value in w_dict.content.iteritems():
        m.put_w_obj(w_key)
        m.put_w_obj(w_value)
    m.atom(TYPE_NULL)

def marshal_w__DictMulti(space, w_dict, m):
    m.start(TYPE_DICT)
    for w_tuple in w_dict.implementation.items():
        w_key, w_value = space.unpacktuple(w_tuple, 2)
        m.put_w_obj(w_key)
        m.put_w_obj(w_value)
    m.atom(TYPE_NULL)

def unmarshal_Dict(space, u, tc):
    # since primitive lists are not optimized and we don't know
    # the dict size in advance, use the dict's setitem instead
    # of building a list of tuples.
    w_dic = space.newdict()
    while 1:
        w_key = u.get_w_obj(True)
        if w_key is None:
            break
        w_value = u.get_w_obj(False)
        space.setitem(w_dic, w_key, w_value)
    return w_dic
register(TYPE_DICT, unmarshal_Dict)

def unmarshal_NULL(self, u, tc):
    return None
register(TYPE_NULL, unmarshal_NULL)

# this one is registered by hand:
def marshal_w_pycode(space, w_pycode, m):
    m.start(TYPE_CODE)
    # see pypy.interpreter.pycode for the layout
    x = space.interp_w(PyCode, w_pycode)
    m.put_int(x.co_argcount)
    m.put_int(x.co_nlocals)
    m.put_int(x.co_stacksize)
    m.put_int(x.co_flags)
    m.atom_str(TYPE_STRING, x.co_code)
    m.start(TYPE_TUPLE)
    m.put_list_w(x.co_consts_w, len(x.co_consts_w))
    m.atom_strlist(TYPE_TUPLE, TYPE_INTERNED, [space.str_w(w_name) for w_name in x.co_names_w])
    m.atom_strlist(TYPE_TUPLE, TYPE_INTERNED, x.co_varnames)
    m.atom_strlist(TYPE_TUPLE, TYPE_INTERNED, x.co_freevars)
    m.atom_strlist(TYPE_TUPLE, TYPE_INTERNED, x.co_cellvars)
    m.atom_str(TYPE_INTERNED, x.co_filename)
    m.atom_str(TYPE_INTERNED, x.co_name)
    m.put_int(x.co_firstlineno)
    m.atom_str(TYPE_STRING, x.co_lnotab)

StdObjSpace.MM.marshal_w.register(marshal_w_pycode, PyCode)

# helper for unmarshalling string lists of code objects.
# unfortunately they now can be interned or referenced,
# so we no longer can handle it in interp_marshal.atom_strlist

def unmarshal_str(u):
    w_obj = u.get_w_obj(False)
    try:
        return u.space.str_w(w_obj)
    except OperationError, e:
        if e.match(u.space, u.space.w_TypeError):
            u.raise_exc('invalid marshal data for code object')
        else:
            raise

def unmarshal_strlist(u, tc):
    lng = u.atom_lng(tc)
    res = [None] * lng
    idx = 0
    space = u.space
    while idx < lng:
        res[idx] = unmarshal_str(u)
        idx += 1
    return res

def unmarshal_pycode(space, u, tc):
    argcount    = u.get_int()
    nlocals     = u.get_int()
    stacksize   = u.get_int()
    flags       = u.get_int()
    code        = unmarshal_str(u)
    u.start(TYPE_TUPLE)
    consts_w    = u.get_list_w()
    names       = unmarshal_strlist(u, TYPE_TUPLE)
    varnames    = unmarshal_strlist(u, TYPE_TUPLE)
    freevars    = unmarshal_strlist(u, TYPE_TUPLE)
    cellvars    = unmarshal_strlist(u, TYPE_TUPLE)
    filename    = unmarshal_str(u)
    name        = unmarshal_str(u)
    firstlineno = u.get_int()
    lnotab      = unmarshal_str(u)
    code = PyCode._code_new_w(space, argcount, nlocals, stacksize, flags,
                              code, consts_w, names, varnames, filename,
                              name, firstlineno, lnotab, freevars, cellvars)
    return space.wrap(code)
register(TYPE_CODE, unmarshal_pycode)

app = gateway.applevel(r'''
    def PyUnicode_EncodeUTF8(data):
        import _codecs
        return _codecs.utf_8_encode(data)[0]

    def PyUnicode_DecodeUTF8(data):
        import _codecs
        return _codecs.utf_8_decode(data)[0]
''')

PyUnicode_EncodeUTF8 = app.interphook('PyUnicode_EncodeUTF8')
PyUnicode_DecodeUTF8 = app.interphook('PyUnicode_DecodeUTF8')

def marshal_w__Unicode(space, w_unicode, m):
    s = space.str_w(PyUnicode_EncodeUTF8(space, w_unicode))
    m.atom_str(TYPE_UNICODE, s)

def unmarshal_Unicode(space, u, tc):
    return PyUnicode_DecodeUTF8(space, space.wrap(u.get_str()))
register(TYPE_UNICODE, unmarshal_Unicode)

# not directly supported:
def marshal_w_buffer(space, w_buffer, m):
    s = space.str_w(space.str(w_buffer))
    m.atom_str(TYPE_UNKNOWN, s)

handled_by_any.append( ('buffer', marshal_w_buffer) )

app = gateway.applevel(r'''
    def string_to_buffer(s):
        return buffer(s)
''')

string_to_buffer = app.interphook('string_to_buffer')

def unmarshal_buffer(space, u, tc):
    w_s = space.wrap(u.get_str())
    return string_to_buffer(space, w_s)
register(TYPE_UNKNOWN, unmarshal_buffer)

app = gateway.applevel(r'''
    def set_to_list(theset):
        return [item for item in theset]

    def list_to_set(datalist, frozen=False):
        if frozen:
            return frozenset(datalist)
        return set(datalist)
''')

set_to_list = app.interphook('set_to_list')
list_to_set = app.interphook('list_to_set')

# not directly supported:
def marshal_w_set(space, w_set, m):
    w_lis = set_to_list(space, w_set)
    # cannot access this list directly, because it's
    # type is not exactly known through applevel.
    lis_w = space.unpackiterable(w_lis)
    m.start(TYPE_SET)
    m.put_list_w(lis_w, len(lis_w))

handled_by_any.append( ('set', marshal_w_set) )

# not directly supported:
def marshal_w_frozenset(space, w_frozenset, m):
    w_lis = set_to_list(space, w_frozenset)
    lis_w = space.unpackiterable(w_lis)
    m.start(TYPE_FROZENSET)
    m.put_list_w(lis_w, len(lis_w))

handled_by_any.append( ('frozenset', marshal_w_frozenset) )

def unmarshal_set_frozenset(space, u, tc):
    items_w = u.get_list_w()
    if tc == TYPE_SET:
        w_frozen = space.w_False
    else:
        w_frozen = space.w_True
    w_lis = space.newlist(items_w)
    return list_to_set(space, w_lis, w_frozen)
register(TYPE_SET + TYPE_FROZENSET, unmarshal_set_frozenset)

# dispatching for all not directly dispatched types
def marshal_w__ANY(space, w_obj, m):
    w_type = space.type(w_obj)
    for name, func in handled_by_any:
        w_t = space.builtin.get(name)
        if space.is_true(space.issubtype(w_type, w_t)):
            func(space, w_obj, m)
            break
    else:
        raise_exception(space, "unmarshallable object")

register_all(vars())