"""
Interp-level implementation of the basic space operations.
"""

from pypy.interpreter import gateway
from pypy.interpreter.baseobjspace import ObjSpace
from pypy.interpreter.error import OperationError
import __builtin__
NoneNotWrapped = gateway.NoneNotWrapped

def abs(space, w_val):
    "abs(number) -> number\n\nReturn the absolute value of the argument."
    return space.abs(w_val)

def chr(space, w_ascii):
    "Return a string of one character with the given ascii code."
    w_character = space.newstring([w_ascii])
    return w_character

def unichr(space, w_code):
    "Return a Unicode string of one character with the given ordinal."
    # XXX range checking!
    return space.newunicode([__builtin__.unichr(space.int_w(w_code))])

def len(space, w_obj):
    "len(object) -> integer\n\nReturn the number of items of a sequence or mapping."
    return space.len(w_obj)


def checkattrname(space, w_name):
    # This is a check to ensure that getattr/setattr/delattr only pass a
    # string to the rest of the code.  XXX not entirely sure if these three
    # functions are the only way for non-string objects to reach
    # space.{get,set,del}attr()...
    # Note that if w_name is already a string (or a subclass of str),
    # it must be returned unmodified (and not e.g. unwrapped-rewrapped).
    if not space.is_true(space.isinstance(w_name, space.w_str)):
        name = space.str_w(w_name)    # typecheck
        w_name = space.wrap(name)     # rewrap as a real string
    return w_name

def delattr(space, w_object, w_name):
    """Delete a named attribute on an object.
delattr(x, 'y') is equivalent to ``del x.y''."""
    w_name = checkattrname(space, w_name)
    space.delattr(w_object, w_name)
    return space.w_None

def getattr(space, w_object, w_name, w_defvalue=NoneNotWrapped):
    """Get a named attribute from an object.
getattr(x, 'y') is equivalent to ``x.y''."""
    w_name = checkattrname(space, w_name)
    try:
        return space.getattr(w_object, w_name)
    except OperationError, e:
        if w_defvalue is not None:
            if e.match(space, space.w_AttributeError):
                return w_defvalue
        raise

def hasattr(space, w_object, w_name):
    """Return whether the object has an attribute with the given name.
    (This is done by calling getattr(object, name) and catching exceptions.)"""
    w_name = checkattrname(space, w_name)
    if space.findattr(w_object, w_name) is not None:
        return space.w_True
    else:
        return space.w_False

def hash(space, w_object):
    """Return a hash value for the object.  Two objects which compare as
equal have the same hash value.  It is possible, but unlikely, for
two un-equal objects to have the same hash value."""
    return space.hash(w_object)

def oct(space, w_val):
    """Return the octal representation of an integer."""
    # XXX does this need to be a space operation?
    return space.oct(w_val)

def hex(space, w_val):
    """Return the hexadecimal representation of an integer."""
    return space.hex(w_val)

def id(space, w_object):
    "Return the identity of an object: id(x) == id(y) if and only if x is y."
    return space.id(w_object)

def cmp(space, w_x, w_y):
    """return 0 when x == y, -1 when x < y and 1 when x > y """
    return space.cmp(w_x, w_y)

def coerce(space, w_x, w_y):
    """coerce(x, y) -> (x1, y1)

Return a tuple consisting of the two numeric arguments converted to
a common type, using the same rules as used by arithmetic operations.
If coercion is not possible, raise TypeError."""
    return space.coerce(w_x, w_y)

def divmod(space, w_x, w_y):
    """Return the tuple ((x-x%y)/y, x%y).  Invariant: div*y + mod == x."""
    return space.divmod(w_x, w_y)

# semi-private: works only for new-style classes.
def _issubtype(space, w_cls1, w_cls2):
    return space.issubtype(w_cls1, w_cls2)

# ____________________________________________________________

from math import floor as _floor
from math import ceil as _ceil

def round(space, number, ndigits=0):
    """round(number[, ndigits]) -> floating point number

Round a number to a given precision in decimal digits (default 0 digits).
This always returns a floating point number.  Precision may be negative."""
    # Algortithm copied directly from CPython
    f = 1.0
    if ndigits < 0:
        i = -ndigits
    else:
        i = ndigits
    while i > 0:
        f = f*10.0
        i -= 1
    if ndigits < 0:
        number /= f
    else:
        number *= f
    if number >= 0.0:
        number = _floor(number + 0.5)
    else:
        number = _ceil(number - 0.5)
    if ndigits < 0:
        number *= f
    else:
        number /= f
    return space.wrap(number)
#
round.unwrap_spec = [ObjSpace, float, int]

# ____________________________________________________________

iter_sentinel = gateway.applevel('''
    # NOT_RPYTHON  -- uses yield
    # App-level implementation of the iter(callable,sentinel) operation.

    def iter_generator(callable_, sentinel):
        while 1:
            result = callable_()
            if result == sentinel:
                return
            yield result

    def iter_sentinel(callable_, sentinel):
        if not callable(callable_):
            raise TypeError, 'iter(v, w): v must be callable'
        return iter_generator(callable_, sentinel)

''', filename=__file__).interphook("iter_sentinel")

