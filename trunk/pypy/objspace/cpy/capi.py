"""
CTypes declarations for the CPython API.
"""
import sys
import ctypes
import py
from ctypes import *
from pypy.rpython.rctypes.tool import ctypes_platform
##from pypy.rpython.rctypes.implementation import CALLBACK_FUNCTYPE
from pypy.objspace.cpy.ctypes_base import W_Object, cpyapi


###############################################################
# ____________________ Types and constants ____________________

##PyCFunction = CALLBACK_FUNCTYPE(W_Object, W_Object, W_Object, callconv=PyDLL)
##PyNoArgsFunction = CALLBACK_FUNCTYPE(W_Object, W_Object, callconv=PyDLL)
##PyCFunctionWithKeywords = CALLBACK_FUNCTYPE(W_Object,
##                                            W_Object, W_Object, W_Object,
##                                            callconv=PyDLL)

class CConfig:
    _header_ = """
#include <Python.h>
#if PY_VERSION_HEX < 0x02050000   /* < 2.5 */
typedef int Py_ssize_t;
#endif
    """
    _include_dirs_ = [ctypes_platform.get_python_include_dir()]
    
    Py_ssize_t = ctypes_platform.SimpleType('Py_ssize_t')
    Py_UNICODE = ctypes_platform.SimpleType('Py_UNICODE')
    Py_UNICODE_WIDE = ctypes_platform.Defined('Py_UNICODE_WIDE')

    Py_LT = ctypes_platform.ConstantInteger('Py_LT')
    Py_LE = ctypes_platform.ConstantInteger('Py_LE')
    Py_EQ = ctypes_platform.ConstantInteger('Py_EQ')
    Py_NE = ctypes_platform.ConstantInteger('Py_NE')
    Py_GT = ctypes_platform.ConstantInteger('Py_GT')
    Py_GE = ctypes_platform.ConstantInteger('Py_GE')

##    PyMethodDef = ctypes_platform.Struct('PyMethodDef',
##                                         [('ml_name', c_char_p),
##                                          ('ml_meth', PyCFunction),
##                                          ('ml_flags', c_int),
##                                          ('ml_doc', c_char_p)])
##    METH_VARARGS = ctypes_platform.ConstantInteger('METH_VARARGS')

##    # NB. all integers fields can be specified as c_int,
##    #     which is replaced by the more precise type automatically.
##    PyObject_HEAD = [('ob_refcnt', c_int), ('ob_type', 
##    PyTypeObject = ctypes_platform.Struct('PyTypeObject', [
##        ('tp_name', c_char_p),
##        ('tp_basicsize', c_int),
##        ('tp_flags', c_int),
##        ('tp_doc', c_char_p),
##        ])
##    Py_TPFLAGS_DEFAULT = ctypes_platform.ConstantInteger('Py_TPFLAGS_DEFAULT')

globals().update(ctypes_platform.configure(CConfig))
del CConfig


###########################################################
# ____________________ Object Protocol ____________________

PyObject_Size = cpyapi.PyObject_Size
PyObject_Size.argtypes = [W_Object]
PyObject_Size.restype = Py_ssize_t

PyObject_GetAttr = cpyapi.PyObject_GetAttr
PyObject_GetAttr.argtypes = [W_Object, W_Object]
PyObject_GetAttr.restype = W_Object

PyObject_SetAttr = cpyapi.PyObject_SetAttr
PyObject_SetAttr.argtypes = [W_Object, W_Object, W_Object]
PyObject_SetAttr.restype = c_int

PyObject_GetItem = cpyapi.PyObject_GetItem
PyObject_GetItem.argtypes = [W_Object, W_Object]
PyObject_GetItem.restype = W_Object

PyObject_SetItem = cpyapi.PyObject_SetItem
PyObject_SetItem.argtypes = [W_Object, W_Object, W_Object]
PyObject_SetItem.restype = c_int

PyObject_DelItem = cpyapi.PyObject_DelItem
PyObject_DelItem.argtypes = [W_Object, W_Object]
PyObject_DelItem.restype = c_int

PyObject_Call = cpyapi.PyObject_Call
PyObject_Call.argtypes = [W_Object, W_Object, W_Object]
PyObject_Call.restype = W_Object

PyObject_CallFunctionObjArgs = cpyapi.PyObject_CallFunctionObjArgs
PyObject_CallFunctionObjArgs.restype = W_Object
#PyObject_CallFunctionObjArgs.argtypes = [W_Object, ..., final NULL]

PyObject_RichCompare = cpyapi.PyObject_RichCompare
PyObject_RichCompare.argtypes = [W_Object, W_Object, c_int]
PyObject_RichCompare.restype = W_Object

