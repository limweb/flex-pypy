from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

    
def callback(event):
    flexTrace("hola")        
   
class Clase:
    def metodo(self):
        flexTrace("hola")
        
def flash_main( x=1 ):
    window = castToWindow( x ) 
    b = Button()
    b.addEventListener( "click" , callback)
    b.label = "Hello world!"
    b.x=20
    b.y=52

    a = Clase()
    a.metodo()
    window.addChild(b)
    
    
