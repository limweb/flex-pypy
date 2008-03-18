from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

class Grossini():
    def load_image(self, w):
        i = Image()
        i.load("espejo.png")
        w.addChild(i)

def flash_main( x=1 ):
    w = castToWindow( x )
    w.setActualSize(400,400)

    o = Grossini()
    o.load_image(w)
