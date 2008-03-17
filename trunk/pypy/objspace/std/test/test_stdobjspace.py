from pypy.interpreter.error import OperationError



class TestW_StdObjSpace:

    def test_wrap_wrap(self):
        raises(TypeError,
                          self.space.wrap,
                          self.space.wrap(0))

    def test_str_w_non_str(self):
        raises(OperationError,self.space.str_w,self.space.wrap(None))
        raises(OperationError,self.space.str_w,self.space.wrap(0))

    def test_int_w_non_int(self):
        raises(OperationError,self.space.int_w,self.space.wrap(None))
        raises(OperationError,self.space.int_w,self.space.wrap(""))        

    def test_uint_w_non_int(self):
        raises(OperationError,self.space.uint_w,self.space.wrap(None))
        raises(OperationError,self.space.uint_w,self.space.wrap(""))        

    def test_multimethods_defined_on(self):
        from pypy.objspace.std.stdtypedef import multimethods_defined_on
        from pypy.objspace.std.listobject import W_ListObject
        res = multimethods_defined_on(W_ListObject)
        res = [(m.name, local) for (m, local) in res]
        assert ('add', False) in res
        assert ('lt', False) in res
        assert ('setitem', False) in res
        assert ('mod', False) not in res
        assert ('pop', True) in res
        assert ('reverse', True) in res
        assert ('popitem', True) not in res
