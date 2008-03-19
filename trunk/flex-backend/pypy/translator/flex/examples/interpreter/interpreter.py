from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc
from pypy.interpreter.main import run_string
import py
from pypy.objspace.std import Space
   
from pypy.interpreter.pycompiler import CPythonCompiler as CompilerClass


def codetest(source, functionname, args):
    """Compile and run the given code string, and then call its function
    named by 'functionname' with arguments 'args'."""
    from pypy.interpreter import baseobjspace
    from pypy.interpreter import pyframe, gateway, module
    space = Space()

    source = str(py.code.Source(source).strip()) + '\n'

    w = space.wrap
    w_code = space.builtin.call('compile', 
            w(source), w('<string>'), w('exec'), w(0), w(0))

    tempmodule = module.Module(space, w("__temp__"))
    w_glob = tempmodule.w_dict
    space.setitem(w_glob, w("__builtins__"), space.builtin)

    code = space.unwrap(w_code)
    code.exec_code(space, w_glob, w_glob)

    wrappedargs = [w(a) for a in args]
    wrappedfunc = space.getitem(w_glob, w(functionname))
    def callit():
        return space.call_function(wrappedfunc, *wrappedargs)
    return callit
    try:
        w_output = space.call_function(wrappedfunc, *wrappedargs)
    except baseobjspace.OperationError, e:
        #e.print_detailed_traceback(space)
        return '<<<%s>>>' % e.errorstr(space)
    else:
        return space.unwrap(w_output) 


       
python_code = codetest("""
def hello():
    print 'hello'
""", "hello", [])
   
def callback(event):
    python_code()
        
def flash_main( x=1 ):
    window = castToWindow( x ) 
    b = Button()
    b.addEventListener( "click" , callback)
    b.label = "Hello world!"
    b.x=20
    b.y=52

    window.addChild(b)