PyObject_RichCompareBool = cpyapi.PyObject_RichCompareBool
PyObject_RichCompareBool.argtypes = [W_Object, W_Object, c_int]
PyObject_RichCompareBool.restype = c_int

PyObject_Compare = cpyapi.PyObject_Compare
PyObject_Compare.argtypes = [W_Object, W_Object]
PyObject_Compare.restype = c_int

PyObject_GetIter = cpyapi.PyObject_GetIter
PyObject_GetIter.argtypes = [W_Object]
PyObject_GetIter.restype = W_Object

PyIter_Next = cpyapi.PyIter_Next
PyIter_Next.argtypes = [W_Object]
PyIter_Next.restype = W_Object

PyObject_IsTrue = cpyapi.PyObject_IsTrue
PyObject_IsTrue.argtypes = [W_Object]
PyObject_IsTrue.restype = c_int

PyObject_Type = cpyapi.PyObject_Type
PyObject_Type.argtypes = [W_Object]
PyObject_Type.restype = W_Object

PyObject_Str = cpyapi.PyObject_Str
PyObject_Str.argtypes = [W_Object]
PyObject_Str.restype = W_Object

PyObject_Repr = cpyapi.PyObject_Repr
PyObject_Repr.argtypes = [W_Object]
PyObject_Repr.restype = W_Object

PyObject_Hash = cpyapi.PyObject_Hash
PyObject_Hash.argtypes = [W_Object]
PyObject_Hash.restype = c_long


###########################################################
# ____________________ Number Protocol ____________________

UnaryOps = {'pos':       'PyNumber_Positive',
            'neg':       'PyNumber_Negative',
            'abs':       'PyNumber_Absolute',
            'invert':    'PyNumber_Invert',
            'int':       'PyNumber_Int',
            'long':      'PyNumber_Long',
            'float':     'PyNumber_Float',
            }
BinaryOps = {'add':      'PyNumber_Add',
             'sub':      'PyNumber_Subtract',
             'mul':      'PyNumber_Multiply',
             'truediv':  'PyNumber_TrueDivide',
             'floordiv': 'PyNumber_FloorDivide',
             'div':      'PyNumber_Divide',
             'mod':      'PyNumber_Remainder',
             'divmod':   'PyNumber_Divmod',
             'lshift':   'PyNumber_Lshift',
             'rshift':   'PyNumber_Rshift',
             'and_':     'PyNumber_And',
             'or_':      'PyNumber_Or',
             'xor':      'PyNumber_Xor',

             'inplace_add':      'PyNumber_InPlaceAdd',
             'inplace_sub':      'PyNumber_InPlaceSubtract',
             'inplace_mul':      'PyNumber_InPlaceMultiply',
             'inplace_truediv':  'PyNumber_InPlaceTrueDivide',
             'inplace_floordiv': 'PyNumber_InPlaceFloorDivide',
             'inplace_div':      'PyNumber_InPlaceDivide',
             'inplace_mod':      'PyNumber_InPlaceRemainder',
             'inplace_lshift':   'PyNumber_InPlaceLshift',
             'inplace_rshift':   'PyNumber_InPlaceRshift',
             'inplace_and':      'PyNumber_InPlaceAnd',
             'inplace_or':       'PyNumber_InPlaceOr',
             'inplace_xor':      'PyNumber_InPlaceXor',
             }

for name in UnaryOps.values():
    exec py.code.Source("""
        %(name)s = cpyapi.%(name)s
        %(name)s.argtypes = [W_Object]
        %(name)s.restype = W_Object
    """ % locals()).compile()

for name in BinaryOps.values():
    exec py.code.Source("""
        %(name)s = cpyapi.%(name)s
        %(name)s.argtypes = [W_Object, W_Object]
        %(name)s.restype = W_Object
    """ % locals()).compile()

del name

PyNumber_Power = cpyapi.PyNumber_Power
PyNumber_Power.argtypes = [W_Object, W_Object, W_Object]
PyNumber_Power.restype = W_Object

PyNumber_InPlacePower = cpyapi.PyNumber_InPlacePower
PyNumber_InPlacePower.argtypes = [W_Object, W_Object, W_Object]
PyNumber_InPlacePower.restype = W_Object


#############################################################
# ____________________ Sequence Protocol ____________________

PySequence_Tuple = cpyapi.PySequence_Tuple
PySequence_Tuple.argtypes = [W_Object]
PySequence_Tuple.restype = W_Object

PySequence_SetItem = cpyapi.PySequence_SetItem
PySequence_SetItem.argtypes = [W_Object, Py_ssize_t, W_Object]
PySequence_SetItem.restype = c_int

