from pypy.objspace.std.objspace import *
from pypy.interpreter import gateway
from pypy.objspace.std.stringobject import W_StringObject
from pypy.objspace.std.ropeobject import W_RopeObject
from pypy.objspace.std.noneobject import W_NoneObject
from pypy.objspace.std.sliceobject import W_SliceObject
from pypy.objspace.std.tupleobject import W_TupleObject
from pypy.rlib.rarithmetic import intmask, ovfcheck
from pypy.module.unicodedata import unicodedb_3_2_0 as unicodedb

from pypy.objspace.std.formatting import mod_format

class W_UnicodeObject(W_Object):
    from pypy.objspace.std.unicodetype import unicode_typedef as typedef

    def __init__(w_self, unicodechars):
        w_self._value = unicodechars
        w_self.w_hash = None
    def __repr__(w_self):
        """ representation for debugging purposes """
        return "%s(%r)" % (w_self.__class__.__name__, w_self._value)

    def unwrap(w_self, space):
        # For faked functions taking unicodearguments.
        # Remove when we no longer need faking.
        return u''.join(w_self._value)

registerimplementation(W_UnicodeObject)

# Helper for converting int/long
def unicode_to_decimal_w(space, w_unistr):
    if not isinstance(w_unistr, W_UnicodeObject):
        raise OperationError(space.w_TypeError,
                             space.wrap("expected unicode"))
    unistr = w_unistr._value
    result = ['\0'] * len(unistr)
    digits = [ '0', '1', '2', '3', '4',
               '5', '6', '7', '8', '9']
    for i in xrange(len(unistr)):
        uchr = ord(unistr[i])
        if unicodedb.isspace(uchr):
            result[i] = ' '
            continue
        try:
            result[i] = digits[unicodedb.decimal(uchr)]
        except KeyError:
            if 0 < uchr < 256:
                result[i] = chr(uchr)
            else:
                w_encoding = space.wrap('decimal')
                w_start = space.wrap(i)
                w_end = space.wrap(i+1)
                w_reason = space.wrap('invalid decimal Unicode string')
                raise OperationError(space.w_UnicodeEncodeError,space.newtuple ([w_encoding, w_unistr, w_start, w_end, w_reason]))
    return ''.join(result)

# string-to-unicode delegation
def delegate_String2Unicode(space, w_str):
    w_uni =  space.call_function(space.w_unicode, w_str)
    assert isinstance(w_uni, W_UnicodeObject) # help the annotator!
    return w_uni

def str_w__Unicode(space, w_uni):
    return space.str_w(space.str(w_uni))

def unichars_w__Unicode(space, w_uni):
    return w_uni._value

def str__Unicode(space, w_uni):
    return space.call_method(w_uni, 'encode')

def eq__Unicode_Unicode(space, w_left, w_right):
    return space.newbool(w_left._value == w_right._value)

def lt__Unicode_Unicode(space, w_left, w_right):
    left = w_left._value
    right = w_right._value
    for i in range(min(len(left), len(right))):
        if left[i] != right[i]:
            return space.newbool(ord(left[i]) < ord(right[i]))
            # NB. 'unichar < unichar' is not RPython at the moment
    return space.newbool(len(left) < len(right))

def ord__Unicode(space, w_uni):
    if len(w_uni._value) != 1:
        raise OperationError(space.w_TypeError, space.wrap('ord() expected a character'))
    return space.wrap(ord(w_uni._value[0]))

def getnewargs__Unicode(space, w_uni):
    return space.newtuple([W_UnicodeObject(w_uni._value)])

def add__Unicode_Unicode(space, w_left, w_right):
    left = w_left._value
    right = w_right._value
    leftlen = len(left)
    rightlen = len(right)
    result = [u'\0'] * (leftlen + rightlen)
    for i in range(leftlen):
        result[i] = left[i]
    for i in range(rightlen):
        result[i + leftlen] = right[i]
    return W_UnicodeObject(result)

def add__String_Unicode(space, w_left, w_right):
    return space.add(space.call_function(space.w_unicode, w_left) , w_right)

add__Rope_Unicode = add__String_Unicode

def add__Unicode_String(space, w_left, w_right):
    return space.add(w_left, space.call_function(space.w_unicode, w_right))

add__Unicode_Rope = add__Unicode_String

def contains__String_Unicode(space, w_container, w_item):
    return space.contains(space.call_function(space.w_unicode, w_container), w_item )
contains__Rope_Unicode = contains__String_Unicode


