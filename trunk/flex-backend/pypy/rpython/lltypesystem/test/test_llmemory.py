from pypy.rpython.lltypesystem.llmemory import *
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.test.test_llinterp import interpret
import py

def test_simple():
    S = lltype.GcStruct("S", ("x", lltype.Signed), ("y", lltype.Signed))
    s = lltype.malloc(S)
    s.x = 123
    s.y = 456
    a = fakeaddress(s)
    assert a.ref() == s
    b = a + FieldOffset(S, 'x')
    assert b.signed[0] == 123
    b.signed[0] = 234
    assert s.x == 234

def test_composite():
    S1 = lltype.GcStruct("S1", ("x", lltype.Signed), ("y", lltype.Signed))
    S2 = lltype.GcStruct("S2", ("s", S1))
    s2 = lltype.malloc(S2)
    s2.s.x = 123
    s2.s.y = 456
    a = fakeaddress(s2)
    assert a.ref() == s2
    b = a + FieldOffset(S2, 's') + FieldOffset(S1, 'x')
    assert b.signed[0] == 123
    b.signed[0] = 234
    assert s2.s.x == 234
    
def test_array():
    A = lltype.GcArray(lltype.Signed)
    x = lltype.malloc(A, 5)
    x[3] = 123
    a = fakeaddress(x)
    b = a + ArrayItemsOffset(A)
    b += ItemOffset(lltype.Signed)*2
    b += ItemOffset(lltype.Signed)
    assert b.signed[0] == 123
    b.signed[0] = 14
    assert x[3] == 14
    
def test_dont_mix_offsets_and_ints():
    o = AddressOffset()
    py.test.raises(TypeError, "1 + o")
    py.test.raises(TypeError, "o + 1")
    
def test_sizeof():
    # this is mostly an "assert not raises" sort of test
    array = lltype.Array(lltype.Signed)
    struct = lltype.Struct("S", ('x', lltype.Signed))
    varstruct = lltype.Struct("S", ('x', lltype.Signed), ('y', array))
    sizeof(struct)
    sizeof(lltype.Signed)
    py.test.raises(AssertionError, "sizeof(array)")
    py.test.raises(AssertionError, "sizeof(varstruct)")
    sizeof(array, 1)
    sizeof(varstruct, 2)

def test_cast_ptr_to_adr():
    from pypy.rpython.memory.test.test_llinterpsim import interpret
    class A(object):
        pass
    def f(x):
        if x:
            a = A()
        else:
            a = None
        adr_a = cast_ptr_to_adr(a)
        return bool(adr_a)
    res = interpret(f, [1])
    assert res
    res = interpret(f, [0])
    assert not res

def test_confusion_with_fixedarray_item_0():
    A = lltype.FixedSizeArray(lltype.Signed, 5)
    B = lltype.FixedSizeArray(A, 3)
    myoffset = itemoffsetof(A, 4)
    global_b = lltype.malloc(B, immortal=True)
    global_b[0][4] = 1000
    global_b[1][4] = 1010
    global_b[2][4] = 1200
    def f(n):
        a = global_b[n]    # bug: with n=0, this was considered as the
                           # first inlined substructure, confusing
                           # normalizeptr(a) into returning global_b
        adr_a = cast_ptr_to_adr(a)
        return (adr_a + myoffset).signed[0]
    assert f(2) == 1200
    assert f(1) == 1010
    assert f(0) == 1000
    res = interpret(f, [0])
    assert res == 1000

def test_structarray_add():
    S = lltype.Struct("S", ("x", lltype.Signed))
    for a in [lltype.malloc(lltype.GcArray(S), 5),
              lltype.malloc(lltype.FixedSizeArray(S, 5), immortal=True)]:
        a[3].x = 42
        adr_s = cast_ptr_to_adr(a[0])
        adr_s += sizeof(S) * 3
        s = cast_adr_to_ptr(adr_s, lltype.Ptr(S))
        assert s.x == 42

def test_cast_adr_to_ptr():
    from pypy.rpython.memory.test.test_llinterpsim import interpret
    S = lltype.GcStruct("S", ("x", lltype.Signed))
    Sptr = lltype.Ptr(S)
    def f():
        s1 = lltype.malloc(S)
        adr = cast_ptr_to_adr(s1)
        s2 = cast_adr_to_ptr(adr, Sptr)
        return s1 == s2
    res = interpret(f, [])
    assert res

