import py
from pypy.translator.lisp.buildcl import make_cl_func, generate_cl_code

def test_simple():
    class C:
        pass
    def new_get_set():
        obj = C()
        obj.answer = 42
        return obj.answer
    cl_new_get_set = make_cl_func(new_get_set)
    assert cl_new_get_set() == 42

def test_inc():
    class IntHolder:
        def __init__(self, number):
            self.number = number
        def inc(self):
            self.number += 1
        def get(self):
            return self.number
    def inc(number):
        obj = IntHolder(number)
        obj.inc()
        return obj.get()
    cl_inc = make_cl_func(inc, [int])
    assert cl_inc(5) == 6

def test_method_twice():
    class IntHolder:
        def __init__(self, number):
            self.number = number
        def inc(self):
            self.number += 1
        def get(self):
            return self.number
    def inc_two(number):
        obj = IntHolder(number)
        obj.inc()
        obj.inc()
        return obj.get()
    code = generate_cl_code(inc_two, [int])
    methodcount = code.count("defmethod")
    assert methodcount == 3

def test_inheritance():
    class Foo:
        pass
    class Bar(Foo):
        pass
    def check_inheritance():
        Bar()
    code = generate_cl_code(check_inheritance)
    classcount = code.count("defclass")
    # Divide by two to get rid of meta hierarchy
    # Minus one to get rid of Object
    realcount = (classcount / 2) - 1
    assert realcount == 2

def test_isinstance():
    class Foo:
        pass
    class Bar(Foo):
        pass
    class Baz(Foo):
        pass
    def check_isinstance(flag):
        if flag:
            obj = Bar()
        else:
            obj = Baz()
        return isinstance(obj, Bar)
    cl_check_isinstance = make_cl_func(check_isinstance, [bool])
    assert cl_check_isinstance(True) == True
    assert cl_check_isinstance(False) == False

def test_class_variable():
    class Foo:
        value = 0
    class Bar(Foo):
        value = 1
    class Baz(Foo):
        value = 2
    def pick_class(flag):
        if flag:
            return Bar
        else:
            return Baz
    def dynamic_class(flag):
        cls = pick_class(flag)
        return cls.value
    cl_dynamic_class = make_cl_func(dynamic_class, [bool])
    assert cl_dynamic_class(True) == 1
    assert cl_dynamic_class(False) == 2

def test_runtime_new():
    class Foo:
        pass
    class Bar(Foo):
        pass
    class Baz(Foo):
        pass
    def pick_class(flag):
        if flag:
            return Bar
        else:
            return Baz
    def runtime_new(flag):
        cls = pick_class(flag)
        cls()
        return True
    cl_runtime_new = make_cl_func(runtime_new, [bool])
    assert cl_runtime_new(True)
    assert cl_runtime_new(False)

def test_instance_variable():
    class Foo:
        value = 0
    class Bar(Foo):
        value = 1
    class Baz(Foo):
        value = 2
    def pick_class(flag):
        if flag:
            return Bar
        else:
            return Baz
    def dynamic_instance(flag):
        cls = pick_class(flag)
        obj = cls()
        return obj.value
    cl_dynamic_instance = make_cl_func(dynamic_instance, [bool])
    assert cl_dynamic_instance(True) == 1
    assert cl_dynamic_instance(False) == 2

def test_nullable():
    class Foo:
        def __init__(self, value):
            self.value = value
    def maybe_foo(flag):
        if flag:
            return Foo(1)
        else:
            return None
    def maybe_one(flag):
        obj = maybe_foo(flag)
        if obj is None:
            obj = Foo(2)
        return obj.value
    cl_maybe_one = make_cl_func(maybe_one, [bool])
    assert cl_maybe_one(True) == 1
    assert cl_maybe_one(False) == 2
