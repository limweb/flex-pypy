import py
import sys
from pypy.translator.translator import TranslationContext, graphof
from pypy.rpython.lltypesystem.lltype import *
from pypy.rpython.ootypesystem import ootype
from pypy.rlib.rarithmetic import intmask
from pypy.rpython.test.tool import BaseRtypingTest, LLRtypeMixin, OORtypeMixin
from pypy.objspace.flow.model import summary

class EmptyBase(object):
    pass

class Random:
    xyzzy = 12
    yadda = 21

# for method calls
class A:
    def f(self):
        return self.g()

    def g(self):
        return 42

class B(A):
    def g(self):
        return 1

class C(B):
    pass

class BaseTestRclass(BaseRtypingTest):

    def test_instanceattr(self):
        def dummyfn():
            x = EmptyBase()
            x.a = 5
            x.a += 1
            return x.a
        res = self.interpret(dummyfn, [])
        assert res == 6

    def test_simple(self):
        def dummyfn():
            x = EmptyBase()
            return x
        res = self.interpret(dummyfn, [])
        assert self.is_of_instance_type(res)

    def test_classattr(self):
        def dummyfn():
            x = Random()
            return x.xyzzy
        res = self.interpret(dummyfn, [])
        assert res == 12

    def test_classattr_both(self):
        class A:
            a = 1
        class B(A):
            a = 2
        def pick(i):
            if i == 0:
                return A
            else:
                return B
            
        def dummyfn(i):
            C = pick(i)
            i = C()
            return C.a + i.a
        res = self.interpret(dummyfn, [0])
        assert res == 2
        res = self.interpret(dummyfn, [1])
        assert res == 4

    def test_classattr_both2(self):
        class Base(object):
            a = 0
        class A(Base):
            a = 1
        class B(Base):
            a = 2
        def pick(i):
            if i == 0:
                return A
            else:
                return B
            
        def dummyfn(i):
            C = pick(i)
            i = C()
            return C.a + i.a
        res = self.interpret(dummyfn, [0])
        assert res == 2
        res = self.interpret(dummyfn, [1])
        assert res == 4

    def test_runtime_exception(self):
        def pick(flag):
            if flag:
                return TypeError
            else:
                return ValueError
        def f(flag):
            ex = pick(flag)
            raise ex()
        self.interpret_raises(TypeError, f, [True])
        self.interpret_raises(ValueError, f, [False])

    def test_classattr_as_defaults(self):
        def dummyfn():
            x = Random()
            x.xyzzy += 1
            return x.xyzzy
        res = self.interpret(dummyfn, [])
        assert res == 13

    def test_overridden_classattr_as_defaults(self):
        class W_Root(object):
            pass
        class W_Thunk(W_Root):
            pass

        THUNK_PLACEHOLDER = W_Thunk()
        W_Root.w_thunkalias = None
        W_Thunk.w_thunkalias = THUNK_PLACEHOLDER

        def dummyfn(x):
            if x == 1:
                t = W_Thunk()
            elif x == 2:
                t = W_Thunk()
                t.w_thunkalias = W_Thunk()
            else:
                t = W_Root()
            return t.w_thunkalias is THUNK_PLACEHOLDER
        res = self.interpret(dummyfn, [1])
        assert res == True

    def test_prebuilt_instance(self):
        a = EmptyBase()
        a.x = 5
        def dummyfn():
            a.x += 1
            return a.x
        self.interpret(dummyfn, [])

    def test_recursive_prebuilt_instance(self):
        a = EmptyBase()
        b = EmptyBase()
        a.x = 5
        b.x = 6
        a.peer = b
        b.peer = a
        def dummyfn():
            return a.peer.peer.peer.x
        res = self.interpret(dummyfn, [])
        assert res == 6

    def test_recursive_prebuilt_instance_classattr(self):
        class Base:
            def m(self):
                return self.d.t.v
        class T1(Base):
            v = 3
        class T2(Base):
            v = 4
        class D:
            def _freeze_(self):
                return True

        t1 = T1()
        t2 = T2()
        T1.d = D()
        T2.d = D()
        T1.d.t = t1

        def call_meth(obj):
            return obj.m()
        def fn():
            return call_meth(t1) + call_meth(t2)
        assert self.interpret(fn, []) == 6

    def test_prebuilt_instances_with_void(self):
        def marker():
            return 42
        a = EmptyBase()
        a.nothing_special = marker
        def dummyfn():
            return a.nothing_special()
        res = self.interpret(dummyfn, [])
        assert res == 42

    def test_simple_method_call(self):
        def f(i):
            if i:
                a = A()
            else:
                a = B()
            return a.f()
        res = self.interpret(f, [True])
        assert res == 42
        res = self.interpret(f, [False])
        assert res == 1

    def test_isinstance(self):
        def f(i):
            if i == 0:
                o = None
            elif i == 1:
                o = A()
            elif i == 2:
                o = B()
            else:
                o = C()
            return 100*isinstance(o, A)+10*isinstance(o, B)+1*isinstance(o ,C)

        res = self.interpret(f, [1])
        assert res == 100
        res = self.interpret(f, [2])
        assert res == 110
        res = self.interpret(f, [3])
        assert res == 111

        res = self.interpret(f, [0])
        assert res == 0

    def test_method_used_in_subclasses_only(self):
        class A:
            def meth(self):
                return 123
        class B(A):
            pass
        def f():
            x = B()
            return x.meth()
        res = self.interpret(f, [])
        assert res == 123

    def test_method_both_A_and_B(self):
        class A:
            def meth(self):
                return 123
        class B(A):
            pass
        def f():
            a = A()
            b = B()
            return a.meth() + b.meth()
        res = self.interpret(f, [])
        assert res == 246

    def test_issubclass_type(self):
        class Abstract:
            pass
        class A(Abstract):
            pass
        class B(A):
            pass
        def f(i):
            if i == 0: 
                c1 = A()
            else: 
                c1 = B()
            return issubclass(type(c1), B)
        assert self.interpret(f, [0]) == False 
        assert self.interpret(f, [1]) == True

        def g(i):
            if i == 0: 
                c1 = A()
            else: 
                c1 = B()
            return issubclass(type(c1), A)
        assert self.interpret(g, [0]) == True
        assert self.interpret(g, [1]) == True

    def test_staticmethod(self):
        class A(object):
            f = staticmethod(lambda x, y: x*y)
        def f():
            a = A()
            return a.f(6, 7)
        res = self.interpret(f, [])
        assert res == 42

    def test_is(self):
        class A: pass
        class B(A): pass
        class C: pass
        def f(i):
            a = A()
            b = B()
            c = C()
            d = None
            e = None
            if i == 0:
                d = a
            elif i == 1:
                d = b
            elif i == 2:
                e = c
            return (0x0001*(a is b) | 0x0002*(a is c) | 0x0004*(a is d) |
                    0x0008*(a is e) | 0x0010*(b is c) | 0x0020*(b is d) |
                    0x0040*(b is e) | 0x0080*(c is d) | 0x0100*(c is e) |
                    0x0200*(d is e))
        res = self.interpret(f, [0])
        assert res == 0x0004
        res = self.interpret(f, [1])
        assert res == 0x0020
        res = self.interpret(f, [2])
        assert res == 0x0100
        res = self.interpret(f, [3])
        assert res == 0x0200

    def test_eq(self):
        class A: pass
        class B(A): pass
        class C: pass
        def f(i):
            a = A()
            b = B()
            c = C()
            d = None
            e = None
            if i == 0:
                d = a
            elif i == 1:
                d = b
            elif i == 2:
                e = c
            return (0x0001*(a == b) | 0x0002*(a == c) | 0x0004*(a == d) |
                    0x0008*(a == e) | 0x0010*(b == c) | 0x0020*(b == d) |
                    0x0040*(b == e) | 0x0080*(c == d) | 0x0100*(c == e) |
                    0x0200*(d == e))
        res = self.interpret(f, [0])
        assert res == 0x0004
        res = self.interpret(f, [1])
        assert res == 0x0020
        res = self.interpret(f, [2])
        assert res == 0x0100
        res = self.interpret(f, [3])
        assert res == 0x0200

    def test_istrue(self):
        class A:
            pass
        def f(i):
            if i == 0:
                a = A()
            else:
                a = None
            if a:
                return 1
            else:
                return 2
        res = self.interpret(f, [0])
        assert res == 1
        res = self.interpret(f, [1])
        assert res == 2

    def test_ne(self):
        class A: pass
        class B(A): pass
        class C: pass
        def f(i):
            a = A()
            b = B()
            c = C()
            d = None
            e = None
            if i == 0:
                d = a
            elif i == 1:
                d = b
            elif i == 2:
                e = c
            return (0x0001*(a != b) | 0x0002*(a != c) | 0x0004*(a != d) |
                    0x0008*(a != e) | 0x0010*(b != c) | 0x0020*(b != d) |
                    0x0040*(b != e) | 0x0080*(c != d) | 0x0100*(c != e) |
                    0x0200*(d != e))
        res = self.interpret(f, [0])
        assert res == ~0x0004 & 0x3ff
        res = self.interpret(f, [1])
        assert res == ~0x0020 & 0x3ff
        res = self.interpret(f, [2])
        assert res == ~0x0100 & 0x3ff
        res = self.interpret(f, [3])
        assert res == ~0x0200 & 0x3ff

    def test_hash_preservation(self):
        class C:
            pass
        class D(C):
            pass
        c = C()
        d = D()
        def f():
            d2 = D()
            # xxx check for this CPython peculiarity for now:
            x = (hash(d2) & sys.maxint) == (id(d2) & sys.maxint)
            return x, hash(c)+hash(d)

        res = self.interpret(f, [])

        assert res.item0 == True
        assert res.item1 == intmask(hash(c)+hash(d))
        
    def test_type(self):
        class A:
            pass
        class B(A):
            pass
        def g(a):
            return type(a)
        def f(i):
            if i > 0:
                a = A()
            elif i < 0:
                a = B()
            else:
                a = None
            return g(a) is A    # should type(None) work?  returns None for now
        res = self.interpret(f, [1])
        assert res is True
        res = self.interpret(f, [-1])
        assert res is False
        res = self.interpret(f, [0])
        assert res is False

    def test_type_of_constant(self):
        class A:
            pass
        a = A()

        def f():
            return type(a) is A
        
        res = self.interpret(f, [])
        
        
    def test_void_fnptr(self):
        def g():
            return 42
        def f():
            e = EmptyBase()
            e.attr = g
            return e.attr()
        res = self.interpret(f, [])
        assert res == 42

    def test_getattr_on_classes(self):
        class A:
            def meth(self):
                return self.value + 42
        class B(A):
            def meth(self):
                shouldnt**be**seen
        class C(B):
            def meth(self):
                return self.value - 1
        def pick_class(i):
            if i > 0:
                return A
            else:
                return C
        def f(i):
            meth = pick_class(i).meth
            x = C()
            x.value = 12
            return meth(x)   # calls A.meth or C.meth, completely ignores B.meth
        res = self.interpret(f, [1])
        assert res == 54
        res = self.interpret(f, [0])
        assert res == 11

    def test_constant_bound_method(self):
        class C:
            value = 1
            def meth(self):
                return self.value
        meth = C().meth
        def f():
            return meth()
        res = self.interpret(f, [])
        assert res == 1

    def test_mixin(self):
        class Mixin(object):
            _mixin_ = True

            def m(self, v):
                return v

        class Base(object):
            pass

        class A(Base, Mixin):
            pass

        class B(Base, Mixin):
            pass

        class C(B):
            pass

        def f():
            a = A()
            v0 = a.m(2)
            b = B()
            v1 = b.m('x')
            c = C()
            v2 = c.m('y')
            return v0, v1, v2

        res = self.interpret(f, [])
        assert typeOf(res.item0) == Signed

    def test___class___attribute(self):
        class Base(object): pass
        class A(Base): pass
        class B(Base): pass
        class C(A): pass
        def seelater():
            C()
        def f(n):
            if n == 1:
                x = A()
            else:
                x = B()
            y = B()
            result = x.__class__, y.__class__
            seelater()
            return result
        def g():
            cls1, cls2 = f(1)
            return cls1 is A, cls2 is B

        res = self.interpret(g, [])
        assert res.item0
        assert res.item1


    def test_common_class_attribute(self):
        class A:
            def meth(self):
                return self.x
        class B(A):
            x = 42
        class C(A):
            x = 43
        def call_meth(a):
            return a.meth()
        def f():
            b = B()
            c = C()
            return call_meth(b) + call_meth(c)
        assert self.interpret(f, []) == 85

    def test_default_attribute_non_primitive(self):
        class A:
            x = (1, 2)
        def f():
            a = A()
            a.x = (3, 4)
            return a.x[0]
        assert self.interpret(f, []) == 3

    def test_filter_unreachable_methods(self):
        # this creates a family with 20 unreachable methods m(), all
        # hidden by a 21st method m().
        class Base:
            pass
        prev = Base
        for i in range(20):
            class Intermediate(prev):
                def m(self, value=i):
                    return value
            prev = Intermediate
        class Final(prev):
            def m(self):
                return -7
        def f():
            return Final().m()
        res = self.interpret(f, [])
        assert res == -7