def test_fakeaddress_equality():
    S = lltype.GcStruct('S', ('x', lltype.Signed))
    T = lltype.GcStruct('T', ('y', lltype.Signed))

    s1 = lltype.malloc(S)
    s1.x = 1
    s2 = lltype.malloc(S)
    s2.x = 1
    t = lltype.malloc(T)
    t.y = 1

    a1s1, a2s1, as2, at = map(cast_ptr_to_adr, [s1, s1, s2, t])
    assert a1s1 == a2s1
    assert a1s1 != as2
    assert a1s1 != at
    assert as2 != at

def test_more_fakeaddress_equality():
    S = lltype.GcStruct('S', ('x', lltype.Signed))
    T = lltype.GcStruct('T', ('s', S))

    t = lltype.malloc(T)
    t.s.x = 1
    s = lltype.cast_pointer(lltype.Ptr(S), t)

    a_t, a_s = map(cast_ptr_to_adr, [s, t])
    assert a_t == a_s

def test_cast_adr_to_int():
    from pypy.rpython.memory.test.test_llinterpsim import interpret
    S = lltype.GcStruct("S", ("x", lltype.Signed))
    Sptr = lltype.Ptr(S)
    def f():
        s1 = lltype.malloc(S)
        adr = cast_ptr_to_adr(s1)
        i = cast_adr_to_int(adr)
        i2 = lltype.cast_ptr_to_int(s1)
        return i == i2
    assert f()
    res = interpret(f, [])
    assert res

def test_weak_casts():
    from pypy.rpython.memory.test.test_llinterpsim import interpret
    S = lltype.GcStruct("S", ("x", lltype.Signed))
    Sptr = lltype.Ptr(S)
    def f():
        s1 = lltype.malloc(S)
        adr = cast_ptr_to_weakadr(s1)
        s2 = cast_weakadr_to_ptr(adr, Sptr)
        return s1 == s2
    res = interpret(f, [])
    assert res

def test_fakeaccessor():
    S = lltype.GcStruct("S", ("x", lltype.Signed), ("y", lltype.Signed))
    s = lltype.malloc(S)
    s.x = 123
    s.y = 456
    adr = cast_ptr_to_adr(s)
    adr += FieldOffset(S, "y")
    assert adr.signed[0] == 456
    adr.signed[0] = 789
    assert s.y == 789

    A = lltype.GcArray(lltype.Signed)
    a = lltype.malloc(A, 5)
    a[3] = 123
    adr = cast_ptr_to_adr(a)
    assert (adr + ArrayLengthOffset(A)).signed[0] == 5
    assert (adr + ArrayItemsOffset(A)).signed[3] == 123
    (adr + ArrayItemsOffset(A)).signed[3] = 456
    assert a[3] == 456
    adr1000 = (adr + ArrayItemsOffset(A) + ItemOffset(lltype.Signed, 1000))
    assert adr1000.signed[-997] == 456

    A = lltype.GcArray(lltype.Char)
    a = lltype.malloc(A, 5)
    a[3] = '*'
    adr = cast_ptr_to_adr(a)
    assert (adr + ArrayLengthOffset(A)).signed[0] == 5
    assert (adr + ArrayItemsOffset(A)).char[3] == '*'
    (adr + ArrayItemsOffset(A)).char[3] = '+'
    assert a[3] == '+'
    adr1000 = (adr + ArrayItemsOffset(A) + ItemOffset(lltype.Char, 1000))
    assert adr1000.char[-997] == '+'

    T = lltype.FixedSizeArray(lltype.Char, 10)
    S = lltype.GcStruct('S', ('z', lltype.Ptr(T)))
    s = lltype.malloc(S)
    s.z = lltype.malloc(T, immortal=True)
    adr = cast_ptr_to_adr(s)
    assert (adr + offsetof(S, 'z')).address[0] == cast_ptr_to_adr(s.z)
    (adr + offsetof(S, 'z')).address[0] = NULL
    assert s.z == lltype.nullptr(T)
    t = lltype.malloc(T, immortal=True)
    (adr + offsetof(S, 'z')).address[0] = cast_ptr_to_adr(t)
    assert s.z == t

