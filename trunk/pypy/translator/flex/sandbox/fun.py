from pypy.translator.flex.modules.flex import *

class Bar:
    def __init__(self, arg):
        self.arg = arg +"(!)"
    def setValue(self, arg):
        self.arg = arg

    def value(self):
        return self.arg        
        
class Foo:
    def __init__(self, arg):
        self.arg = Bar(arg + "@")
        
    def setValue(self, arg):
        self.arg = Bar(arg +"#")
    def value(self):
        return self.arg.value()
        
def flash_main(a=1):
    flexTrace("Starting! python")
    
    f = Foo("hola")
    
    #for x in range(20):
    x = 0
    while True:
        f.setValue( "doing number "+str(x)+" !!" )
        flexTrace(f.value())
        x += 1
    flexTrace("Im done!")