class TestLltype(BaseTestRclass, LLRtypeMixin):

    def test__del__(self):
        class A(object):
            def __init__(self):
                self.a = 2
            def __del__(self):
                self.a = 3
        def f():
            a = A()
            return a.a
        t = TranslationContext()
        t.buildannotator().build_types(f, [])
        t.buildrtyper().specialize()
        graph = graphof(t, f)
        TYPE = graph.startblock.operations[0].args[0].value
        RTTI = getRuntimeTypeInfo(TYPE)
        queryptr = RTTI._obj.query_funcptr # should not raise
        destrptr = RTTI._obj.destructor_funcptr
        assert destrptr is not None
    
    def test_del_inheritance(self):
        class State:
            pass
        s = State()
        s.a_dels = 0
        s.b_dels = 0
        class A(object):
            def __del__(self):
                s.a_dels += 1
        class B(A):
            def __del__(self):
                s.b_dels += 1
        class C(A):
            pass
        def f():
            A()
            B()
            C()
            A()
            B()
            C()
            return s.a_dels * 10 + s.b_dels
        res = f()
        assert res == 42
        t = TranslationContext()
        t.buildannotator().build_types(f, [])
        t.buildrtyper().specialize()
        graph = graphof(t, f)
        TYPEA = graph.startblock.operations[0].args[0].value
        RTTIA = getRuntimeTypeInfo(TYPEA)
        TYPEB = graph.startblock.operations[3].args[0].value
        RTTIB = getRuntimeTypeInfo(TYPEB)
        TYPEC = graph.startblock.operations[6].args[0].value
        RTTIC = getRuntimeTypeInfo(TYPEC)
        queryptra = RTTIA._obj.query_funcptr # should not raise
        queryptrb = RTTIB._obj.query_funcptr # should not raise
        queryptrc = RTTIC._obj.query_funcptr # should not raise
        destrptra = RTTIA._obj.destructor_funcptr
        destrptrb = RTTIB._obj.destructor_funcptr
        destrptrc = RTTIC._obj.destructor_funcptr
        assert destrptra == destrptrc
        assert typeOf(destrptra).TO.ARGS[0] != typeOf(destrptrb).TO.ARGS[0]
        assert destrptra is not None
        assert destrptrb is not None

    def test_immutable(self):
        class I(object):
            _immutable_ = True
            
            def __init__(self, v):
                self.v = v

        i = I(3)
        def f():
            return i.v

        t, typer, graph = self.gengraph(f, [], backendopt=True)
        assert summary(graph) == {}

    def test_instance_repr(self):
        class FooBar(object):
            pass
        def f():
            x = FooBar()
            return id(x), str(x)

        res = self.interpret(f, [])
        xid, xstr = self.ll_unpack_tuple(res, 2)
        xstr = self.ll_to_string(xstr)
        print xid, xstr
        assert 'FooBar' in xstr
        from pypy.rlib.rarithmetic import r_uint
        expected = hex(r_uint(xid)).lower().replace('l', '')
        assert expected in xstr


