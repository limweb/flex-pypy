from pypy.rpython.extfunc import genericcallable, register_external
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc


def flexTrace(s):
    pass

def trace(s):
    pass

register_external(flexTrace, args=[str], export_name="_consts_0.flexTrace")
register_external(trace, args=[str], export_name="trace")