def _find(self, sub, start, end):
    if len(sub) == 0:
        return start
    if start >= end:
        return -1
    for i in range(start, end - len(sub) + 1):
        for j in range(len(sub)):
            if self[i + j]  != sub[j]:
                break
        else:
            return i
    return -1

def _rfind(self, sub, start, end):
    if len(sub) == 0:
        return end
    if end - start < len(sub):
        return -1
    for i in range(end - len(sub), start - 1, -1):
        for j in range(len(sub)):
            if self[i + j]  != sub[j]:
                break
        else:
            return i
    return -1

def contains__Unicode_Unicode(space, w_container, w_item):
    item = w_item._value
    container = w_container._value
    return space.newbool(_find(container, item, 0, len(container)) >= 0)

def unicode_join__Unicode_ANY(space, w_self, w_list):
    list = space.unpackiterable(w_list)
    delim = w_self._value
    totlen = 0
    if len(list) == 0:
        return W_UnicodeObject([])
    if (len(list) == 1 and
        space.is_w(space.type(list[0]), space.w_unicode)):
        return list[0]
    
    values_list = [None] * len(list)
    values_list[0] = [u'\0']
    for i in range(len(list)):
        item = list[i]
        if space.is_true(space.isinstance(item, space.w_unicode)):
            pass
        elif space.is_true(space.isinstance(item, space.w_str)):
            item = space.call_function(space.w_unicode, item)
        else:
            w_msg = space.mod(space.wrap('sequence item %d: expected string or Unicode'),
                              space.wrap(i))
            raise OperationError(space.w_TypeError, w_msg)
        assert isinstance(item, W_UnicodeObject)
        item = item._value
        totlen += len(item)
        values_list[i] = item
    totlen += len(delim) * (len(values_list) - 1)
    if len(values_list) == 1:
        return W_UnicodeObject(values_list[0])
    # Allocate result
    result = [u'\0'] * totlen
    first = values_list[0]
    for i in range(len(first)):
        result[i] = first[i]
    offset = len(first)
    for i in range(1, len(values_list)):
        item = values_list[i]
        # Add delimiter
        for j in range(len(delim)):
            result[offset + j] = delim[j]
        offset += len(delim)
        # Add item from values_list
        for j in range(len(item)):
            result[offset + j] = item[j]
        offset += len(item)
    return W_UnicodeObject(result)


def hash__Unicode(space, w_uni):
    if w_uni.w_hash is None:
        # hrmpf
        chars = w_uni._value
        if len(chars) == 0:
            return space.wrap(0)
        if space.config.objspace.std.withrope:
            x = 0
            for c in chars:
                x = intmask((1000003 * x) + ord(c))
            x <<= 1
            x ^= len(chars)
            x ^= ord(chars[0])
            h = intmask(x)
        else:
            x = ord(chars[0]) << 7
            for c in chars:
                x = intmask((1000003 * x) ^ ord(c))
            h = intmask(x ^ len(chars))
            if h == -1:
                h = -2
        w_uni.w_hash = space.wrap(h)
    return w_uni.w_hash

def len__Unicode(space, w_uni):
    return space.wrap(len(w_uni._value))

def getitem__Unicode_ANY(space, w_uni, w_index):
    ival = space.getindex_w(w_index, space.w_IndexError, "string index")
    uni = w_uni._value
    ulen = len(uni)
    if ival < 0:
        ival += ulen
    if ival < 0 or ival >= ulen:
        exc = space.call_function(space.w_IndexError,
                                  space.wrap("unicode index out of range"))
        raise OperationError(space.w_IndexError, exc)
    return W_UnicodeObject([uni[ival]])

def getitem__Unicode_Slice(space, w_uni, w_slice):
    uni = w_uni._value
    length = len(uni)
    start, stop, step, sl = w_slice.indices4(space, length)
    if sl == 0:
        r = []
    elif step == 1:
        assert start >= 0 and stop >= 0
        r = uni[start:stop]
    else:
        r = [uni[start + i*step] for i in range(sl)]
    return W_UnicodeObject(r)

def mul__Unicode_ANY(space, w_uni, w_times):
    try:
        times = space.getindex_w(w_times, space.w_OverflowError)
    except OperationError, e:
        if e.match(space, space.w_TypeError):
            raise FailedToImplement
        raise
    chars = w_uni._value
    charlen = len(chars)
    if times <= 0 or charlen == 0:
        return W_UnicodeObject([])
    if times == 1:
        return space.call_function(space.w_unicode, w_uni)
    if charlen == 1:
        return W_UnicodeObject([w_uni._value[0]] * times)

    try:
        result_size = ovfcheck(charlen * times)
        result = [u'\0'] * result_size
    except (OverflowError, MemoryError):
        raise OperationError(space.w_OverflowError, space.wrap('repeated string is too long'))
    for i in range(times):
        offset = i * charlen
        for j in range(charlen):
            result[offset + j] = chars[j]
    return W_UnicodeObject(result)

