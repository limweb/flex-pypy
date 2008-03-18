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
class Event(BasicExternal):
    _fields = {
        'localX':int,
        'localY':int,
        'stageX':int,
        'stageY':int,
    }
    
    
class Button(BasicExternal):
    _render_class = "mx.controls.Button"
    _fields = {
        'label': str,
        'labelPlacement':str,
    }

    _methods = {
        #'move': MethodDesc([int, int]),
        #'addEventListener':MethodDesc([str, genericcallable([Event])])
    }
add_import("mx.controls.Image")
class Image(BasicExternal):
    _render_class = "mx.controls.Image"
    _fields = {
        'data': str,
        'source' : str,
        'x': int,
        'y': int,
        'width':int,
        'height':int,
        'rotation':int,
    }

    _methods = {
        'load': MethodDesc([str]),
        'move': MethodDesc([int,int]),
    }
add_import("flash.display.Sprite")
class Sprite(BasicExternal):
    _render_class = "flash.display.Sprite"
    _fields = {
        'data': str,
        'source' : str,
        'x': int,
        'y': int,
        'width':int,
        'height':int,
        'rotation':int,
    }

    _methods = {
        'load': MethodDesc([str]),
        'move': MethodDesc([int,int]),
        'addChild': MethodDesc([Image]),
    }

class Window(BasicExternal):
    _fields = {
        'layout': str,
    }
    _methods = {
        'addChild': MethodDesc([Image]),
        'setActualSize': MethodDesc([int, int]),
        'addEventListener':MethodDesc([str, genericcallable([Event])])
    }
class SpriteWindow(BasicExternal):
    _fields = {
        'layout': str,
    }
    _methods = {
        'addChild': MethodDesc([Sprite]),
        'setActualSize': MethodDesc([int, int]),
        'addEventListener':MethodDesc([str, genericcallable([Event])])
    }

def castToWindow(i):
    pass
register_external(castToWindow, args=[int], result=Window, export_name="_consts_0.castToWindow")

def castToSpriteWindow(i):
    pass
register_external(castToSpriteWindow, args=[Window], result=SpriteWindow, export_name="_consts_0.castToSpriteWindow")

add_import("flash.net.URLRequest")
class URLRequest(BasicExternal):
    _render_class = "flash.net.URLRequest"
    _fields = {
    }

    _methods = {
    }

def newURLRequest(s):
    pass
register_external(newURLRequest, args=[str], result=URLRequest, export_name="new URLRequest")

add_import("flash.media.Sound")
class Sound(Button):
    _render_class = "flash.media.Sound"
    _fields = {
        'data': str,
    }

    _methods = {
        'load': MethodDesc([URLRequest]),
        'play': MethodDesc([]),
    }

def partial(i):
    pass
register_external(partial, args=[genericcallable([Event, str]), str], result=genericcallable([Event]), export_name="_consts_0.partial")

add_import("mx.core.SoundAsset")
class SoundAsset(Sound):
    _render_class = "mx.core.SoundAsset"

def load_resource(what):
    pass
register_external(load_resource, args=[str], result=str, export_name="load_resource")

def load_sound_resource(what):
    pass
register_external(load_sound_resource, args=[str], result=SoundAsset, export_name="load_sound_resource")

