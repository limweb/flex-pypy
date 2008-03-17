import py
from pypy.translator.c.test.test_typed import TestTypedTestCase as _TestTypedTestCase
from pypy.translator.backendopt.all import backend_optimizations
from pypy.rlib.rarithmetic import r_uint, r_longlong, r_ulonglong
from pypy import conftest

class TestTypedOptimizedTestCase(_TestTypedTestCase):

    def process(self, t):
        _TestTypedTestCase.process(self, t)
        self.t = t
        backend_optimizations(t, merge_if_blocks=False)
        if conftest.option.view:
            t.view()

    def test_remove_same_as(self):
        def f(n):
            if bool(bool(bool(n))):
                return 123
            else:
                return 456
        fn = self.getcompiled(f, [bool])
        assert f(True) == 123
        assert f(False) == 456

    def test__del__(self):
        import os
        class B(object):
            pass
        b = B()
        b.nextid = 0
        b.num_deleted = 0
        class A(object):
            def __init__(self):
                self.id = b.nextid
                b.nextid += 1

            def __del__(self):
                b.num_deleted += 1

        def f(x):
            a = A()
            for i in range(x):
                a = A()
            return b.num_deleted

        fn = self.getcompiled(f, [int])
        res = f(5)
        assert res == 5
        res = fn(5)
        # translated function loses its last reference earlier
        assert res == 6
    
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
        def f(x):
            A()
            B()
            C()
            A()
            B()
            C()
            if x:
                return s.a_dels * 10 + s.b_dels
            else:
                return -1
        fn = self.getcompiled(f, [int])
        res = f(1)
        assert res == 42
        res = fn(1)
        assert res == 42

class TestTypedOptimizedSwitchTestCase:

    class CodeGenerator(_TestTypedTestCase):
        def process(self, t):
            _TestTypedTestCase.process(self, t)
            self.t = t
            backend_optimizations(t, merge_if_blocks=True)

    def test_int_switch(self):
        def f(x):
            if x == 3:
                return 9
            elif x == 9:
                return 27
            elif x == 27:
                return 3
            return 0
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [int])
        for x in (0,1,2,3,9,27,48, -9):
            assert fn(x) == f(x)

    def test_uint_switch(self):
        def f(x):
            if x == r_uint(3):
                return 9
            elif x == r_uint(9):
                return 27
            elif x == r_uint(27):
                return 3
            return 0
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [r_uint])
        for x in (0,1,2,3,9,27,48):
            assert fn(x) == f(x)

    def test_longlong_switch(self):
        def f(x):
            if x == r_longlong(3):
                return 9
            elif x == r_longlong(9):
                return 27
            elif x == r_longlong(27):
                return 3
            return 0
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [r_longlong])
        for x in (0,1,2,3,9,27,48, -9):
            assert fn(x) == f(x)

    def test_ulonglong_switch(self):
        def f(x):
            if x == r_ulonglong(3):
                return 9
            elif x == r_ulonglong(9):
                return 27
            elif x == r_ulonglong(27):
                return 3
            return 0
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [r_ulonglong])
        for x in (0,1,2,3,9,27,48, r_ulonglong(-9)):
            assert fn(x) == f(x)

    def test_chr_switch(self):
        def f(y):
            x = chr(y)
            if x == 'a':
                return 'b'
            elif x == 'b':
                return 'c'
            elif x == 'c':
                return 'd'
            return '@'
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [int])
        for x in 'ABCabc@':
            y = ord(x)
            assert fn(y) == f(y)

    def test_unichr_switch(self):
        def f(y):
            x = unichr(y)
            if x == u'a':
                return 'b'
            elif x == u'b':
                return 'c'
            elif x == u'c':
                return 'd'
            return '@'
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [int])
        for x in u'ABCabc@':
            y = ord(x)
            assert fn(y) == f(y)


class TestTypedOptimizedRaisingOps:

    class CodeGenerator(_TestTypedTestCase):
        def process(self, t):
            _TestTypedTestCase.process(self, t)
            self.t = t
            backend_optimizations(t, raisingop2direct_call=True)

    def test_int_floordiv_zer(self):
        def f(x):
            try:
                y = 123 / x
            except:
                y = 456
            return y
        codegenerator = self.CodeGenerator()
        fn = codegenerator.getcompiled(f, [int])
        for x in (0,1,2,3,9,27,48, -9):
            assert fn(x) == f(x)