def mul__ANY_Unicode(space, w_times, w_uni):
    return mul__Unicode_ANY(space, w_uni, w_times)

def _isspace(uchar):
    return unicodedb.isspace(ord(uchar))

def unicode_isspace__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isspace(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_isalpha__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isalpha(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_isalnum__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isalnum(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_isdecimal__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isdecimal(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_isdigit__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isdigit(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_isnumeric__Unicode(space, w_unicode):
    if len(w_unicode._value) == 0:
        return space.w_False
    for uchar in w_unicode._value:
        if not unicodedb.isnumeric(ord(uchar)):
            return space.w_False
    return space.w_True

def unicode_islower__Unicode(space, w_unicode):
    cased = False
    for uchar in w_unicode._value:
        if (unicodedb.isupper(ord(uchar)) or
            unicodedb.istitle(ord(uchar))):
            return space.w_False
        if not cased and unicodedb.islower(ord(uchar)):
            cased = True
    return space.newbool(cased)

def unicode_isupper__Unicode(space, w_unicode):
    cased = False
    for uchar in w_unicode._value:
        if (unicodedb.islower(ord(uchar)) or
            unicodedb.istitle(ord(uchar))):
            return space.w_False
        if not cased and unicodedb.isupper(ord(uchar)):
            cased = True
    return space.newbool(cased)

def unicode_istitle__Unicode(space, w_unicode):
    cased = False
    previous_is_cased = False
    for uchar in w_unicode._value:
        if (unicodedb.isupper(ord(uchar)) or
            unicodedb.istitle(ord(uchar))):
            if previous_is_cased:
                return space.w_False
            previous_is_cased = cased = True
        elif unicodedb.islower(ord(uchar)):
            if not previous_is_cased:
                return space.w_False
            previous_is_cased = cased = True
        else:
            previous_is_cased = False
    return space.newbool(cased)

def _strip(space, w_self, w_chars, left, right):
    "internal function called by str_xstrip methods"
    u_self = w_self._value
    u_chars = w_chars._value
    
    lpos = 0
    rpos = len(u_self)
    
    if left:
        while lpos < rpos and u_self[lpos] in u_chars:
           lpos += 1
       
    if right:
        while rpos > lpos and u_self[rpos - 1] in u_chars:
           rpos -= 1
           
    result = [u'\0'] * (rpos - lpos)
    for i in range(rpos - lpos):
        result[i] = u_self[lpos + i]
    return W_UnicodeObject(result)

def _strip_none(space, w_self, left, right):
    "internal function called by str_xstrip methods"
    u_self = w_self._value
    
    lpos = 0
    rpos = len(u_self)
    
    if left:
        while lpos < rpos and _isspace(u_self[lpos]):
           lpos += 1
       
    if right:
        while rpos > lpos and _isspace(u_self[rpos - 1]):
           rpos -= 1
       
    result = [u'\0'] * (rpos - lpos)
    for i in range(rpos - lpos):
        result[i] = u_self[lpos + i]
    return W_UnicodeObject(result)

def unicode_strip__Unicode_None(space, w_self, w_chars):
    return _strip_none(space, w_self, 1, 1)
def unicode_strip__Unicode_Unicode(space, w_self, w_chars):
    return _strip(space, w_self, w_chars, 1, 1)
def unicode_strip__Unicode_String(space, w_self, w_chars):
    return space.call_method(w_self, 'strip',
                             space.call_function(space.w_unicode, w_chars))
unicode_strip__Unicode_Rope = unicode_strip__Unicode_String

def unicode_lstrip__Unicode_None(space, w_self, w_chars):
    return _strip_none(space, w_self, 1, 0)
def unicode_lstrip__Unicode_Unicode(space, w_self, w_chars):
    return _strip(space, w_self, w_chars, 1, 0)
def unicode_lstrip__Unicode_String(space, w_self, w_chars):
    return space.call_method(w_self, 'lstrip',
                             space.call_function(space.w_unicode, w_chars))

unicode_lstrip__Unicode_Rope = unicode_lstrip__Unicode_String

def unicode_rstrip__Unicode_None(space, w_self, w_chars):
    return _strip_none(space, w_self, 0, 1)
def unicode_rstrip__Unicode_Unicode(space, w_self, w_chars):
    return _strip(space, w_self, w_chars, 0, 1)
def unicode_rstrip__Unicode_String(space, w_self, w_chars):
    return space.call_method(w_self, 'rstrip',
                             space.call_function(space.w_unicode, w_chars))

unicode_rstrip__Unicode_Rope = unicode_rstrip__Unicode_String

def unicode_capitalize__Unicode(space, w_self):
    input = w_self._value
    if len(input) == 0:
        return W_UnicodeObject([])
    result = [u'\0'] * len(input)
    result[0] = unichr(unicodedb.toupper(ord(input[0])))
    for i in range(1, len(input)):
        result[i] = unichr(unicodedb.tolower(ord(input[i])))
    return W_UnicodeObject(result)

def unicode_title__Unicode(space, w_self):
    input = w_self._value
    if len(input) == 0:
        return w_self
    result = [u'\0'] * len(input)

    previous_is_cased = 0
    for i in range(len(input)):
        unichar = ord(input[i])
        if previous_is_cased:
            result[i] = unichr(unicodedb.tolower(unichar))
        else:
            result[i] = unichr(unicodedb.totitle(unichar))
        previous_is_cased = unicodedb.iscased(unichar)
    return W_UnicodeObject(result)

def unicode_lower__Unicode(space, w_self):
    input = w_self._value
    result = [u'\0'] * len(input)
    for i in range(len(input)):
        result[i] = unichr(unicodedb.tolower(ord(input[i])))
    return W_UnicodeObject(result)

def unicode_upper__Unicode(space, w_self):
    input = w_self._value
    result = [u'\0'] * len(input)
    for i in range(len(input)):
        result[i] = unichr(unicodedb.toupper(ord(input[i])))
    return W_UnicodeObject(result)

def unicode_swapcase__Unicode(space, w_self):
    input = w_self._value
    result = [u'\0'] * len(input)
    for i in range(len(input)):
        unichar = ord(input[i])
        if unicodedb.islower(unichar):
            result[i] = unichr(unicodedb.toupper(unichar))
        elif unicodedb.isupper(unichar):
            result[i] = unichr(unicodedb.tolower(unichar))
        else:
            result[i] = input[i]
    return W_UnicodeObject(result)

def _normalize_index(length, index):
    if index < 0:
        index += length
        if index < 0:
            index = 0
    elif index > length:
        index = length
    return index

def unicode_endswith__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))

    substr = w_substr._value
    substr_len = len(substr)
    
    if end - start < substr_len:
        return space.w_False # substring is too long
    start = end - substr_len
    for i in range(substr_len):
        if self[start + i] != substr[i]:
            return space.w_False
    return space.w_True

def unicode_startswith__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))

    substr = w_substr._value
    substr_len = len(substr)
    
    if end - start < substr_len:
        return space.w_False # substring is too long
    
    for i in range(substr_len):
        if self[start + i] != substr[i]:
            return space.w_False
    return space.w_True

def _to_unichar_w(space, w_char):
    try:
        w_unichar = unicodetype.unicode_from_object(space, w_char)
    except OperationError, e:
        if e.match(space, space.w_TypeError):
            msg = 'The fill character cannot be converted to Unicode'
            raise OperationError(space.w_TypeError, space.wrap(msg))
        else:
            raise

    if space.int_w(space.len(w_unichar)) != 1:
        raise OperationError(space.w_TypeError, space.wrap('The fill character must be exactly one character long'))
    unichar = unichr(space.int_w(space.ord(w_unichar)))
    return unichar

def unicode_center__Unicode_ANY_ANY(space, w_self, w_width, w_fillchar):
    self = w_self._value
    width = space.int_w(w_width)
    fillchar = _to_unichar_w(space, w_fillchar)
    padding = width - len(self)
    if padding < 0:
        return space.call_function(space.w_unicode, w_self)
    leftpad = padding // 2 + (padding & width & 1)
    result = [fillchar] * width
    for i in range(len(self)):
        result[leftpad + i] = self[i]
    return W_UnicodeObject(result)

def unicode_ljust__Unicode_ANY_ANY(space, w_self, w_width, w_fillchar):
    self = w_self._value
    width = space.int_w(w_width)
    fillchar = _to_unichar_w(space, w_fillchar)
    padding = width - len(self)
    if padding < 0:
        return space.call_function(space.w_unicode, w_self)
    result = [fillchar] * width
    for i in range(len(self)):
        result[i] = self[i]
    return W_UnicodeObject(result)

def unicode_rjust__Unicode_ANY_ANY(space, w_self, w_width, w_fillchar):
    self = w_self._value
    width = space.int_w(w_width)
    fillchar = _to_unichar_w(space, w_fillchar)
    padding = width - len(self)
    if padding < 0:
        return space.call_function(space.w_unicode, w_self)
    result = [fillchar] * width
    for i in range(len(self)):
        result[padding + i] = self[i]
    return W_UnicodeObject(result)
    
def unicode_zfill__Unicode_ANY(space, w_self, w_width):
    self = w_self._value
    width = space.int_w(w_width)
    if len(self) == 0:
        return W_UnicodeObject([u'0'] * width)
    padding = width - len(self)
    if padding <= 0:
        return space.call_function(space.w_unicode, w_self)
    result = [u'0'] * width
    for i in range(len(self)):
        result[padding + i] = self[i]
    # Move sign to first position
    if self[0] in (u'+', u'-'):
        result[0] = self[0]
        result[padding] = u'0'
    return W_UnicodeObject(result)

def unicode_splitlines__Unicode_ANY(space, w_self, w_keepends):
    self = w_self._value
    keepends = 0
    if space.int_w(w_keepends):
        keepends = 1
    if len(self) == 0:
        return space.newlist([])
    
    start = 0
    end = len(self)
    pos = 0
    lines = []
    while pos < end:
        if unicodedb.islinebreak(ord(self[pos])):
            if (self[pos] == u'\r' and pos + 1 < end and
                self[pos + 1] == u'\n'):
                # Count CRLF as one linebreak
                lines.append(W_UnicodeObject(self[start:pos + keepends * 2]))
                pos += 1
            else:
                lines.append(W_UnicodeObject(self[start:pos + keepends]))
            pos += 1
            start = pos
        else:
            pos += 1
    if not unicodedb.islinebreak(ord(self[end - 1])):
        lines.append(W_UnicodeObject(self[start:]))
    return space.newlist(lines)

def unicode_find__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))
    substr = w_substr._value
    return space.wrap(_find(self, substr, start, end))

