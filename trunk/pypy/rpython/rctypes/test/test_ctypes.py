"""
The purpose of this test file is to check how ctypes really work,
down to what aliases what and what exact types operations return.
"""

import py
from ctypes import *

def test_primitive_pointer():
    x = c_int(5)
    assert x.value == 5
    x.value = 6
    assert x.value == 6

    p = pointer(x)                           #  p ---> x = 6
    assert isinstance(p.contents, c_int)
    p.contents.value += 1
    assert x.value == 7                      #  p ---> x = 7

    y = c_int(12)
    p.contents = y                           #  p ---> y = 12
    p.contents.value += 2                    #  p ---> y = 14
    assert y.value == 14
    assert x.value == 7

    pp = pointer(p)                          #  pp ---> p ---> y = 14
    pp.contents.contents = x                 #  pp ---> p ---> x = 7
    p.contents.value += 2                    #  pp ---> p ---> x = 9
    assert x.value == 9

    assert isinstance(p[0], int)
    p[0] += 1                                #  pp ---> p ---> x = 10
    assert x.value == 10
    z = c_int(86)
    p[0] = z                                 #  pp ---> p ---> x = 86  (not z!)
    assert x.value == 86
    z.value = 84
    assert x.value == 86

    assert isinstance(pp[0], POINTER(c_int))
    assert pp[0].contents.value == x.value == 86
    pp[0].contents = z                       #  pp ---> p ---> z = 84
    assert p.contents.value == z.value == 84

##    *** the rest is commented out because it should work but occasionally
##    *** trigger a ctypes bug (SourceForge bug #1467852). ***
##    q = pointer(y)
##    pp[0] = q                                #  pp ---> p ---> y = 14
##    assert y.value == 14                     #        (^^^ not q! )
##    assert p.contents.value == 14
##    assert pp.contents.contents.value == 14
##    q.contents = x
##    assert pp.contents.contents.value == 14


def test_char_p():
    x = c_char_p("hello\x00world")
    assert x.value == "hello"
    x.value = "world"
    assert x.value == "world"

    p = pointer(x)
    assert p[0] == x.value == "world"
    p[0] = "other"
    assert x.value == p.contents.value == p[0] == "other"

    myarray = (c_char_p * 10)()
    myarray[7] = "hello"
    assert isinstance(myarray[7], str)
    assert myarray[7] == "hello"

def test_struct():
    class tagpoint(Structure):
        _fields_ = [('x', c_int),
                    ('p', POINTER(c_short))]

    y = c_short(123)
    z = c_short(-33)
    s = tagpoint()
    s.p.contents = z
    assert s.p.contents.value == -33
    s.p = pointer(y)
    assert s.p.contents.value == 123
    s.p.contents.value = 124
    assert y.value == 124

    s = tagpoint(x=12)
    assert s.x == 12
    s = tagpoint(17, p=pointer(z))
    assert s.x == 17
    assert s.p.contents.value == -33

def test_void_p():
    x = c_int(12)
    p1 = cast(pointer(x), c_void_p)
    p2 = cast(p1, POINTER(c_int))
    assert p2.contents.value == 12

def test_char_array():
    a = (c_char * 3)()
    a[0] = 'x'
    a[1] = 'y'
    assert a.value == 'xy'
    a[2] = 'z'
    assert a.value == 'xyz'

    b = create_string_buffer(3)
    assert type(b) is type(a)
    assert len(b) == 3

    b.value = "nxw"
    assert b[0] == 'n'
    assert b[1] == 'x'
    assert b[2] == 'w'

    b.value = "?"
    assert b[0] == '?'
    assert b[1] == '\x00'
    assert b[2] == 'w'

    class S(Structure):
        _fields_ = [('p', POINTER(c_char))]

    s = S()
    s.p = b
    s.p.contents.value = '!'
    assert b.value == '!'

    assert len(create_string_buffer(0)) == 0

def test_array():
    a = (c_int * 10)()

    class S(Structure):
        _fields_ = [('p', POINTER(c_int))]

    s = S()
    s.p = a
    s.p.contents.value = 42
    assert a[0] == 42

    a = (c_int * 5)(5, 6, 7)
    assert list(a) == [5, 6, 7, 0, 0]

def test_truth_value():
    p = POINTER(c_int)()
    assert not p
    p.contents = c_int(12)
    assert p
    # I can't figure out how to reset p to NULL...

    assert c_int(12)
    assert not c_int(0)    # a bit strange, if you ask me
    assert c_int(-1)
    assert not c_byte(0)
    assert not c_char('\x00')   # hum
    assert not c_float(0.0)
    assert not c_double(0.0)
    assert not c_ulonglong(0)
    assert c_ulonglong(2L**42)

    assert c_char_p("hello")
    assert c_char_p("")
    assert not c_char_p(None)

    assert not c_void_p()

def test_py_object():
    class TAG:
        pass
    x = py_object(TAG)
    assert x.value is TAG
    x.value = 42
    assert x.value == 42

def test_pythonapi():
    PyInt_AsLong = pythonapi.PyInt_AsLong
    PyInt_AsLong.argtypes = [py_object]
    PyInt_AsLong.restype = c_long
    assert PyInt_AsLong(py_object(17L)) == 17
    py.test.raises(TypeError, "PyInt_AsLong(py_object('hello'))")

def test_py_object_subclass():
    PyInt_FromLong = pythonapi.PyInt_FromLong
    # automatic unwrapping of the py_object result
    PyInt_FromLong.argtypes = [c_long]
    PyInt_FromLong.restype = py_object
    assert isinstance(PyInt_FromLong(17), int)

    # but not if we subclass it...
    class W_Object(py_object):
        pass
    PyInt_FromLong.argtypes = [c_long]
    PyInt_FromLong.restype = W_Object
    assert isinstance(PyInt_FromLong(17), W_Object)

def test_sizeof():
    x = create_string_buffer(117)
    assert sizeof(x) == 117    # assumes that chars are one byte each
    x = (c_int * 42)()
    assert sizeof(x) == 42 * sizeof(c_int)

def test_convert_pointers():
    PyString_FromString = pythonapi.PyString_FromString
    PyString_FromString.restype = py_object

    # automatic conversions to c_char_p
    PyString_FromString.argtypes = [c_char_p]
    assert PyString_FromString("hello") == "hello"
    assert PyString_FromString(c_char_p("hello")) == "hello"
    assert PyString_FromString((c_char * 6)(*"hello")) == "hello"
    assert PyString_FromString(create_string_buffer("hello")) == "hello"

    # automatic conversions to c_void_p
    PyString_FromString.argtypes = [c_void_p]
    assert PyString_FromString("hello") == "hello"
    assert PyString_FromString(c_char_p("hello")) == "hello"
    assert PyString_FromString((c_char * 6)(*"hello")) == "hello"
    assert PyString_FromString((c_byte * 6)(104,101,108,108,111)) =="hello"
    assert PyString_FromString(create_string_buffer("hello")) == "hello"

def test_varsize_cast():
    import struct
    N = struct.calcsize("l")
    x = c_long()
    p = cast(pointer(x), POINTER(c_ubyte*N))
    for i, c in enumerate(struct.pack("l", 12345678)):
        p.contents[i] = ord(c)
    assert x.value == 12345678

def test_cfunctype_inspection():
    T = CFUNCTYPE(c_int, c_ubyte)
    # T.argtypes and T.restype don't work, must use a dummy instance
    assert list(T().argtypes) == [c_ubyte]
    assert T().restype == c_int
