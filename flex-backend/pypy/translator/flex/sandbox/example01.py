from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc


def flash_main( x=1 ):

    i = Image()
    i.source = load_resource("py_grossini_png")

    w = castToWindow( x )
    w.addChild(i)

    r = load_sound_resource("py_sal_mp3")
    r.play()