def unicode_rfind__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))
    substr = w_substr._value
    return space.wrap(_rfind(self, substr, start, end))

def unicode_index__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))
    substr = w_substr._value
    index = _find(self, substr, start, end)
    if index < 0:
        raise OperationError(space.w_ValueError,
                             space.wrap('substring not found'))
    return space.wrap(index)

def unicode_rindex__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))
    substr = w_substr._value
    index = _rfind(self, substr, start, end)
    if index < 0:
        raise OperationError(space.w_ValueError,
                             space.wrap('substring not found'))
    return space.wrap(index)

def unicode_count__Unicode_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
    self = w_self._value
    start = _normalize_index(len(self), space.int_w(w_start))
    end = _normalize_index(len(self), space.int_w(w_end))
    substr = w_substr._value
    count = 0
    while start <= end:
        index = _find(self, substr, start, end)
        if index < 0:
            break
        start = index + 1
        count += 1
    return space.wrap(count)


def unicode_split__Unicode_None_ANY(space, w_self, w_none, w_maxsplit):
    self = w_self._value
    maxsplit = space.int_w(w_maxsplit)
    parts = []
    if len(self) == 0:
        return space.newlist([])
    start = 0
    end = len(self)
    inword = 0

    while maxsplit != 0 and start < end:
        index = start
        for index in range(start, end):
            if _isspace(self[index]):
                break
            else:
                inword = 1
        else:
            break
        if inword == 1:
            parts.append(W_UnicodeObject(self[start:index]))
            maxsplit -= 1
        # Eat whitespace
        for start in range(index + 1, end):
            if not _isspace(self[start]):
                break
        else:
            return space.newlist(parts)

    parts.append(W_UnicodeObject(self[start:]))
    return space.newlist(parts)

