from pypy.rpython.extfunc import genericcallable, register_external
from pypy.translator.flex.modules.flex import add_import, Event, flexTrace
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

# This demonstrates:

# Global variables (getGlobal, setGlobal), necessary for callback functions to do anything useful
# Text Areas
# Adding multiple kinds of controls to a window (Button and TextArea inherit from Control, Window takes Control type)


# Inherited by TextArea and Button, so that both types can be added to the window
class Control(BasicExternal):
	_render_class = "mx.controls.TextArea"
	pass



add_import("mx.controls.TextArea")
class TextArea(Control):
    _render_class = "mx.controls.TextArea"
    _fields = {
        'x': int,
        'y': int,
        'text':str,
        'editable':bool,
        'labelPlacement':str,
    }

    _methods = {
        'addEventListener':MethodDesc([str, genericcallable([Event])]),
        'move': MethodDesc([int, int])
    }




add_import("mx.controls.Button")
class Button(Control):
    _render_class = "mx.controls.Button"
    _fields = {
        'x': int,
        'y': int,
        'label':str,
        'labelPlacement':str,
    }

    _methods = {
        'addEventListener':MethodDesc([str, genericcallable([Event])]),
        'move': MethodDesc([int, int])
    }


# These Get and Set from the globally accesible Actionscript Dictionary object (see library.as)

def getGlobal(s):
    pass
register_external(getGlobal, args=[str], export_name="_consts_0.getGlobal", result=TextArea)

def setGlobal(s):
    pass
register_external(setGlobal, args=[str, TextArea], export_name="_consts_0.setGlobal")




# Window stuff; note the use of Control

class Window(BasicExternal):
    _methods = {
        'addChild': MethodDesc([Control]),
    }

def castToWindow(i):
    pass
register_external(castToWindow, args=[int], result=Window,export_name="_consts_0.castToWindow")


# Callback function
def onSubmit(event):
    getGlobal("Out").text = getGlobal("In").text


# Main function    
def flash_main( x=1 ):
# Set up the TextAreas
    textOut = TextArea()
    textIn = TextArea()
    textOut.text = "Output"
    textOut.editable = False
    textIn.text = "Input"

# add the TextAreas to the globals
    setGlobal("Out", textOut)
    setGlobal("In", textIn)

# set up the button
    submit = Button()
    submit.label = "Copy Input to Output"
    submit.addEventListener( "click" , onSubmit)

# add to the window
    w = castToWindow( x )
    w.addChild(textOut)
    w.addChild(textIn)
    w.addChild(submit)