PySequence_Contains = cpyapi.PySequence_Contains
PySequence_Contains.argtypes = [W_Object, W_Object]
PySequence_Contains.restype = c_int


########################################################
# ____________________ Type Objects ____________________

PyType_IsSubtype = cpyapi.PyType_IsSubtype
PyType_IsSubtype.argtypes = [W_Object, W_Object]
PyType_IsSubtype.restype = c_int

_PyType_Lookup = cpyapi._PyType_Lookup
_PyType_Lookup.argtypes = [W_Object, W_Object]
_PyType_Lookup.restype = W_Object


###########################################################
# ____________________ Numeric Objects ____________________

PyInt_FromLong = cpyapi.PyInt_FromLong
PyInt_FromLong.argtypes = [c_long]
PyInt_FromLong.restype = W_Object

PyInt_AsLong = cpyapi.PyInt_AsLong
PyInt_AsLong.argtypes = [W_Object]
PyInt_AsLong.restype = c_long

PyInt_AsUnsignedLongMask = cpyapi.PyInt_AsUnsignedLongMask
PyInt_AsUnsignedLongMask.argtypes = [W_Object]
PyInt_AsUnsignedLongMask.restype = c_ulong

PyFloat_FromDouble = cpyapi.PyFloat_FromDouble
PyFloat_FromDouble.argtypes = [c_double]
PyFloat_FromDouble.restype = W_Object

PyFloat_AsDouble = cpyapi.PyFloat_AsDouble 
PyFloat_AsDouble.argtypes = [W_Object]
PyFloat_AsDouble.restype = c_double 

PyLong_FromLong = cpyapi.PyLong_FromLong
PyLong_FromLong.argtypes = [c_long]
PyLong_FromLong.restype = W_Object

PyLong_FromUnsignedLong = cpyapi.PyLong_FromUnsignedLong
PyLong_FromUnsignedLong.argtypes = [c_ulong]
PyLong_FromUnsignedLong.restype = W_Object

PyLong_FromLongLong = cpyapi.PyLong_FromLongLong
PyLong_FromLongLong.argtypes = [c_longlong]
PyLong_FromLongLong.restype = W_Object

PyLong_FromUnsignedLongLong = cpyapi.PyLong_FromUnsignedLongLong
PyLong_FromUnsignedLongLong.argtypes = [c_ulonglong]
PyLong_FromUnsignedLongLong.restype = W_Object

_PyLong_Sign = cpyapi._PyLong_Sign
_PyLong_Sign.argtypes = [W_Object]
_PyLong_Sign.restype = c_long

_PyLong_NumBits = cpyapi._PyLong_NumBits
_PyLong_NumBits.argtypes = [W_Object]
_PyLong_NumBits.restype = c_size_t

_PyLong_AsByteArray = cpyapi._PyLong_AsByteArray
_PyLong_AsByteArray.argtypes = [W_Object, POINTER(c_ubyte), c_size_t,
                                c_long, c_long]
_PyLong_AsByteArray.restype = c_long

# a version of PyLong_FromVoidPtr() that pretends to take a PyObject* arg
PyLong_FromVoidPtr_PYOBJ = cpyapi.PyLong_FromVoidPtr
PyLong_FromVoidPtr_PYOBJ.argtypes = [W_Object]
PyLong_FromVoidPtr_PYOBJ.restype = W_Object


###################################################
# ____________________ Strings ____________________

PyString_FromStringAndSize = cpyapi.PyString_FromStringAndSize
PyString_FromStringAndSize.argtypes = [c_char_p, Py_ssize_t]
PyString_FromStringAndSize.restype = W_Object

PyString_InternInPlace = cpyapi.PyString_InternInPlace
PyString_InternInPlace.argtypes = [POINTER(W_Object)]
PyString_InternInPlace.restype = None

PyString_AsString = cpyapi.PyString_AsString
PyString_AsString.argtypes = [W_Object]
PyString_AsString.restype = POINTER(c_char)

PyString_Size = cpyapi.PyString_Size
PyString_Size.argtypes = [W_Object]
PyString_Size.restype = Py_ssize_t

if Py_UNICODE_WIDE: PyUnicode_AsUnicode = cpyapi.PyUnicodeUCS4_AsUnicode
else:               PyUnicode_AsUnicode = cpyapi.PyUnicodeUCS2_AsUnicode
PyUnicode_AsUnicode.argtypes = [W_Object]
PyUnicode_AsUnicode.restype = POINTER(Py_UNICODE)

if Py_UNICODE_WIDE: PyUnicode_FromUnicode = cpyapi.PyUnicodeUCS4_FromUnicode
else:               PyUnicode_FromUnicode = cpyapi.PyUnicodeUCS2_FromUnicode
PyUnicode_FromUnicode.argtypes = [POINTER(Py_UNICODE), Py_ssize_t]
PyUnicode_FromUnicode.restype = W_Object

