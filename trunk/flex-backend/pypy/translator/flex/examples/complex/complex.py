from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

class Grossini():
    def load_image(self, w):
        i = Image()
        i.load("grossini.png")
        w.addChild(i)

class Sonido():
    def load_sound(self):
        s = Sound()
        r = newURLRequest("sal.mp3")
        s.load(r)
        s.play()

class State(object):
    sound = None
state = State()

def callback(event):
    s = state.sound
    s.load_sound()

def flash_main( x=1 ):
    w = castToWindow( x )
    w.setActualSize(300,200)

    g = Grossini()
    g.load_image(w)

    s = Sonido()
    state.sound = s

    b = Button()
    b.addEventListener("click" , callback)
    b.label = "Play a sound!"
    b.x=20
    b.y=52
    w.addChild(b)
