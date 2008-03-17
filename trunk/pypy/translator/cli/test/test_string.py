import py
from pypy.translator.cli.test.runtest import CliTest
import pypy.translator.oosupport.test_template.string as oostring

class TestCliString(CliTest, oostring.BaseTestString):

    EMPTY_STRING_HASH = 0

    def test_unichar_const(self):
        py.test.skip("CLI interpret doesn't support unicode for input arguments")
    test_unichar_eq = test_unichar_const
    test_unichar_ord = test_unichar_const
    test_unichar_hash = test_unichar_const
    test_char_unichar_eq = test_unichar_const
    test_char_unichar_eq_2 = test_unichar_const

    def test_upper(self):
        py.test.skip("CLI doens't support backquotes inside string literals")
    test_lower = test_upper

    def test_hlstr(self):
        py.test.skip("CLI tests can't have string as input arguments")

    def test_getitem_exc(self):
        py.test.skip('fixme!')

