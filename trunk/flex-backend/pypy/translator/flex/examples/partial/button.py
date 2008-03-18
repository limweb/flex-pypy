from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

def callback(event, mess):
    flexTrace(mess) 

def flash_main( x=1 ):
    window = castToWindow( x ) 
    b = Button()
    func = partial(callback, "hola")
    b.addEventListener("click" , func)
    b.label = "Hello world!"
    b.x=20
    b.y=52
    window.addChild(b)

    b = Button()
    func = partial(callback, "chau")
    b.addEventListener("click" , func)
    b.label = "Bye bye world!"
    b.x=20
    b.y=52
    window.addChild(b)
    
    