class TestOOtype(BaseTestRclass, OORtypeMixin):

    def test__del__(self):
        class A(object):
            def __init__(self):
                self.a = 2
            def __del__(self):
                self.a = 3
        def f():
            a = A()
            return a.a
        t = TranslationContext()
        t.buildannotator().build_types(f, [])
        t.buildrtyper(type_system=self.type_system).specialize()
        graph = graphof(t, f)
        TYPE = graph.startblock.operations[0].args[0].value
        _, meth = TYPE._lookup("o__del__")
        assert meth.finalizer

    def test_del_inheritance(self):
        class State:
            pass
        s = State()
        s.a_dels = 0
        s.b_dels = 0
        class A(object):
            def __del__(self):
                s.a_dels += 1
        class B(A):
            def __del__(self):
                s.b_dels += 1
        class C(A):
            pass
        def f():
            A()
            B()
            C()
            A()
            B()
            C()
            return s.a_dels * 10 + s.b_dels
        res = f()
        assert res == 42
        t = TranslationContext()
        t.buildannotator().build_types(f, [])
        t.buildrtyper(type_system=self.type_system).specialize()
        graph = graphof(t, f)
        TYPEA = graph.startblock.operations[0].args[0].value
        TYPEB = graph.startblock.operations[2].args[0].value
        TYPEC = graph.startblock.operations[4].args[0].value
        _, destra = TYPEA._lookup("o__del__")
        _, destrb = TYPEB._lookup("o__del__")
        _, destrc = TYPEC._lookup("o__del__")
        assert destra == destrc
        assert destrb is not None
        assert destra is not None
