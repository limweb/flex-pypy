# NOT_RPYTHON   -- flowing results in
# AttributeError:   << 'FlowObjSpace' object has no attribute 'w_AttributeError'
# XXX investigate!
"""
The 'sys' module.
"""

import sys 

def excepthook(exctype, value, traceback):
    """Handle an exception by displaying it with a traceback on sys.stderr."""
    from traceback import print_exception
    print_exception(exctype, value, traceback)

def exit(exitcode=0):
    """Exit the interpreter by raising SystemExit(exitcode).
If the exitcode is omitted or None, it defaults to zero (i.e., success).
If the exitcode is numeric, it will be used as the system exit status.
If it is another kind of object, it will be printed and the system
exit status will be one (i.e., failure)."""
    # note that we cannot use SystemExit(exitcode) here.
    # The comma version leads to an extra de-tupelizing
    # in normalize_exception, which is exactly like CPython's.
    raise SystemExit, exitcode

def exitfunc():
    """Placeholder for sys.exitfunc(), which is called when PyPy exits."""

pypy__exithandlers__ = {}

#import __builtin__

def getfilesystemencoding():
    """Return the encoding used to convert Unicode filenames in
operating system filenames.
    """
    if sys.platform == "win32":
        encoding = "mbcs"
    elif sys.platform == "darwin":
        encoding = "utf-8"
    else:
        encoding = None
    return encoding

def callstats():
    """Not implemented."""
    return None

defaultencoding = 'ascii'

def getdefaultencoding():
    """Return the current default string encoding used by the Unicode 
implementation."""
    return defaultencoding

def setdefaultencoding(encoding):
    """Set the current default string encoding used by the Unicode 
implementation."""
    global defaultencoding
    import codecs
    codecs.lookup(encoding)
    defaultencoding = encoding
