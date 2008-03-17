from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

def flash_main( x=1 ):

    b = Button()
    b.x=20
    b.y=52

    w = castToWindow( x )
    w.addChild(b)