def test_fakeadr_eq():
    S = lltype.GcStruct("S", ("x", lltype.Signed), ("y", lltype.Signed))
    s = lltype.malloc(S)

    assert cast_ptr_to_adr(s) == cast_ptr_to_adr(s)

    adr1 = cast_ptr_to_adr(s) + FieldOffset(S, "x")
    adr2 = cast_ptr_to_adr(s) + FieldOffset(S, "y")
    adr3 = cast_ptr_to_adr(s) + FieldOffset(S, "y")
    assert adr1 != adr2
    assert adr2 == adr3

    A = lltype.GcArray(lltype.Char)
    a = lltype.malloc(A, 5)
    adr1 = cast_ptr_to_adr(a) + ArrayLengthOffset(A)
    adr2 = cast_ptr_to_adr(a) + ArrayLengthOffset(A)
    assert adr1 == adr2

    adr1 = cast_ptr_to_adr(a) + ArrayItemsOffset(A)
    adr2 = cast_ptr_to_adr(a) + ArrayItemsOffset(A)
    assert adr1 == adr2
    adr2 += ItemOffset(lltype.Char, 0)
    assert adr1 == adr2

    adr1 += ItemOffset(lltype.Char, 2)
    adr2 += ItemOffset(lltype.Char, 3)
    assert adr1 != adr2
    adr2 += ItemOffset(lltype.Char, -1)
    assert adr1 == adr2

def test_cast_subarray_pointer():
    for a in [lltype.malloc(lltype.GcArray(lltype.Signed), 5),
              lltype.malloc(lltype.FixedSizeArray(lltype.Signed, 5),
                            immortal=True)]:
        A = lltype.typeOf(a).TO
        SUBARRAY = lltype.FixedSizeArray(lltype.Signed, 1)
        a[3] = 132
        adr = cast_ptr_to_adr(a) + itemoffsetof(A, 3)
        subarray = cast_adr_to_ptr(adr, lltype.Ptr(SUBARRAY))
        assert subarray[0] == 132
        subarray[0] += 2
        assert a[3] == 134

def test_cast_structfield_pointer():
    S = lltype.GcStruct('S', ('x', lltype.Signed), ('y', lltype.Signed))
    s = lltype.malloc(S)
    SUBARRAY = lltype.FixedSizeArray(lltype.Signed, 1)
    adr = cast_ptr_to_adr(s) + offsetof(S, 'y')
    subarray = cast_adr_to_ptr(adr, lltype.Ptr(SUBARRAY))
    subarray[0] = 121
    assert s.y == 121

def test_opaque():
    S = lltype.GcStruct('S', ('x', lltype.Signed), ('y', lltype.Signed))
    O = lltype.GcOpaqueType('O')
    s = lltype.malloc(S)
    adr = cast_ptr_to_adr(s)
    o = cast_adr_to_ptr(adr, lltype.Ptr(O))
    assert lltype.cast_opaque_ptr(lltype.Ptr(S), o) == s
    adr2 = cast_ptr_to_adr(o)
    s2 = cast_adr_to_ptr(adr2, lltype.Ptr(S))
    assert s2 == s

def test_raw_malloc_struct():
    T = lltype.GcStruct('T', ('z', lltype.Signed))
    S = lltype.Struct('S', ('x', lltype.Signed), ('y', lltype.Ptr(T)))
    adr = raw_malloc(sizeof(S))
    s = cast_adr_to_ptr(adr, lltype.Ptr(S))
    py.test.raises(lltype.UninitializedMemoryAccess, "s.x")
    raw_memclear(adr, sizeof(S))
    assert s.x == 0
    assert lltype.typeOf(s) == lltype.Ptr(S)
    s.x = 123
    x_adr = adr + offsetof(S, 'x')
    assert x_adr.signed[0] == 123
    x_adr.signed[0] = 124
    assert s.x == 124

def test_llinterp_raw_malloc_struct():
    T = lltype.GcStruct('T', ('z', lltype.Signed))
    S = lltype.Struct('S', ('x', lltype.Signed), ('y', lltype.Ptr(T)))

    from pypy.rpython.memory import lladdress # GRUMBLE!

    size = sizeof(S)

    def test_read_uninit():
        adr = lladdress.raw_malloc(size)
        s = cast_adr_to_ptr(adr, lltype.Ptr(S))
        return s.x
    py.test.raises(lltype.UninitializedMemoryAccess, "interpret(test_read_uninit, [])")
    def test_read_init():
        adr = lladdress.raw_malloc(size)
        lladdress.raw_memclear(adr, size)
        s = cast_adr_to_ptr(adr, lltype.Ptr(S))
        return s.x
    res = interpret(test_read_init, [])
    assert res == 0


