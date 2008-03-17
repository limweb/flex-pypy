from pypy.rpython.memory.lladdress import *
from pypy.annotation.model import SomeAddress, SomeChar
from pypy.translator.c.test.test_genc import compile
from pypy.rlib.objectmodel import free_non_gc_object

def test_null():
    def f():
        return NULL - NULL
    fc = compile(f, [])

def test_convert_to_bool():
    def f(x):
        if x:
            return bool(NULL)
        else:
            return bool(NULL + 1)
    fc = compile(f, [int])
    res = fc(1)
    assert isinstance(res, bool) and not res
    res = fc(0)
    assert isinstance(res, bool) and res

def test_memory_access():
    def f(value):
        addr = raw_malloc(16)
        addr.signed[0] = value
        result = addr.signed[0]
        raw_free(addr)
        return result
    fc = compile(f, [int])
    res = fc(42)
    assert res == 42
    res = fc(1)
    assert res == 1
    
def test_pointer_arithmetic():
    def f(offset, char):
        addr = raw_malloc(10000)
        same_offset = (addr + 2 * offset - offset) - addr 
        addr.char[offset] = char
        result = (addr + same_offset).char[0]
        raw_free(addr)
        return result
    fc = compile(f, [int, SomeChar()])
    res = fc(10, "c")
    assert res == "c"
    res = fc(12, "x")
    assert res == "x"

def test_pointer_arithmetic_inplace():
    def f(offset, char):
        addr = raw_malloc(10000)
        addr += offset
        addr.char[-offset] = char
        addr -= offset
        result = addr.char[0]
        raw_free(addr)
        return result
    fc = compile(f, [int, SomeChar()])
    res = fc(10, "c")
    assert res == "c"

def test_raw_memcopy():
    def f():
        addr = raw_malloc(100)
        addr.signed[0] = 12
        (addr + 10).signed[0] = 42
        (addr + 20).char[0] = "a"
        addr1 = raw_malloc(100)
        raw_memcopy(addr, addr1, 100)
        result = addr1.signed[0] == 12
        result = result and (addr1 + 10).signed[0] == 42
        result = result and (addr1 + 20).char[0] == "a"
        raw_free(addr)
        raw_free(addr1)
        return result
    fc = compile(f, [])
    res = fc()
    assert res

def test_pointer_comparison():
    def f():
        result = 0
        addresses = [raw_malloc(1), NULL]
        for addr1 in addresses:
            addr2 = addr1 + 1
            result = result * 2 + int(addr1 == addr2)
            result = result * 2 + int(addr1 != addr2)
            result = result * 2 + int(addr1 <  addr2)
            result = result * 2 + int(addr1 <= addr2)
            result = result * 2 + int(addr1 >  addr2)
            result = result * 2 + int(addr1 >= addr2)
        raw_free(addresses[0])
        return result
    fc = compile(f, [])
    res = fc()
    assert res == int('011100' * 2, 2)

def test_flavored_malloc_raw():
    class A(object):
        _alloc_flavor_ = "raw"
        def __init__(self, val):
            self.val = val
    def f(x):
        a = A(x + 1)
        result = a.val
        free_non_gc_object(a)
        return result
    fn = compile(f, [int])
    assert fn(1) == 2

def test_flavored_malloc_stack():
    class A(object):
        _alloc_flavor_ = "stack"
        def __init__(self, val):
            self.val = val
    def f(x):
        a = A(x + 1)
        result = a.val
        return result
    fn = compile(f, [int])
    assert fn(1) == 2

def test_weakaddress():
    from pypy.rlib.objectmodel import cast_object_to_weakgcaddress
    from pypy.rlib.objectmodel import cast_weakgcaddress_to_object
    from pypy.rpython.lltypesystem.lloperation import llop
    class A(object):
        pass
    def func(i):
        l1 = []
        l2 = []
        for i in range(i):
            a = A()
            l1.append(a)
            l2.append(cast_object_to_weakgcaddress(a))
        return len(l1) == len(l2)
    fn = compile(func, [int])
    assert fn(10)

def test_constant_weakaddress():
    from pypy.rlib.objectmodel import cast_object_to_weakgcaddress
    from pypy.rlib.objectmodel import cast_weakgcaddress_to_object
    from pypy.rpython.lltypesystem.lloperation import llop
    class A(object):
        pass
    constant_a = A()
    constant_weak_a = cast_object_to_weakgcaddress(constant_a)
    l = [constant_weak_a]
    def func(i):
        l1 = []
        l2 = []
        l3 = []
        l4 = []
        for i in range(i):
            a = A()
            l1.append(a)
            l2.append(cast_object_to_weakgcaddress(a))
            l3.append(constant_a)
            l4.extend(l)
        return len(l1) == len(l2) == len(l3) == len(l4)
    fn = compile(func, [int])
    assert fn(10)
