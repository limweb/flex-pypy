from pypy.rpython.extfunc import genericcallable, register_external
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc
from pypy.translator.flex.asmgen import add_import

def flexTrace(s):
    pass
register_external(flexTrace, args=[str], export_name="_consts_0.flexTrace")

def trace(s):
    pass
register_external(trace, args=[str], export_name="trace")

def addChild(what):
    pass
register_external(addChild, args=None, export_name="addChild")
    
    
add_import("mx.controls.Button")
class Button(BasicExternal):
    _render_class = "mx.controls.Button"
    _fields = {
        'x': int,
        'y': int,
    }

    _methods = {
        'move': MethodDesc([int, int]),
    }

