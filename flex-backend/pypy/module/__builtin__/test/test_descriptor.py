import autopath


class AppTestBuiltinApp:
    def test_staticmethod(self):
        class C:
            def f(a, b):
                return a+b
            f = staticmethod(f)
        class D(C):
            pass

        c = C()
        d = D()
        assert c.f("abc", "def") == "abcdef"
        assert C.f("abc", "def") == "abcdef"
        assert d.f("abc", "def") == "abcdef"
        assert D.f("abc", "def") == "abcdef"

    def test_classmethod(self):
        class C:
            def f(cls, stuff):
                return cls, stuff
            f = classmethod(f)
        class D(C):
            pass

        c = C()
        d = D()
        assert c.f("abc") == (C, "abc")
        assert C.f("abc") == (C, "abc")
        assert d.f("abc") == (D, "abc")
        assert D.f("abc") == (D, "abc")

    def test_property_simple(self):
        
        class a(object):
            def _get(self): return 42
            def _set(self, value): raise AttributeError
            def _del(self): raise KeyError
            name = property(_get, _set, _del)
        a1 = a()
        assert a1.name == 42
        raises(AttributeError, setattr, a1, 'name', 42)
        raises(KeyError, delattr, a1, 'name')

    def test_super(self):
        class A(object):
            def f(self):
                return 'A'
        class B(A):
            def f(self):
                return 'B' + super(B,self).f()
        class C(A):
            def f(self):
                return 'C' + super(C,self).f()
        class D(B, C):
            def f(self):
                return 'D' + super(D,self).f()
        d = D()
        assert d.f() == "DBCA"
        assert D.__mro__ == (D, B, C, A, object)

    def test_super_metaclass(self):
        class xtype(type):
            def __init__(self, name, bases, dict):
                super(xtype, self).__init__(name, bases, dict)
        A = xtype('A', (), {})
        assert isinstance(A, xtype)
        a = A()
        assert isinstance(a, A)

    def test_super_classmethod(self):
        class A(object):
            def f(cls):
                return cls
            f = classmethod(f)
        class B(A):
            def f(cls):
                return [cls, super(B, cls).f()]
            f = classmethod(f)
        assert B().f() == [B, B]
