from pypy.rpython.extfunc import genericcallable, register_external
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

# For each wrapped function, we define an empty function, and then register it with an actionscript function:
# This one is for debug output, so we can see our calls working
def flexTrace(s):
    pass

# This function has one arg, which is of type string
# if there were a return type, it would be result=<type>
# export_name refers to the corresponding Actionscript function. In this case it's _const_0.flexTrace, which is defined by us in library.as
register_external(flexTrace, args=[str], export_name="_consts_0.flexTrace")

# Wrapping a Actionscript class as a python class
class Date(BasicExternal):
    # This ties the Python "Date" class to the Actionscript "Date" class
    _render_class = "Date"

    # This lists the methods. The required argument for MethodDesc is a list of arguments (which are all empty in this case).
    # The return types are specified by retval=<type>
    _methods = {
        'getDate': MethodDesc([], retval=int),
        'getFullYear': MethodDesc([], retval=int),
        'getMonth': MethodDesc([], retval=int),
        'getHours': MethodDesc([], retval=int),
        'getMinutes': MethodDesc([], retval=int),
    }

# The Date class in Actionscript doesn't require importing any libraries, but if it did, we would import the library with:
# add_import(<libname>)
# We would do it at the top level, not in flash_main

def flash_main(a=1):
    flexTrace("Starting! python")

    d = Date()
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] [d.getMonth()]
    dateString = month + " " + str(d.getDate()) + ", " + str(d.getFullYear())
    timeString = str(d.getHours()) + ":" + str(d.getMinutes())
    flexTrace("The current date is: " +  dateString + " The current time is " + timeString)

    flexTrace("Im done!")