def unicode_split__Unicode_Unicode_ANY(space, w_self, w_delim, w_maxsplit):
    self = w_self._value
    delim = w_delim._value
    maxsplit = space.int_w(w_maxsplit)
    delim_len = len(delim)
    if delim_len == 0:
        raise OperationError(space.w_ValueError,
                             space.wrap('empty separator'))
    parts = []
    start = 0
    end = len(self)
    while maxsplit != 0:
        index = _find(self, delim, start, end)
        if index < 0:
            break
        parts.append(W_UnicodeObject(self[start:index]))
        start = index + delim_len
        maxsplit -= 1
    parts.append(W_UnicodeObject(self[start:]))
    return space.newlist(parts)


def unicode_rsplit__Unicode_None_ANY(space, w_self, w_none, w_maxsplit):
    self = w_self._value
    maxsplit = space.int_w(w_maxsplit)
    parts = []
    if len(self) == 0:
        return space.newlist([])
    start = 0
    end = len(self)
    inword = 0

    while maxsplit != 0 and start < end:
        index = end
        for index in range(end-1, start-1, -1):
            if _isspace(self[index]):
                break
            else:
                inword = 1
        else:
            break
        if inword == 1:
            parts.append(W_UnicodeObject(self[index+1:end]))
            maxsplit -= 1
        # Eat whitespace
        for end in range(index, start-1, -1):
            if not _isspace(self[end-1]):
                break
        else:
            return space.newlist(parts)

    parts.append(W_UnicodeObject(self[:end]))
    parts.reverse()
    return space.newlist(parts)

