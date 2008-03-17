from pypy.interpreter import gateway
from pypy.objspace.std.stdtypedef import *
from pypy.objspace.std.basestringtype import basestring_typedef
from pypy.interpreter.error import OperationError

from sys import maxint

unicode_capitalize = SMM('capitalize', 1,
                         doc='S.capitalize() -> unicode\n\nReturn a'
                             ' capitalized version of S, i.e. make the first'
                             ' character\nhave upper case.')
unicode_center     = SMM('center', 3, defaults=(' ',),
                         doc='S.center(width[, fillchar]) -> unicode\n\nReturn'
                             ' S centered in a Unicode string of length width.'
                             ' Padding is\ndone using the specified fill'
                             ' character (default is a space)')
unicode_count      = SMM('count', 4, defaults=(0, maxint),
                         doc='S.count(sub[, start[, end]]) -> int\n\nReturn'
                             ' the number of occurrences of substring sub in'
                             ' Unicode string\nS[start:end].  Optional'
                             ' arguments start and end are\ninterpreted as in'
                             ' slice notation.')
unicode_encode     = SMM('encode', 3, defaults=(None, None),
                         doc='S.encode([encoding[,errors]]) -> string or'
                             ' unicode\n\nEncodes S using the codec registered'
                             ' for encoding. encoding defaults\nto the default'
                             ' encoding. errors may be given to set a'
                             ' different error\nhandling scheme. Default is'
                             " 'strict' meaning that encoding errors raise\na"
                             ' UnicodeEncodeError. Other possible values are'
                             " 'ignore', 'replace' and\n'xmlcharrefreplace' as"
                             ' well as any other name registered'
                             ' with\ncodecs.register_error that can handle'
                             ' UnicodeEncodeErrors.')
unicode_expandtabs = SMM('expandtabs', 2, defaults=(8,),
                         doc='S.expandtabs([tabsize]) -> unicode\n\nReturn a'
                             ' copy of S where all tab characters are expanded'
                             ' using spaces.\nIf tabsize is not given, a tab'
                             ' size of 8 characters is assumed.')
unicode_isalnum    = SMM('isalnum', 1,
                         doc='S.isalnum() -> bool\n\nReturn True if all'
                             ' characters in S are alphanumeric\nand there is'
                             ' at least one character in S, False otherwise.')
unicode_isalpha    = SMM('isalpha', 1,
                         doc='S.isalpha() -> bool\n\nReturn True if all'
                             ' characters in S are alphabetic\nand there is at'
                             ' least one character in S, False otherwise.')
unicode_isdecimal  = SMM('isdecimal', 1,
                         doc='S.isdecimal() -> bool\n\nReturn True if there'
                             ' are only decimal characters in S,\nFalse'
                             ' otherwise.')
unicode_isdigit    = SMM('isdigit', 1,
                         doc='S.isdigit() -> bool\n\nReturn True if all'
                             ' characters in S are digits\nand there is at'
                             ' least one character in S, False otherwise.')
unicode_islower    = SMM('islower', 1,
                         doc='S.islower() -> bool\n\nReturn True if all cased'
                             ' characters in S are lowercase and there is\nat'
                             ' least one cased character in S, False'
                             ' otherwise.')
unicode_isnumeric  = SMM('isnumeric', 1,
                         doc='S.isnumeric() -> bool\n\nReturn True if there'
                             ' are only numeric characters in S,\nFalse'
                             ' otherwise.')
unicode_isspace    = SMM('isspace', 1,
                         doc='S.isspace() -> bool\n\nReturn True if all'
                             ' characters in S are whitespace\nand there is at'
                             ' least one character in S, False otherwise.')
unicode_istitle    = SMM('istitle', 1,
                         doc='S.istitle() -> bool\n\nReturn True if S is a'
                             ' titlecased string and there is at least'
                             ' one\ncharacter in S, i.e. upper- and titlecase'
                             ' characters may only\nfollow uncased characters'
                             ' and lowercase characters only cased'
                             ' ones.\nReturn False otherwise.')
unicode_isupper    = SMM('isupper', 1,
                         doc='S.isupper() -> bool\n\nReturn True if all cased'
                             ' characters in S are uppercase and there is\nat'
                             ' least one cased character in S, False'
                             ' otherwise.')
unicode_join       = SMM('join', 2,
                         doc='S.join(sequence) -> unicode\n\nReturn a string'
                             ' which is the concatenation of the strings in'
                             ' the\nsequence.  The separator between elements'
                             ' is S.')
unicode_ljust      = SMM('ljust', 3, defaults=(' ',),
                         doc='S.ljust(width[, fillchar]) -> int\n\nReturn S'
                             ' left justified in a Unicode string of length'
                             ' width. Padding is\ndone using the specified'
                             ' fill character (default is a space).')
unicode_lower      = SMM('lower', 1,
                         doc='S.lower() -> unicode\n\nReturn a copy of the'
                             ' string S converted to lowercase.')
unicode_rjust      = SMM('rjust', 3, defaults=(' ',),
                         doc='S.rjust(width[, fillchar]) -> unicode\n\nReturn'
                             ' S right justified in a Unicode string of length'
                             ' width. Padding is\ndone using the specified'
                             ' fill character (default is a space).')
unicode_swapcase   = SMM('swapcase', 1,
                         doc='S.swapcase() -> unicode\n\nReturn a copy of S'
                             ' with uppercase characters converted to'
                             ' lowercase\nand vice versa.')
unicode_title      = SMM('title', 1,
                         doc='S.title() -> unicode\n\nReturn a titlecased'
                             ' version of S, i.e. words start with title'
                             ' case\ncharacters, all remaining cased'
                             ' characters have lower case.')
