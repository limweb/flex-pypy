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
register_external(addChild, args=None, export_name="x_0.addChild")

add_import("mx.controls.Button")
class Event(BasicExternal):
    pass
    
class Button(BasicExternal):
    _render_class = "mx.controls.Button"
    _fields = {
        'x': int,
        'y': int,
        'label': str,
        'labelPlacement':str,
    }

    _methods = {
        'move': MethodDesc([int, int]),
        'addEventListener':MethodDesc([str, genericcallable([Event])])
    }

class Window(BasicExternal):
    _methods = {
        'addChild': MethodDesc([Button]),
        'setActualSize': MethodDesc([int, int]),
    }

def castToWindow(i):
    pass
register_external(castToWindow, args=[int], result=Window, export_name="_consts_0.castToWindow")

add_import("mx.controls.Image")
class Image(Button):
    _render_class = "mx.controls.Image"
    _fields = {
        'data': str,
    }

    _methods = {
        'load': MethodDesc([str]),
    }
