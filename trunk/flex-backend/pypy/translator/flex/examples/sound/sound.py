from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

class Sonido():
    def load_sound(self, w):
        s = Sound()
        r = newURLRequest("sal.mp3")
        s.load(r)
        s.play()

def flash_main( x=1 ):
    w = castToWindow( x )

    o = Sonido()
    o.load_sound(w)