def test_raw_malloc_signed():
    adr = raw_malloc(sizeof(lltype.Signed))
    p = cast_adr_to_ptr(adr,
                        lltype.Ptr(lltype.FixedSizeArray(lltype.Signed, 1)))
    p[0] = 123
    assert adr.signed[0] == 123
    adr.signed[0] = 124
    assert p[0] == 124
    py.test.raises(IndexError, "adr.signed[-1]")
    py.test.raises(IndexError, "adr.signed[1]")

def test_raw_malloc_access():
    S = lltype.GcStruct("S", ('x', lltype.Signed))
    T = lltype.GcStruct("T", ('y', lltype.Signed), ('s', lltype.Ptr(S)))
    # regular malloc zeros GC pointers
    p_t = lltype.malloc(T)
    assert p_t.s == lltype.nullptr(S)
    # raw malloc does not
    p_raw_t = lltype.malloc(T, flavor="raw")
    py.test.raises(lltype.UninitializedMemoryAccess, "p_raw_t.s")
    # this sort of raw_malloc too
    p_raw_t = cast_adr_to_ptr(raw_malloc(sizeof(T)), lltype.Ptr(T))
    py.test.raises(lltype.UninitializedMemoryAccess, "p_raw_t.s")
    

def test_raw_malloc_signed_bunch():
    adr = raw_malloc(sizeof(lltype.Signed) * 50)
    p = cast_adr_to_ptr(adr,
                        lltype.Ptr(lltype.FixedSizeArray(lltype.Signed, 1)))
    for i in range(50):
        p[i] = 123 + i
        assert adr.signed[i] == 123 + i
        adr.signed[i] = 124 - i
        assert p[i] == 124 - i
    py.test.raises(IndexError, "adr.signed[50]")

def test_raw_malloc_array():
    A = lltype.Array(lltype.Signed)
    adr = raw_malloc(sizeof(A, 50))
    length_adr = adr + ArrayLengthOffset(A)
    length_adr.signed[0] = 50
    p = cast_adr_to_ptr(adr, lltype.Ptr(A))
    assert len(p) == 50
    for i in range(50):
        item_adr = adr + itemoffsetof(A, i)
        p[i] = 123 + i
        assert item_adr.signed[0] == 123 + i
        item_adr.signed[0] = 124 - i
        assert p[i] == 124 - i
    item_adr = adr + itemoffsetof(A, 50)
    py.test.raises(IndexError, "item_adr.signed[0]")

def test_raw_malloc_gcstruct():
    from pypy.rpython.memory import gcheader
    HDR = lltype.Struct('header', ('a', lltype.Signed))
    builder = gcheader.GCHeaderBuilder(HDR)
    gchdr = builder.size_gc_header
    S = lltype.GcStruct('S', ('x', lltype.Signed))

    def allocate():
        adr = raw_malloc(gchdr + sizeof(S))
        p = cast_adr_to_ptr(adr, lltype.Ptr(HDR))
        p.a = -21
        adr = cast_ptr_to_adr(p)
        sadr = adr + gchdr
        s = cast_adr_to_ptr(sadr, lltype.Ptr(S))
        s.x = 123
        assert (sadr+offsetof(S, 'x')).signed[0] == 123
        (sadr+offsetof(S, 'x')).signed[0] = 125
        assert s.x == 125
        return s

    s = allocate()
    adr = cast_ptr_to_adr(s) - gchdr
    p = cast_adr_to_ptr(adr, lltype.Ptr(HDR))
    assert p.a == -21