def unicode_rsplit__Unicode_Unicode_ANY(space, w_self, w_delim, w_maxsplit):
    self = w_self._value
    delim = w_delim._value
    maxsplit = space.int_w(w_maxsplit)
    delim_len = len(delim)
    if delim_len == 0:
        raise OperationError(space.w_ValueError,
                             space.wrap('empty separator'))
    parts = []
    if len(self) == 0:
        return space.newlist([])
    start = 0
    end = len(self)
    while maxsplit != 0:
        index = _rfind(self, delim, 0, end)
        if index < 0:
            break
        parts.append(W_UnicodeObject(self[index+delim_len:end]))
        end = index
        maxsplit -= 1
    parts.append(W_UnicodeObject(self[:end]))
    parts.reverse()
    return space.newlist(parts)

def _split(space, self, maxsplit):
    if maxsplit == 0:
        return [W_UnicodeObject(self)]
    index = 0
    end = len(self)
    parts = [W_UnicodeObject([])]
    maxsplit -= 1
    while maxsplit != 0:
        if index >= end:
            break
        parts.append(W_UnicodeObject([self[index]]))
        index += 1
        maxsplit -= 1
    parts.append(W_UnicodeObject(self[index:]))
    return parts

def unicode_replace__Unicode_Unicode_Unicode_ANY(space, w_self, w_old,
                                                 w_new, w_maxsplit):
    if len(w_old._value):
        w_parts = space.call_method(w_self, 'split', w_old, w_maxsplit)
    else:
        self = w_self._value
        maxsplit = space.int_w(w_maxsplit)
        w_parts = space.newlist(_split(space, self, maxsplit))
    return space.call_method(w_new, 'join', w_parts)
    

app = gateway.applevel(r'''
import sys

def unicode_expandtabs__Unicode_ANY(self, tabsize):
    parts = self.split(u'\t')
    result = [ parts[0] ]
    prevsize = 0
    for ch in parts[0]:
        prevsize += 1
        if ch in (u"\n", u"\r"):
            prevsize = 0
    for i in range(1, len(parts)):
        pad = tabsize - prevsize % tabsize
        result.append(u' ' * pad)
        nextpart = parts[i]
        result.append(nextpart)
        prevsize = 0
        for ch in nextpart:
            prevsize += 1
            if ch in (u"\n", u"\r"):
                prevsize = 0
    return u''.join(result)

def unicode_translate__Unicode_ANY(self, table):
    result = []
    for unichar in self:
        try:
            newval = table[ord(unichar)]
        except KeyError:
            result.append(unichar)
        else:
            if newval is None:
                continue
            elif isinstance(newval, int):
                if newval < 0 or newval > sys.maxunicode:
                    raise TypeError("character mapping must be in range(0x%x)"%(sys.maxunicode + 1,))
                result.append(unichr(newval))
            elif isinstance(newval, unicode):
                result.append(newval)
            else:
                raise TypeError("character mapping must return integer, None or unicode")
    return ''.join(result)

def unicode_encode__Unicode_ANY_ANY(unistr, encoding=None, errors=None):
    import codecs, sys
    if encoding is None:
        encoding = sys.getdefaultencoding()

    encoder = codecs.getencoder(encoding)
    if errors is None:
        retval, lenght = encoder(unistr)
    else:
        retval, length = encoder(unistr, errors)
    if not isinstance(retval,str):
        raise TypeError("encoder did not return a string object (type=%s)" %
                        type(retval).__name__)
    return retval

# XXX: These should probably be written on interplevel 

def unicode_partition__Unicode_Unicode(unistr, unisub):
    pos = unistr.find(unisub)
    if pos == -1:
        return (unistr, u'', u'')
    else:
        return (unistr[:pos], unisub, unistr[pos+len(unisub):])

def unicode_rpartition__Unicode_Unicode(unistr, unisub):
    pos = unistr.rfind(unisub)
    if pos == -1:
        return (u'', u'', unistr)
    else:
        return (unistr[:pos], unisub, unistr[pos+len(unisub):])

def unicode_startswith__Unicode_Tuple_ANY_ANY(unistr, prefixes, start, end):
    for prefix in prefixes:
        if unistr.startswith(prefix):
            return True
    return False

def unicode_endswith__Unicode_Tuple_ANY_ANY(unistr, suffixes, start, end):
    for suffix in suffixes:
        if unistr.endswith(suffix):
            return True
    return False

''')

