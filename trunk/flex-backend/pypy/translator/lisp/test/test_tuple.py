from pypy.translator.lisp.buildcl import make_cl_func
from py.test import skip

def test_tuple_get():
    def tuple_get(number):
        tuple = (number,)
        return tuple[0]
    cl_tuple_get = make_cl_func(tuple_get, [int])
    assert cl_tuple_get(1) == 1

def test_tuple_iter():
    skip("CDefinedInt implementation")
    def tuple_double(number):
        tuple = (number,)
        for item in tuple:
            number += item
        return number
    cl_double = make_cl_func(tuple_double, [int])
    assert cl_double(1) == 2
