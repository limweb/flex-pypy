from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc


class Grossini():
    def load_image(self,w):
        print "hola"

def flash_main( x=1 ):


    b = Button()
    b.label="Hello World"
    b.labelPlacement = "Top"
    b.move(0,0)

    w = castToWindow( x )

    o = Grossini()
    o.load_image(w)

    w.addChild(b)