def test_raw_malloc_varsize():
    A = lltype.Array(lltype.Signed)
    S = lltype.Struct('S', ('x', lltype.Signed), ('y', A))
    adr = raw_malloc(offsetof(S, 'y') + itemoffsetof(A, 10))
    length_adr = adr + offsetof(S, 'y') + ArrayLengthOffset(A)
    length_adr.signed[0] = 10

    p = cast_adr_to_ptr(adr, lltype.Ptr(S))
    p.y[7] = 5
    assert (adr + offsetof(S, 'y') + itemoffsetof(A, 7)).signed[0] == 5
    (adr + offsetof(S, 'y') + itemoffsetof(A, 7)).signed[0] = 18187
    assert p.y[7] == 18187
    py.test.raises(IndexError,
                   "(adr + offsetof(S, 'y') + itemoffsetof(A, 10)).signed[0]")

def test_raw_free():
    A = lltype.GcArray(lltype.Signed)
    adr = raw_malloc(sizeof(A, 10))
    p_a = cast_adr_to_ptr(adr, lltype.Ptr(A))
    p_a[0] = 1
    raw_free(adr)
    py.test.raises(RuntimeError, "p_a[0]")
    py.test.raises(RuntimeError, "p_a[0] = 2")
    repr(adr)
    str(p_a)

    S = lltype.GcStruct('S', ('x', lltype.Signed))
    adr = raw_malloc(sizeof(S))
    p_s = cast_adr_to_ptr(adr, lltype.Ptr(S))
    p_s.x = 1
    raw_free(adr)
    py.test.raises(RuntimeError, "p_s.x")
    py.test.raises(RuntimeError, "p_s.x = 2")
    repr(adr)
    str(p_s)
    
    T = lltype.GcStruct('T', ('s', S))
    adr = raw_malloc(sizeof(T))
    p_s = cast_adr_to_ptr(adr, lltype.Ptr(S))
    p_s.x = 1
    raw_free(adr)
    py.test.raises(RuntimeError, "p_s.x")
    py.test.raises(RuntimeError, "p_s.x = 2")
    repr(adr)
    str(p_s)
    
    U = lltype.Struct('U', ('y', lltype.Signed))
    T = lltype.GcStruct('T', ('x', lltype.Signed), ('u', U))
    adr = raw_malloc(sizeof(T))
    p_t = cast_adr_to_ptr(adr, lltype.Ptr(T))
    p_u = p_t.u
    p_u.y = 1
    raw_free(adr)
    py.test.raises(RuntimeError, "p_u.y")
    py.test.raises(RuntimeError, "p_u.y = 2")
    repr(adr)
    str(p_u)

def test_raw_free_with_hdr():
    from pypy.rpython.memory.gcheader import GCHeaderBuilder
    
    HDR = lltype.Struct('h', ('t', lltype.Signed))
    gh = GCHeaderBuilder(HDR).size_gc_header
    
    A = lltype.GcArray(lltype.Signed)
    adr = raw_malloc(gh+sizeof(A, 10))
    p_a = cast_adr_to_ptr(adr+gh, lltype.Ptr(A))
    p_a[0] = 1
    adr = cast_ptr_to_adr(p_a)-gh
    raw_free(adr)
    py.test.raises(RuntimeError, "p_a[0]")
    py.test.raises(RuntimeError, "p_a[0] = 2")
    repr(adr)
    str(p_a)

    S = lltype.GcStruct('S', ('x', lltype.Signed))
    adr = raw_malloc(gh+sizeof(S))
    p_s = cast_adr_to_ptr(adr+gh, lltype.Ptr(S))
    p_s.x = 1
    adr = cast_ptr_to_adr(p_s)-gh
    raw_free(adr)
    py.test.raises(RuntimeError, "p_s.x")
    py.test.raises(RuntimeError, "p_s.x = 2")
    repr(adr)
    str(p_s)
    
    T = lltype.GcStruct('T', ('s', S))
    adr = raw_malloc(gh+sizeof(T))
    p_s = cast_adr_to_ptr(adr+gh, lltype.Ptr(S))
    p_s.x = 1
    adr = cast_ptr_to_adr(p_s)-gh
    raw_free(adr)
    py.test.raises(RuntimeError, "p_s.x")
    py.test.raises(RuntimeError, "p_s.x = 2")
    repr(adr)
    str(p_s)
    
    U = lltype.Struct('U', ('y', lltype.Signed))
    T = lltype.GcStruct('T', ('x', lltype.Signed), ('u', U))
    adr = raw_malloc(gh+sizeof(T))
    p_t = cast_adr_to_ptr(adr+gh, lltype.Ptr(T))
    p_u = p_t.u
    p_u.y = 1
    adr = cast_ptr_to_adr(p_t)-gh
    raw_free(adr)
    py.test.raises(RuntimeError, "p_u.y")
    py.test.raises(RuntimeError, "p_u.y = 2")
    repr(adr)
    str(p_u)