def iter(space, w_collection_or_callable, w_sentinel=NoneNotWrapped):
    """iter(collection) -> iterator over the elements of the collection.

iter(callable, sentinel) -> iterator calling callable() until it returns
                            the sentinal.
"""
    if w_sentinel is None:
        return space.iter(w_collection_or_callable) 
        # XXX it seems that CPython checks the following 
        #     for newstyle but doesn't for oldstyle classes :-( 
        #w_res = space.iter(w_collection_or_callable)
        #w_typeres = space.type(w_res) 
        #try: 
        #    space.getattr(w_typeres, space.wrap('next'))
        #except OperationError, e: 
        #    if not e.match(space, space.w_AttributeError): 
        #        raise 
        #    raise OperationError(space.w_TypeError, 
        #        space.wrap("iter() returned non-iterator of type '%s'" % 
        #                   w_typeres.name))
        #else: 
        #    return w_res 
    else:
        return iter_sentinel(space, w_collection_or_callable, w_sentinel)

def _seqiter(space, w_obj):
    return space.newseqiter(w_obj)

def ord(space, w_val):
    """Return the integer ordinal of a character."""
    return space.ord(w_val)

def pow(space, w_base, w_exponent, w_modulus=None):
    """With two arguments, equivalent to ``base**exponent''.
With three arguments, equivalent to ``(base**exponent) % modulus'',
but much more efficient for large exponents."""
    return space.pow(w_base, w_exponent, w_modulus)

def repr(space, w_object):
    """Return a canonical string representation of the object.
For simple object types, eval(repr(object)) == object."""
    return space.repr(w_object)

def setattr(space, w_object, w_name, w_val):
    """Store a named attribute into an object.
setattr(x, 'y', z) is equivalent to ``x.y = z''."""
    w_name = checkattrname(space, w_name)
    space.setattr(w_object, w_name, w_val)
    return space.w_None

def intern(space, w_str):
    """``Intern'' the given string.  This enters the string in the (global)
table of interned strings whose purpose is to speed up dictionary lookups.
Return the string itself or the previously interned string object with the
same value."""
    if space.is_w(space.type(w_str), space.w_str):
        return space.new_interned_w_str(w_str)
    raise OperationError(space.w_TypeError, space.wrap("intern() argument must be string."))

def callable(space, w_object):
    """Check whether the object appears to be callable (i.e., some kind of
function).  Note that classes are callable."""
    return space.callable(w_object)



def _recursive_issubclass(space, w_cls, w_klass_or_tuple): # returns interp-level bool
    if space.is_w(w_cls, w_klass_or_tuple):
        return True
    try:
        w_bases = space.getattr(w_cls, space.wrap("__bases__"))
    except OperationError, e:
        if e.match(space, space.w_AttributeError):
            return False
        else:
            raise
    w_iterator = space.iter(w_bases)
    while True:
        try:
            w_base = space.next(w_iterator)
        except OperationError, e:
            if not e.match(space, space.w_StopIteration):
                raise
            break
        if _recursive_issubclass(space, w_base, w_klass_or_tuple):
            return True
    return False

def _issubclass(space, w_cls, w_klass_or_tuple, check_cls, depth): # returns interp-level bool
    if depth == 0:
        # XXX overzealous test compliance hack
        raise OperationError(space.w_RuntimeError, space.wrap("maximum recursion depth exceeded"))
    if space.is_true(space.issubtype(space.type(w_klass_or_tuple), space.w_tuple)):
        w_iter = space.iter(w_klass_or_tuple)
        while True:
            try:
                w_klass = space.next(w_iter)
            except OperationError, e:
                if not e.match(space, space.w_StopIteration):
                   raise
                break
            if _issubclass(space, w_cls, w_klass, True, depth - 1):
                return True
        return False

    try:
        return space.is_true(space.issubtype(w_cls, w_klass_or_tuple))
    except OperationError, e:
        if e.match(space, space.w_TypeError):
            w_bases = space.wrap('__bases__')
            if check_cls:
                try:
                    space.getattr(w_cls, w_bases)
                except OperationError, e:
                    if not e.match(space, space.w_AttributeError):
                        raise
                    raise OperationError(space.w_TypeError, space.wrap('arg 1 must be a class or type'))
            try:
                space.getattr(w_klass_or_tuple, w_bases)
            except OperationError, e:
                if not e.match(space, space.w_AttributeError):
                    raise
                raise OperationError(space.w_TypeError, space.wrap('arg 2 must be a class or type or a tuple thereof'))
            return _recursive_issubclass(space, w_cls, w_klass_or_tuple)
        else:
            raise


def issubclass(space, w_cls, w_klass_or_tuple):
    """Check whether a class 'cls' is a subclass (i.e., a derived class) of
another class.  When using a tuple as the second argument, check whether
'cls' is a subclass of any of the classes listed in the tuple."""
    return space.wrap(issubclass_w(space, w_cls, w_klass_or_tuple))

def issubclass_w(space, w_cls, w_klass_or_tuple):
    return _issubclass(space, w_cls, w_klass_or_tuple, True, space.sys.recursionlimit)


def isinstance(space, w_obj, w_klass_or_tuple):
    """Check whether an object is an instance of a class (or of a subclass
thereof).  When using a tuple as the second argument, check whether 'obj'
is an instance of any of the classes listed in the tuple."""
    w_objtype = space.type(w_obj)
    if issubclass_w(space, w_objtype, w_klass_or_tuple):
        return space.w_True
    try:
        w_objcls = space.getattr(w_obj, space.wrap("__class__"))
    except OperationError, e:
        if e.match(space, space.w_AttributeError):
            return space.w_False
        else:
            raise
    if space.is_w(w_objcls, w_objtype):
        return space.w_False
    else:
        return space.wrap(_issubclass(space, w_objcls, w_klass_or_tuple, False, space.sys.recursionlimit))
