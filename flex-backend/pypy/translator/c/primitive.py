import sys
from pypy.rlib.objectmodel import Symbolic, ComputedIntSymbolic
from pypy.rlib.objectmodel import CDefinedIntSymbolic
from pypy.rpython.lltypesystem.rffi import CConstant
from pypy.rpython.lltypesystem.lltype import *
from pypy.rpython.lltypesystem.llmemory import Address, \
     AddressOffset, ItemOffset, ArrayItemsOffset, FieldOffset, \
     CompositeOffset, ArrayLengthOffset, WeakGcAddress, fakeweakaddress, \
     GCHeaderOffset
from pypy.translator.c.support import cdecl

# ____________________________________________________________
#
# Primitives

def name_signed(value, db):
    if isinstance(value, Symbolic):
        if isinstance(value, FieldOffset):
            structnode = db.gettypedefnode(value.TYPE)
            return 'offsetof(%s, %s)'%(
                cdecl(db.gettype(value.TYPE), ''),
                structnode.c_struct_field_name(value.fldname))
        elif isinstance(value, ItemOffset):
            if value.TYPE != Void:
                return '(sizeof(%s) * %s)'%(
                    cdecl(db.gettype(value.TYPE), ''), value.repeat)
            else:
                return '0'
        elif isinstance(value, ArrayItemsOffset):
            if isinstance(value.TYPE, FixedSizeArray):
                return '0'
            elif value.TYPE.OF != Void:
                return 'offsetof(%s, items)'%(
                    cdecl(db.gettype(value.TYPE), ''))
            else:
                return 'sizeof(%s)'%(cdecl(db.gettype(value.TYPE), ''),)
        elif isinstance(value, ArrayLengthOffset):
            return 'offsetof(%s, length)'%(
                cdecl(db.gettype(value.TYPE), ''))
        elif isinstance(value, CompositeOffset):
            names = [name_signed(item, db) for item in value.offsets]
            return '(%s)' % (' + '.join(names),)
        elif type(value) == AddressOffset:
            return '0'
        elif type(value) == GCHeaderOffset:
            return '0'
        elif isinstance(value, CDefinedIntSymbolic):
            return str(value.expr)
        elif isinstance(value, ComputedIntSymbolic):
            value = value.compute_fn()
        elif isinstance(value, CConstant):
            return value.c_name
        else:
            raise Exception("unimplemented symbolic %r"%value)
    if value is None:
        assert not db.completed
        return None
    if value == -sys.maxint-1:   # blame C
        return '(-%dL-1L)' % sys.maxint
    else:
        return '%dL' % value

def name_unsigned(value, db):
    assert value >= 0
    return '%dUL' % value

def name_unsignedlonglong(value, db):
    assert value >= 0
    return '%dULL' % value

def name_signedlonglong(value, db):
    return '%dLL' % value

def isinf(x):
    return x != 0.0 and x / 2 == x

# To get isnan, working x-platform and both on 2.3 and 2.4, is a
# horror.  I think this works (for reasons I don't really want to talk
# about), and probably when implemented on top of pypy, too.
def isnan(v):
    return v != v*1.0 or (v == 1.0 and v == 2.0)

def name_float(value, db):
    if isinf(value):
        if value > 0:
            return '(Py_HUGE_VAL)'
        else:
            return '(-Py_HUGE_VAL)'
    elif isnan(value):
        return '(Py_HUGE_VAL/Py_HUGE_VAL)'
    else:
        return repr(value)

def name_char(value, db):
    assert type(value) is str and len(value) == 1
    if ' ' <= value < '\x7f':
        return "'%s'" % (value.replace("\\", r"\\").replace("'", r"\'"),)
    else:
        return '%d' % ord(value)

def name_bool(value, db):
    return '%d' % value

def name_void(value, db):
    return '/* nothing */'

def name_unichar(value, db):
    assert type(value) is unicode and len(value) == 1
    return '%d' % ord(value)

def name_address(value, db):
    if value:
        return db.get(value.ref())
    else:
        return 'NULL'

def name_weakgcaddress(value, db):
    assert isinstance(value, fakeweakaddress)
    if value.ref is None: 
        return 'HIDE_POINTER(NULL)'
    else:
        ob = value.ref()
        assert ob is not None
        return 'HIDE_POINTER(%s)'%db.get(ob)

# On 64 bit machines, SignedLongLong and Signed are the same, so the
# order matters, because we want the Signed implementation.
PrimitiveName = {
    SignedLongLong:   name_signedlonglong,
    Signed:   name_signed,
    UnsignedLongLong: name_unsignedlonglong,
    Unsigned: name_unsigned,
    Float:    name_float,
    Char:     name_char,
    UniChar:  name_unichar,
    Bool:     name_bool,
    Void:     name_void,
    Address:  name_address,
    WeakGcAddress:  name_weakgcaddress,
    }

PrimitiveType = {
    SignedLongLong:   'long long @',
    Signed:   'long @',
    UnsignedLongLong: 'unsigned long long @',
    Unsigned: 'unsigned long @',
    Float:    'double @',
    Char:     'char @',
    UniChar:  'unsigned int @',
    Bool:     'bool_t @',
    Void:     'void @',
    Address:  'void* @',
    WeakGcAddress:  'GC_hidden_pointer @',
    }

PrimitiveErrorValue = {
    SignedLongLong:   '-1LL',
    Signed:   '-1',
    UnsignedLongLong: '((unsigned long long) -1)',
    Unsigned: '((unsigned) -1)',
    Float:    '-1.0',
    Char:     '((char) -1)',
    UniChar:  '((unsigned) -1)',
    Bool:     '0 /* error */',
    Void:     '/* error */',
    Address:  'NULL',
    WeakGcAddress:  'HIDE_POINTER(NULL)',
    }

def define_c_primitive(ll_type, c_name):
    if ll_type in PrimitiveName:
        return
    if ll_type._cast(-1) > 0:
        name_str = '((%s) %%dULL)' % c_name
    else:
        name_str = '((%s) %%dLL)' % c_name
    PrimitiveName[ll_type] = lambda value, db: name_str % value
    PrimitiveType[ll_type] = '%s @'% c_name
    PrimitiveErrorValue[ll_type] = '((%s) -1)'% c_name
    
try:
    import ctypes
except ImportError:
    pass
else:
    from pypy.rpython.rctypes import rcarithmetic as rcarith
    for ll_type, c_name in [(rcarith.CByte, 'signed char'),
                            (rcarith.CUByte, 'unsigned char'),
                            (rcarith.CShort, 'short'),
                            (rcarith.CUShort, 'unsigned short'),
                            (rcarith.CInt, 'int'),
                            (rcarith.CUInt, 'unsigned int'),
                            (rcarith.CLong, 'long'),
                            (rcarith.CULong, 'unsigned long'),
                            (rcarith.CLonglong, 'long long'),
                            (rcarith.CULonglong, 'unsigned long long')]:
        define_c_primitive(ll_type, c_name)