unicode_expandtabs__Unicode_ANY = app.interphook('unicode_expandtabs__Unicode_ANY')
unicode_translate__Unicode_ANY = app.interphook('unicode_translate__Unicode_ANY')
unicode_encode__Unicode_ANY_ANY = app.interphook('unicode_encode__Unicode_ANY_ANY')
unicode_partition__Unicode_Unicode = app.interphook('unicode_partition__Unicode_Unicode')
unicode_rpartition__Unicode_Unicode = app.interphook('unicode_rpartition__Unicode_Unicode')
unicode_startswith__Unicode_Tuple_ANY_ANY = app.interphook('unicode_startswith__Unicode_Tuple_ANY_ANY')
unicode_endswith__Unicode_Tuple_ANY_ANY = app.interphook('unicode_endswith__Unicode_Tuple_ANY_ANY')

# Move this into the _codecs module as 'unicodeescape_string (Remember to cater for quotes)'
def repr__Unicode(space, w_unicode):
    hexdigits = "0123456789abcdef"
    chars = w_unicode._value
    size = len(chars)
    
    singlequote = doublequote = False
    for c in chars:
        if c == u'\'':
            singlequote = True
        elif c == u'"':
            doublequote = True
    if singlequote and not doublequote:
        quote = '"'
    else:
        quote = '\''
    result = ['\0'] * (2 + size*6 + 1)
    result[0] = 'u'
    result[1] = quote
    i = 2
    j = 0
    while j<len(chars):
        ch = chars[j]
##        if ch == u"'":
##            quote ='''"'''
##            result[1] = quote
##            result[i] = '\''
##            #result[i + 1] = "'"
##            i += 1
##            continue
        code = ord(ch)
        if code >= 0x10000:
            # Resize if needed
            if i + 12 > len(result):
                result.extend(['\0'] * 100)
            result[i] = '\\'
            result[i + 1] = "U"
            result[i + 2] = hexdigits[(code >> 28) & 0xf] 
            result[i + 3] = hexdigits[(code >> 24) & 0xf] 
            result[i + 4] = hexdigits[(code >> 20) & 0xf] 
            result[i + 5] = hexdigits[(code >> 16) & 0xf] 
            result[i + 6] = hexdigits[(code >> 12) & 0xf] 
            result[i + 7] = hexdigits[(code >>  8) & 0xf] 
            result[i + 8] = hexdigits[(code >>  4) & 0xf] 
            result[i + 9] = hexdigits[(code >>  0) & 0xf]
            i += 10
            j += 1
            continue
        if code >= 0xD800 and code < 0xDC00:
            if j < size - 1:
                ch2 = chars[j+1]
                code2 = ord(ch2)
                if code2 >= 0xDC00 and code2 <= 0xDFFF:
                    code = (((code & 0x03FF) << 10) | (code2 & 0x03FF)) + 0x00010000
                    if i + 12 > len(result):
                        result.extend(['\0'] * 100)
                    result[i] = '\\'
                    result[i + 1] = "U"
                    result[i + 2] = hexdigits[(code >> 28) & 0xf] 
                    result[i + 3] = hexdigits[(code >> 24) & 0xf] 
                    result[i + 4] = hexdigits[(code >> 20) & 0xf] 
                    result[i + 5] = hexdigits[(code >> 16) & 0xf] 
                    result[i + 6] = hexdigits[(code >> 12) & 0xf] 
                    result[i + 7] = hexdigits[(code >>  8) & 0xf] 
                    result[i + 8] = hexdigits[(code >>  4) & 0xf] 
                    result[i + 9] = hexdigits[(code >>  0) & 0xf]
                    i += 10
                    j += 2
                    continue
                
        if code >= 0x100:
            result[i] = '\\'
            result[i + 1] = "u"
            result[i + 2] = hexdigits[(code >> 12) & 0xf] 
            result[i + 3] = hexdigits[(code >>  8) & 0xf] 
            result[i + 4] = hexdigits[(code >>  4) & 0xf] 
            result[i + 5] = hexdigits[(code >>  0) & 0xf] 
            i += 6
            j += 1
            continue
        if code == ord('\\') or code == ord(quote):
            result[i] = '\\'
            result[i + 1] = chr(code)
            i += 2
            j += 1
            continue
        if code == ord('\t'):
            result[i] = '\\'
            result[i + 1] = "t"
            i += 2
            j += 1
            continue
        if code == ord('\r'):
            result[i] = '\\'
            result[i + 1] = "r"
            i += 2
            j += 1
            continue
        if code == ord('\n'):
            result[i] = '\\'
            result[i + 1] = "n"
            i += 2
            j += 1
            continue
        if code < ord(' ') or code >= 0x7f:
            result[i] = '\\'
            result[i + 1] = "x"
            result[i + 2] = hexdigits[(code >> 4) & 0xf] 
            result[i + 3] = hexdigits[(code >> 0) & 0xf] 
            i += 4
            j += 1
            continue
        result[i] = chr(code)
        i += 1
        j += 1
    result[i] = quote
    i += 1
    return space.wrap(''.join(result[:i]))
        