if Py_UNICODE_WIDE: PyUnicode_FromOrdinal = cpyapi.PyUnicodeUCS4_FromOrdinal
else:               PyUnicode_FromOrdinal = cpyapi.PyUnicodeUCS2_FromOrdinal
PyUnicode_FromOrdinal.argtypes = [Py_UNICODE]
PyUnicode_FromOrdinal.restype = W_Object


##################################################
# ____________________ Tuples ____________________

PyTuple_New = cpyapi.PyTuple_New
PyTuple_New.argtypes = [Py_ssize_t]
PyTuple_New.restype = W_Object

PyTuple_SetItem = cpyapi.PyTuple_SetItem
PyTuple_SetItem.argtypes = [W_Object, Py_ssize_t, W_Object]
PyTuple_SetItem.restype = c_int


#################################################
# ____________________ Lists ____________________

PyList_New = cpyapi.PyList_New
PyList_New.argtypes = [Py_ssize_t]
PyList_New.restype = W_Object

PyList_Append = cpyapi.PyList_Append
PyList_Append.argtypes = [W_Object, W_Object]
PyList_Append.restype = c_int

PyList_SetItem = cpyapi.PyList_SetItem
PyList_SetItem.argtypes = [W_Object, Py_ssize_t, W_Object]
PyList_SetItem.restype = c_int


########################################################
# ____________________ Dictionaries ____________________

PyDict_New = cpyapi.PyDict_New
PyDict_New.argtypes = []
PyDict_New.restype = W_Object

PyDict_SetItem = cpyapi.PyDict_SetItem
PyDict_SetItem.argtypes = [W_Object, W_Object, W_Object]
PyDict_SetItem.restype = c_int


#####################################################
# ____________________ Utilities ____________________

PyImport_ImportModule = cpyapi.PyImport_ImportModule
PyImport_ImportModule.argtypes = [c_char_p]
PyImport_ImportModule.restype = W_Object

_PyObject_Dump = cpyapi._PyObject_Dump
_PyObject_Dump.argtypes = [W_Object]
_PyObject_Dump.restype = None


################################################
# ____________________ Misc ____________________

PySlice_New = cpyapi.PySlice_New
PySlice_New.argtypes = [W_Object, W_Object, W_Object]
PySlice_New.restype = W_Object


##############################################################
# ____________________ Built-in functions ____________________

PyArg_ParseTuple = cpyapi.PyArg_ParseTuple
PyArg_ParseTuple.restype = c_int
#PyArg_ParseTuple.argtypes = [W_Object, c_char_p, ...]

PyArg_ParseTupleAndKeywords = cpyapi.PyArg_ParseTupleAndKeywords
PyArg_ParseTupleAndKeywords.restype = c_int
#PyArg_ParseTupleAndKeywords.argtypes = [W_Object, W_Object,
#                                        c_char_p, POINTER(c_char_p), ...]

##PyCFunction_NewEx = cpyapi.PyCFunction_NewEx
##PyCFunction_NewEx.argtypes = [POINTER(PyMethodDef), W_Object, W_Object]
##PyCFunction_NewEx.restype = W_Object


##############################################################
# ____________________ Exception handling ____________________

# "RAW" because it comes from pythonapi instead of cpyapi.
# The normal error handling (wrapping CPython exceptions into
# an OperationError) is disabled.
RAW_PyErr_SetObject = pythonapi.PyErr_SetObject
RAW_PyErr_SetObject.argtypes = [W_Object, W_Object]
RAW_PyErr_SetObject.restype = None
RAW_PyErr_SetObject._rctypes_pyerrchecker_ = None

# WARNING: consumes references
RAW_PyErr_Restore = pythonapi.PyErr_Restore
RAW_PyErr_Restore.argtypes = [W_Object, W_Object, W_Object]
RAW_PyErr_Restore.restype = None
RAW_PyErr_Restore._rctypes_pyerrchecker_ = None

RAW_PyErr_Occurred = pythonapi.PyErr_Occurred
RAW_PyErr_Occurred.argtypes = []
RAW_PyErr_Occurred.restype = c_void_p
RAW_PyErr_Occurred._rctypes_pyerrchecker_ = None

RAW_PyErr_Fetch = pythonapi.PyErr_Fetch
RAW_PyErr_Fetch.argtypes = [POINTER(W_Object),
                            POINTER(W_Object),
                            POINTER(W_Object)]
RAW_PyErr_Fetch.restype = None
RAW_PyErr_Fetch._rctypes_pyerrchecker_ = None
