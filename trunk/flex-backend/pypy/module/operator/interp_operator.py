def index(space, w_a):
    return space.index(w_a)

def abs(space, w_obj):
    'abs(a) -- Same as abs(a).'
    return space.abs(w_obj)

def add(space, w_obj1, w_obj2):
    'add(a, b) -- Same as a a + b'
    return space.add(w_obj1, w_obj2)

def and_(space, w_obj1, w_obj2):
    'and_(a, b) -- Same as a a & b'
    return space.and_(w_obj1, w_obj2)

# attrgetter

def concat(space, w_obj1, w_obj2):
    'concat(a, b) -- Same as a a + b, for a and b sequences.'
    return space.add(w_obj1, w_obj2) # XXX cPython only works on types with sequence api
                                     # we support any with __add__

def contains(space, w_obj1, w_obj2):
    'contains(a, b) -- Same as b in a (note reversed operands).'
    return space.contains(w_obj1, w_obj2)

# countOf

def delitem(space, w_obj, w_key):
    'delitem(a,b) -- Same as del a[b]'
    space.delitem(w_obj, w_key)

# delslice

def div(space, w_a, w_b):
    'div(a, b) -- Same as a / b when __future__.division is no in effect'
    return space.div(w_a, w_b)

def eq(space, w_a, w_b):
    'eq(a, b) -- Same as a==b'
    return space.eq(w_a, w_b)

def floordiv(space, w_a, w_b):
    'floordiv(a, b) -- Same as a // b.'
    return space.floordiv(w_a, w_b)

def ge(space, w_a, w_b):
    'ge(a, b) -- Same as a>=b.'
    return space.ge(w_a, w_b)

def getitem(space, w_a, w_b):
    'getitem(a, b) -- Same as a[b].'
    return space.getitem(w_a, w_b)

# getslice

def gt(space, w_a, w_b):
    'gt(a, b) -- Same as a>b.'
    return space.gt(w_a, w_b)

# indexOf

def inv(space, w_obj,):
    'inv(a) -- Same as ~a.'
    return space.invert(w_obj)

def invert(space, w_obj,):
    'invert(a) -- Same as ~a.'
    return space.invert(w_obj) 

def isCallable(space, w_obj):
    'isCallable(a) -- Same as callable(a).'
    return space.callable(w_obj)

# isMappingType

# isNumberType

# isSequenceType

def is_(space, w_a, w_b):
    'is_(a,b) -- Same as a is b'
    return space.is_(w_a, w_b)

def is_not(space, w_a, w_b):
    'is_not(a, b) -- Same as a is not b'
    return space.not_(space.is_(w_a, w_b))

# itemgetter

def le(space, w_a, w_b):
    'le(a, b) -- Same as a<=b.'
    return space.le(w_a, w_b)

def lshift(space, w_a, w_b):
    'lshift(a, b) -- Same as a << b.'
    return space.lshift(w_a, w_b) 

def lt(space, w_a, w_b):
    'lt(a, b) -- Same as a<b.'
    return space.lt(w_a, w_b)

def mod(space, w_a, w_b):
    'mod(a, b) -- Same as a % b.'
    return space.mod(w_a, w_b)

def mul(space, w_a, w_b):
    'mul(a, b) -- Same as a * b.'
    return space.mul(w_a, w_b)

def ne(space, w_a, w_b):
    'ne(a, b) -- Same as a!=b.'
    return space.ne(w_a, w_b) 

def neg(space, w_obj,):
    'neg(a) -- Same as -a.'
    return space.neg(w_obj)

def not_(space, w_obj,):
    'not_(a) -- Same as not a.'
    return space.not_(w_obj)

def or_(space, w_a, w_b):
    'or_(a, b) -- Same as a | b.'
    return space.or_(w_a, w_b)

def pos(space, w_obj,):
    'pos(a) -- Same as +a.'
    return space.pos(w_obj) 

def pow(space, w_a, w_b):
    'pow(a, b) -- Same as a**b.'
    return space.pow(w_a, w_b, space.w_None)

# reapeat

def rshift(space, w_a, w_b):
    'rshift(a, b) -- Same as a >> b.'
    return space.rshift(w_a, w_b) 

# sequenceIncludes

def setitem(space, w_obj, w_key, w_value):
    'setitem(a, b, c) -- Same as a[b] = c.'
    space.setitem(w_obj, w_key, w_value)

# setslice

def sub(space, w_a, w_b):
    'sub(a, b) -- Same as a - b.'
    return space.sub(w_a, w_b) 

def truediv(space, w_a, w_b):
    'truediv(a, b) -- Same as a / b when __future__.division is in effect.'
    return space.truediv(w_a, w_b)

def truth(space, w_a,):
    'truth(a) -- Return True if a is true, False otherwise.'
    return space.nonzero(w_a)

def xor(space, w_a, w_b):
    'xor(a, b) -- Same as a ^ b.'
    return space.xor(w_a, w_b)