unicode_translate  = SMM('translate', 2,
                         doc='S.translate(table) -> unicode\n\nReturn a copy'
                             ' of the string S, where all characters have been'
                             ' mapped\nthrough the given translation table,'
                             ' which must be a mapping of\nUnicode ordinals to'
                             ' Unicode ordinals, Unicode strings or'
                             ' None.\nUnmapped characters are left untouched.'
                             ' Characters mapped to None\nare deleted.')
unicode_upper      = SMM('upper', 1,
                         doc='S.upper() -> unicode\n\nReturn a copy of S'
                             ' converted to uppercase.')
unicode_zfill      = SMM('zfill', 2,
                         doc='S.zfill(width) -> unicode\n\nPad a numeric'
                             ' string x with zeros on the left, to fill a'
                             ' field\nof the specified width. The string x is'
                             ' never truncated.')

# stuff imported from stringtype for interoperability

from pypy.objspace.std.stringtype import str_endswith as unicode_endswith
from pypy.objspace.std.stringtype import str_startswith as unicode_startswith
from pypy.objspace.std.stringtype import str_find as unicode_find
from pypy.objspace.std.stringtype import str_index as unicode_index
from pypy.objspace.std.stringtype import str_replace as unicode_replace
from pypy.objspace.std.stringtype import str_rfind as unicode_rfind
from pypy.objspace.std.stringtype import str_rindex as unicode_rindex
from pypy.objspace.std.stringtype import str_split as unicode_split
from pypy.objspace.std.stringtype import str_rsplit as unicode_rsplit
from pypy.objspace.std.stringtype import str_partition as unicode_partition
from pypy.objspace.std.stringtype import str_rpartition as unicode_rpartition
from pypy.objspace.std.stringtype import str_splitlines as unicode_splitlines
from pypy.objspace.std.stringtype import str_strip as unicode_strip
from pypy.objspace.std.stringtype import str_rstrip as unicode_rstrip
from pypy.objspace.std.stringtype import str_lstrip as unicode_lstrip

# ____________________________________________________________

app = gateway.applevel('''
def unicode_from_encoded_object(obj, encoding, errors):
    import codecs, sys
    if encoding is None:
        encoding = sys.getdefaultencoding()
    decoder = codecs.getdecoder(encoding)
    if errors is None:
        retval, length = decoder(obj)
    else:
        retval, length = decoder(obj, errors)
    if not isinstance(retval, unicode):
        raise TypeError("decoder did not return an unicode object (type=%s)" %
                        type(retval).__name__)
    return retval

def unicode_from_object(obj):
    if isinstance(obj, str):
        res = obj
    else:
        try:
            unicode_method = obj.__unicode__
        except AttributeError:
            res = str(obj)
        else:
            res = unicode_method()
    if isinstance(res, unicode):
        return res
    return unicode_from_encoded_object(res, None, "strict")
    
''')
unicode_from_object = app.interphook('unicode_from_object')
unicode_from_encoded_object = app.interphook('unicode_from_encoded_object')

def unicode_from_string(space, w_str):
    # this is a performance and bootstrapping hack
    from pypy.objspace.std.unicodeobject import W_UnicodeObject
    w_encoding = space.call_function(space.sys.get('getdefaultencoding'))
    if not space.eq_w(w_encoding, space.wrap('ascii')):
        return unicode_from_object(space, w_str)
    s = space.str_w(w_str)
    codelist = []
    for i in range(len(s)):
        code = ord(s[i])
        if code >= 128:
            # raising UnicodeDecodeError is messy, so "please crash for me"
            return unicode_from_object(space, w_str)
        codelist.append(unichr(code))
    return W_UnicodeObject(codelist)


def descr__new__(space, w_unicodetype, w_string='', w_encoding=None, w_errors=None):
    # NB. the default value of w_string is really a *wrapped* empty string:
    #     there is gateway magic at work
    from pypy.objspace.std.unicodeobject import W_UnicodeObject
    w_obj = w_string
    w_obj_type = space.type(w_obj)
    
    if space.is_w(w_obj_type, space.w_unicode):
        if (not space.is_w(w_encoding, space.w_None) or
            not space.is_w(w_errors, space.w_None)):
            raise OperationError(space.w_TypeError,
                                 space.wrap('decoding Unicode is not supported'))
        if space.is_w(w_unicodetype, space.w_unicode):
            return w_obj
        w_value = w_obj
    elif (space.is_w(w_encoding, space.w_None) and
          space.is_w(w_errors, space.w_None)):
        if space.is_true(space.isinstance(w_obj, space.w_str)):
            w_value = unicode_from_string(space, w_obj)
        elif space.is_true(space.isinstance(w_obj, space.w_unicode)):
            w_value = w_obj
        else:
            w_value = unicode_from_object(space, w_obj)
    else:
        w_value = unicode_from_encoded_object(space, w_obj, w_encoding, w_errors)
    # help the annotator! also the ._value depends on W_UnicodeObject layout
    assert isinstance(w_value, W_UnicodeObject)
    w_newobj = space.allocate_instance(W_UnicodeObject, w_unicodetype)
    W_UnicodeObject.__init__(w_newobj, w_value._value)
    return w_newobj

# ____________________________________________________________

unicode_typedef = StdTypeDef("unicode", basestring_typedef,
    __new__ = newmethod(descr__new__),
    __doc__ = '''unicode(string [, encoding[, errors]]) -> object

Create a new Unicode object from the given encoded string.
encoding defaults to the current default string encoding.
errors can be 'strict', 'replace' or 'ignore' and defaults to 'strict'.'''
    )

unicode_typedef.custom_hash = True
unicode_typedef.registermethods(globals())