#repr__Unicode = app.interphook('repr__Unicode') # uncomment when repr code is moved to _codecs

def mod__Unicode_ANY(space, w_format, w_values):
    return mod_format(space, w_format, w_values, do_unicode=True)


import unicodetype
register_all(vars(), unicodetype)

# str.strip(unicode) needs to convert self to unicode and call unicode.strip
# we use the following magic to register strip_string_unicode as a String multimethod.
class str_methods:
    import stringtype
    W_UnicodeObject = W_UnicodeObject
    from pypy.objspace.std.stringobject import W_StringObject
    from pypy.objspace.std.ropeobject import W_RopeObject
    def str_strip__String_Unicode(space, w_self, w_chars):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'strip', w_chars)
    str_strip__Rope_Unicode = str_strip__String_Unicode
    def str_lstrip__String_Unicode(space, w_self, w_chars):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'lstrip', w_chars)
    str_lstrip__Rope_Unicode = str_lstrip__String_Unicode
    def str_rstrip__String_Unicode(space, w_self, w_chars):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'rstrip', w_chars)
    str_rstrip__Rope_Unicode = str_rstrip__String_Unicode
    def str_count__String_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'count', w_substr, w_start, w_end)
    str_count__Rope_Unicode_ANY_ANY = str_count__String_Unicode_ANY_ANY
    def str_find__String_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'find', w_substr, w_start, w_end)
    str_find__Rope_Unicode_ANY_ANY = str_find__String_Unicode_ANY_ANY
    def str_rfind__String_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'rfind', w_substr, w_start, w_end)
    str_rfind__Rope_Unicode_ANY_ANY = str_rfind__String_Unicode_ANY_ANY
    def str_index__String_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'index', w_substr, w_start, w_end)
    str_index__Rope_Unicode_ANY_ANY = str_index__String_Unicode_ANY_ANY
    def str_rindex__String_Unicode_ANY_ANY(space, w_self, w_substr, w_start, w_end):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'rindex', w_substr, w_start, w_end)
    str_rindex__Rope_Unicode_ANY_ANY = str_rindex__String_Unicode_ANY_ANY
    def str_replace__String_Unicode_Unicode_ANY(space, w_self, w_old, w_new, w_maxsplit):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'replace', w_old, w_new, w_maxsplit)
    str_replace__Rope_Unicode_Unicode_ANY = str_replace__String_Unicode_Unicode_ANY
    def str_split__String_Unicode_ANY(space, w_self, w_delim, w_maxsplit):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'split', w_delim, w_maxsplit)
    str_split__Rope_Unicode_ANY = str_split__String_Unicode_ANY
    def str_rsplit__String_Unicode_ANY(space, w_self, w_delim, w_maxsplit):
        return space.call_method(space.call_function(space.w_unicode, w_self),
                                 'rsplit', w_delim, w_maxsplit)
    str_rsplit__Rope_Unicode_ANY = str_rsplit__String_Unicode_ANY
    register_all(vars(), stringtype)
