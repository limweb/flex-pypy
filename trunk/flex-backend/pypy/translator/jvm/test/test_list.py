import py
from pypy.translator.jvm.test.runtest import JvmTest
from pypy.rpython.test.test_rlist import BaseTestRlist

class TestJvmList(JvmTest, BaseTestRlist):
    #def test_recursive(self):
    #    py.test.skip("JVM doesn't support recursive lists")
    #
    def test_getitem_exc(self):
        py.test.skip('fixme!')