def test_raw_memcopy():
    T = lltype.GcStruct('T', ('x', lltype.Signed))
    t1 = lltype.malloc(T)
    t2 = lltype.malloc(T)
    t1.x = 1
    t2.x = 2
    at1 = cast_ptr_to_adr(t1)
    at2 = cast_ptr_to_adr(t2)
    raw_memcopy(at1, at2, sizeof(T))
    assert t2.x == 1

def test_raw_memcopy_nonrec():
    T = lltype.GcStruct('T', ('x', lltype.Signed))
    A = lltype.FixedSizeArray(lltype.Ptr(T), 1)
    t1 = lltype.malloc(T)
    t2 = lltype.malloc(T)
    t1.x = 1
    t2.x = 2

    at1 = raw_malloc(sizeof(A))
    at2 = raw_malloc(sizeof(A))
    p1 = cast_adr_to_ptr(at1, lltype.Ptr(A))
    p2 = cast_adr_to_ptr(at2, lltype.Ptr(A))
    p1[0] = t1
    p2[0] = t2
    raw_memcopy(at1, at2, sizeof(A))
    assert p1[0] == t1
    assert p2[0] == t1
    assert t1.x == 1    #   not
    assert t2.x == 2    # modified

def test_inlined_substruct():
    T = lltype.Struct('T', ('x', lltype.Signed))
    S1 = lltype.GcStruct('S1', ('t1', T), ('t2', T))
    S = lltype.GcStruct('S', ('header', S1), ('t', T))

    s = lltype.malloc(S)
    s.header.t1.x = 1
    s.header.t2.x = 2
    s.t.x = 3

    for adr in [cast_ptr_to_adr(s), cast_ptr_to_adr(s.header)]:
        assert (adr + offsetof(S, 'header')
                    + offsetof(S1, 't1')
                    + offsetof(T, 'x')).signed[0] == 1
        assert (adr + offsetof(S1, 't1')
                    + offsetof(T, 'x')).signed[0] == 1
        assert (adr + offsetof(S1, 't2')
                    + offsetof(T, 'x')).signed[0] == 2
        assert (adr + offsetof(S, 't')
                    + offsetof(T, 'x')).signed[0] == 3

def test_arena_bump_ptr():
    S = lltype.Struct('S', ('x',lltype.Signed))
    SPTR = lltype.Ptr(S)
    badr = start = raw_malloc(arena(S, 4))
    s_adr = badr
    badr = bump(badr, sizeof(S))
    s_ptr = cast_adr_to_ptr(s_adr, SPTR)
    s_ptr.x = 1
    s2_adr = badr
    badr = bump(badr, sizeof(S))
    s2_ptr = cast_adr_to_ptr(s2_adr, SPTR)
    s2_ptr.x = 2
    badr = start
    s_ptr = cast_adr_to_ptr(badr, SPTR)
    assert s_ptr.x == 1
    badr = bump(badr, sizeof(S))
    s2_ptr = cast_adr_to_ptr(badr, SPTR)
    assert s2_ptr.x == 2
    # release(start)

class TestWeakAddressLLinterp(object):
    def test_null(self):
        from pypy.rlib.objectmodel import cast_weakgcaddress_to_object
        from pypy.rlib.objectmodel import cast_object_to_weakgcaddress
        class A:
            pass
        def f():
            return cast_weakgcaddress_to_object(WEAKNULL, A) is None
        assert interpret(f, [])
    
    def test_attribute(object):
        from pypy.rlib.objectmodel import cast_weakgcaddress_to_object
        from pypy.rlib.objectmodel import cast_object_to_weakgcaddress
        class A:
            pass
        class B:
            pass
        def f(x):
            a = A()
            b = B()
            if x:
                a.addr = WEAKNULL
            else:
                a.addr = cast_object_to_weakgcaddress(b)
            return cast_weakgcaddress_to_object(a.addr, B) is b
        assert not interpret(f, [1])
        assert interpret(f, [0])
 
