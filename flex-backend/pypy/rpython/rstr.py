from pypy.tool.staticmethods import StaticMethods
from pypy.annotation.pairtype import pairtype, pair
from pypy.annotation import model as annmodel
from pypy.rpython.error import TyperError
from pypy.rpython.rmodel import IntegerRepr, IteratorRepr
from pypy.rpython.rmodel import inputconst, Repr
from pypy.rpython.rtuple import AbstractTupleRepr
from pypy.rpython.rslice import AbstractSliceRepr
from pypy.rpython import rint
from pypy.rpython.lltypesystem.lltype import Signed, Bool, Void, UniChar

class AbstractStringRepr(Repr):
    pass

class AbstractCharRepr(AbstractStringRepr):
    pass

class AbstractUniCharRepr(Repr):
    pass


class __extend__(annmodel.SomeString):
    def rtyper_makerepr(self, rtyper):
        return rtyper.type_system.rstr.string_repr
    def rtyper_makekey(self):
        return self.__class__,

class __extend__(annmodel.SomeChar):
    def rtyper_makerepr(self, rtyper):
        return rtyper.type_system.rstr.char_repr
    def rtyper_makekey(self):
        return self.__class__,

class __extend__(annmodel.SomeUnicodeCodePoint):
    def rtyper_makerepr(self, rtyper):
        return rtyper.type_system.rstr.unichar_repr
    def rtyper_makekey(self):
        return self.__class__,


class __extend__(AbstractStringRepr):

    def get_ll_eq_function(self):
        return self.ll.ll_streq

    def get_ll_hash_function(self):
        return self.ll.ll_strhash

    def get_ll_fasthash_function(self):
        return self.ll.ll_strfasthash

    def rtype_len(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        return hop.gendirectcall(self.ll.ll_strlen, v_str)

    def rtype_is_true(self, hop):
        s_str = hop.args_s[0]
        if s_str.can_be_None:
            string_repr = hop.rtyper.type_system.rstr.string_repr
            v_str, = hop.inputargs(string_repr)
            return hop.gendirectcall(self.ll.ll_str_is_true, v_str)
        else:
            # defaults to checking the length
            return super(AbstractStringRepr, self).rtype_is_true(hop)

    def rtype_ord(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        c_zero = inputconst(Signed, 0)
        v_chr = hop.gendirectcall(self.ll.ll_stritem_nonneg, v_str, c_zero)
        return hop.genop('cast_char_to_int', [v_chr], resulttype=Signed)

    def rtype_method_startswith(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, v_value = hop.inputargs(string_repr, string_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_startswith, v_str, v_value)

    def rtype_method_endswith(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, v_value = hop.inputargs(string_repr, string_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_endswith, v_str, v_value)

    def rtype_method_find(self, hop, reverse=False):
        rstr = hop.rtyper.type_system.rstr        
        v_str = hop.inputarg(rstr.string_repr, arg=0)
        if hop.args_r[1] == rstr.char_repr:
            v_value = hop.inputarg(rstr.char_repr, arg=1)
            llfn = reverse and self.ll.ll_rfind_char or self.ll.ll_find_char
        else:
            v_value = hop.inputarg(rstr.string_repr, arg=1)
            llfn = reverse and self.ll.ll_rfind or self.ll.ll_find
        if hop.nb_args > 2:
            v_start = hop.inputarg(Signed, arg=2)
            if not hop.args_s[2].nonneg:
                raise TyperError("str.find() start must be proven non-negative")
        else:
            v_start = hop.inputconst(Signed, 0)
        if hop.nb_args > 3:
            v_end = hop.inputarg(Signed, arg=3)
            if not hop.args_s[2].nonneg:
                raise TyperError("str.find() end must be proven non-negative")
        else:
            v_end = hop.gendirectcall(self.ll.ll_strlen, v_str)
        hop.exception_cannot_occur()
        return hop.gendirectcall(llfn, v_str, v_value, v_start, v_end)

    def rtype_method_rfind(self, hop):
        return self.rtype_method_find(hop, reverse=True)

    def rtype_method_count(self, hop):
        rstr = hop.rtyper.type_system.rstr
        v_str = hop.inputarg(rstr.string_repr, arg=0)
        if hop.args_r[1] == rstr.char_repr:
            v_value = hop.inputarg(rstr.char_repr, arg=1)
            llfn = self.ll.ll_count_char
        else:
            v_value = hop.inputarg(rstr.string_repr, arg=1)
            llfn = self.ll.ll_count
        if hop.nb_args > 2:
            v_start = hop.inputarg(Signed, arg=2)
            if not hop.args_s[2].nonneg:
                raise TyperError("str.count() start must be proven non-negative")
        else:
            v_start = hop.inputconst(Signed, 0)
        if hop.nb_args > 3:
            v_end = hop.inputarg(Signed, arg=3)
            if not hop.args_s[2].nonneg:
                raise TyperError("str.count() end must be proven non-negative")
        else:
            v_end = hop.gendirectcall(self.ll.ll_strlen, v_str)
        hop.exception_cannot_occur()
        return hop.gendirectcall(llfn, v_str, v_value, v_start, v_end)

    def rtype_method_strip(self, hop, left=True, right=True):
        rstr = hop.rtyper.type_system.rstr
        v_str = hop.inputarg(rstr.string_repr, arg=0)
        v_char = hop.inputarg(rstr.char_repr, arg=1)
        v_left = hop.inputconst(Bool, left)
        v_right = hop.inputconst(Bool, right)
        return hop.gendirectcall(self.ll.ll_strip, v_str, v_char, v_left, v_right)

    def rtype_method_lstrip(self, hop):
        return self.rtype_method_strip(hop, left=True, right=False)

    def rtype_method_rstrip(self, hop):
        return self.rtype_method_strip(hop, left=False, right=True)

    def rtype_method_upper(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_upper, v_str)
        
    def rtype_method_lower(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_lower, v_str)

    def _list_length_items(self, hop, v_lst, LIST):
        """Return two Variables containing the length and items of a
        list. Need to be overriden because it is typesystem-specific."""
        raise NotImplementedError

    def rtype_method_join(self, hop):
        hop.exception_cannot_occur()
        rstr = hop.rtyper.type_system.rstr
        if hop.s_result.is_constant():
            return inputconst(rstr.string_repr, hop.s_result.const)
        r_lst = hop.args_r[1]
        if not isinstance(r_lst, hop.rtyper.type_system.rlist.BaseListRepr):
            raise TyperError("string.join of non-list: %r" % r_lst)
        v_str, v_lst = hop.inputargs(rstr.string_repr, r_lst)
        v_length, v_items = self._list_length_items(hop, v_lst, r_lst.lowleveltype)

        if hop.args_s[0].is_constant() and hop.args_s[0].const == '':
            if r_lst.item_repr == rstr.string_repr:
                llfn = self.ll.ll_join_strs
            elif r_lst.item_repr == rstr.char_repr:
                llfn = self.ll.ll_join_chars
            else:
                raise TyperError("''.join() of non-string list: %r" % r_lst)
            return hop.gendirectcall(llfn, v_length, v_items)
        else:
            if r_lst.item_repr == rstr.string_repr:
                llfn = self.ll.ll_join
            else:
                raise TyperError("sep.join() of non-string list: %r" % r_lst)
            return hop.gendirectcall(llfn, v_str, v_length, v_items)

    def rtype_method_split(self, hop):
        rstr = hop.rtyper.type_system.rstr
        v_str, v_chr = hop.inputargs(rstr.string_repr, rstr.char_repr)
        try:
            list_type = hop.r_result.lowleveltype.TO
        except AttributeError:
            list_type = hop.r_result.lowleveltype
        cLIST = hop.inputconst(Void, list_type)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_split_chr, cLIST, v_str, v_chr)

    def rtype_method_replace(self, hop):
        rstr = hop.rtyper.type_system.rstr        
        if not (hop.args_r[1] == rstr.char_repr and hop.args_r[2] == rstr.char_repr):
            raise TyperError, 'replace only works for char args'
        v_str, v_c1, v_c2 = hop.inputargs(rstr.string_repr, rstr.char_repr, rstr.char_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(self.ll.ll_replace_chr_chr, v_str, v_c1, v_c2)

    def rtype_int(self, hop):
        hop.has_implicit_exception(ValueError)   # record that we know about it
        string_repr = hop.rtyper.type_system.rstr.string_repr
        if hop.nb_args == 1:
            v_str, = hop.inputargs(string_repr)
            c_base = inputconst(Signed, 10)
            hop.exception_is_here()
            return hop.gendirectcall(self.ll.ll_int, v_str, c_base)
        if not hop.args_r[1] == rint.signed_repr:
            raise TyperError, 'base needs to be an int'
        v_str, v_base= hop.inputargs(string_repr, rint.signed_repr)
        hop.exception_is_here()
        return hop.gendirectcall(self.ll.ll_int, v_str, v_base)

    def rtype_float(self, hop):
        hop.has_implicit_exception(ValueError)   # record that we know about it
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        hop.exception_is_here()
        return hop.gendirectcall(self.ll.ll_float, v_str)

    def ll_str(self, s):
        return s


class __extend__(pairtype(AbstractStringRepr, Repr)):
    def rtype_mod((r_str, _), hop):
        # for the case where the 2nd argument is a tuple, see the
        # overriding rtype_mod() below
        return r_str.ll.do_stringformat(hop, [(hop.args_v[1], hop.args_r[1])])


class __extend__(pairtype(AbstractStringRepr, IntegerRepr)):
    def rtype_getitem((r_str, r_int), hop, checkidx=False):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, v_index = hop.inputargs(string_repr, Signed)
        if checkidx:
            if hop.args_s[1].nonneg:
                llfn = r_str.ll.ll_stritem_nonneg_checked
            else:
                llfn = r_str.ll.ll_stritem_checked
        else:
            if hop.args_s[1].nonneg:
                llfn = r_str.ll.ll_stritem_nonneg
            else:
                llfn = r_str.ll.ll_stritem
        if checkidx:
            hop.exception_is_here()
        else:
            hop.exception_cannot_occur()
        return hop.gendirectcall(llfn, v_str, v_index)

    rtype_getitem_key = rtype_getitem

    def rtype_getitem_idx((r_str, r_int), hop):
        return pair(r_str, r_int).rtype_getitem(hop, checkidx=True)

    rtype_getitem_idx_key = rtype_getitem_idx


class __extend__(pairtype(AbstractStringRepr, AbstractSliceRepr)):

    def rtype_getitem((r_str, r_slic), hop):
        rstr = hop.rtyper.type_system.rstr
        rslice = hop.rtyper.type_system.rslice

        if r_slic == rslice.startonly_slice_repr:
            v_str, v_start = hop.inputargs(rstr.string_repr, rslice.startonly_slice_repr)
            return hop.gendirectcall(r_str.ll.ll_stringslice_startonly, v_str, v_start)
        if r_slic == rslice.startstop_slice_repr:
            v_str, v_slice = hop.inputargs(rstr.string_repr, rslice.startstop_slice_repr)
            return hop.gendirectcall(r_str.ll.ll_stringslice, v_str, v_slice)
        if r_slic == rslice.minusone_slice_repr:
            v_str, v_ignored = hop.inputargs(rstr.string_repr, rslice.minusone_slice_repr)
            return hop.gendirectcall(r_str.ll.ll_stringslice_minusone, v_str)
        raise TyperError(r_slic)


class __extend__(pairtype(AbstractStringRepr, AbstractStringRepr)):
    def rtype_add((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        if hop.s_result.is_constant():
            return hop.inputconst(string_repr, hop.s_result.const)
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        return hop.gendirectcall(r_str1.ll.ll_strconcat, v_str1, v_str2)
    rtype_inplace_add = rtype_add

    def rtype_eq((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        return hop.gendirectcall(r_str1.ll.ll_streq, v_str1, v_str2)
    
    def rtype_ne((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        vres = hop.gendirectcall(r_str1.ll.ll_streq, v_str1, v_str2)
        return hop.genop('bool_not', [vres], resulttype=Bool)

    def rtype_lt((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        vres = hop.gendirectcall(r_str1.ll.ll_strcmp, v_str1, v_str2)
        return hop.genop('int_lt', [vres, hop.inputconst(Signed, 0)],
                         resulttype=Bool)

    def rtype_le((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        vres = hop.gendirectcall(r_str1.ll.ll_strcmp, v_str1, v_str2)
        return hop.genop('int_le', [vres, hop.inputconst(Signed, 0)],
                         resulttype=Bool)

    def rtype_ge((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        vres = hop.gendirectcall(r_str1.ll.ll_strcmp, v_str1, v_str2)
        return hop.genop('int_ge', [vres, hop.inputconst(Signed, 0)],
                         resulttype=Bool)

    def rtype_gt((r_str1, r_str2), hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str1, v_str2 = hop.inputargs(string_repr, string_repr)
        vres = hop.gendirectcall(r_str1.ll.ll_strcmp, v_str1, v_str2)
        return hop.genop('int_gt', [vres, hop.inputconst(Signed, 0)],
                         resulttype=Bool)

class __extend__(pairtype(AbstractStringRepr, AbstractCharRepr)):
    def rtype_contains((r_str, r_chr), hop):
        rstr = hop.rtyper.type_system.rstr
        v_str, v_chr = hop.inputargs(rstr.string_repr, rstr.char_repr)
        return hop.gendirectcall(r_str.ll.ll_contains, v_str, v_chr)

class __extend__(pairtype(AbstractStringRepr, AbstractTupleRepr)):
    def rtype_mod((r_str, r_tuple), hop):
        r_tuple = hop.args_r[1]
        v_tuple = hop.args_v[1]

        sourcevars = []
        for i, r_arg in enumerate(r_tuple.external_items_r):
            v_item = r_tuple.getitem(hop.llops, v_tuple, i)
            sourcevars.append((v_item, r_arg))

        return r_str.ll.do_stringformat(hop, sourcevars)
                

class __extend__(AbstractCharRepr):

    def convert_const(self, value):
        if not isinstance(value, str) or len(value) != 1:
            raise TyperError("not a character: %r" % (value,))
        return value

    def get_ll_eq_function(self):
        return None 

    def get_ll_hash_function(self):
        return self.ll.ll_char_hash

    get_ll_fasthash_function = get_ll_hash_function

    def ll_str(self, ch):
        return self.ll.ll_chr2str(ch)

    def rtype_len(_, hop):
        return hop.inputconst(Signed, 1)

    def rtype_is_true(_, hop):
        assert not hop.args_s[0].can_be_None
        return hop.inputconst(Bool, True)

    def rtype_ord(_, hop):
        rstr = hop.rtyper.type_system.rstr
        vlist = hop.inputargs(rstr.char_repr)
        return hop.genop('cast_char_to_int', vlist, resulttype=Signed)

    def _rtype_method_isxxx(_, llfn, hop):
        rstr = hop.rtyper.type_system.rstr
        vlist = hop.inputargs(rstr.char_repr)
        hop.exception_cannot_occur()
        return hop.gendirectcall(llfn, vlist[0])

    def rtype_method_isspace(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_isspace, hop)
    def rtype_method_isdigit(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_isdigit, hop)
    def rtype_method_isalpha(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_isalpha, hop)
    def rtype_method_isalnum(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_isalnum, hop)
    def rtype_method_isupper(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_isupper, hop)
    def rtype_method_islower(self, hop):
        return self._rtype_method_isxxx(self.ll.ll_char_islower, hop)

class __extend__(pairtype(AbstractCharRepr, IntegerRepr)):
    
    def rtype_mul((r_chr, r_int), hop):
        rstr = hop.rtyper.type_system.rstr
        v_char, v_int = hop.inputargs(rstr.char_repr, Signed)
        return hop.gendirectcall(r_chr.ll.ll_char_mul, v_char, v_int)
    rtype_inplace_mul = rtype_mul

class __extend__(pairtype(IntegerRepr, AbstractCharRepr)):
    def rtype_mul((r_int, r_chr), hop):
        rstr = hop.rtyper.type_system.rstr
        v_int, v_char = hop.inputargs(Signed, rstr.char_repr)
        return hop.gendirectcall(r_chr.ll.ll_char_mul, v_char, v_int)
    rtype_inplace_mul = rtype_mul

class __extend__(pairtype(AbstractCharRepr, AbstractCharRepr)):
    def rtype_eq(_, hop): return _rtype_compare_template(hop, 'eq')
    def rtype_ne(_, hop): return _rtype_compare_template(hop, 'ne')
    def rtype_lt(_, hop): return _rtype_compare_template(hop, 'lt')
    def rtype_le(_, hop): return _rtype_compare_template(hop, 'le')
    def rtype_gt(_, hop): return _rtype_compare_template(hop, 'gt')
    def rtype_ge(_, hop): return _rtype_compare_template(hop, 'ge')

#Helper functions for comparisons

def _rtype_compare_template(hop, func):
    rstr = hop.rtyper.type_system.rstr
    vlist = hop.inputargs(rstr.char_repr, rstr.char_repr)
    return hop.genop('char_'+func, vlist, resulttype=Bool)

class __extend__(AbstractUniCharRepr):

    def convert_const(self, value):
        if isinstance(value, str):
            value = unicode(value)
        if not isinstance(value, unicode) or len(value) != 1:
            raise TyperError("not a unicode character: %r" % (value,))
        return value

    def get_ll_eq_function(self):
        return None 

    def get_ll_hash_function(self):
        return self.ll.ll_unichar_hash

    get_ll_fasthash_function = get_ll_hash_function

##    def rtype_len(_, hop):
##        return hop.inputconst(Signed, 1)
##
##    def rtype_is_true(_, hop):
##        assert not hop.args_s[0].can_be_None
##        return hop.inputconst(Bool, True)

    def rtype_ord(_, hop):
        rstr = hop.rtyper.type_system.rstr
        vlist = hop.inputargs(rstr.unichar_repr)
        return hop.genop('cast_unichar_to_int', vlist, resulttype=Signed)


class __extend__(pairtype(AbstractUniCharRepr, AbstractUniCharRepr),
                 pairtype(AbstractCharRepr, AbstractUniCharRepr),
                 pairtype(AbstractUniCharRepr, AbstractCharRepr)):
    def rtype_eq(_, hop): return _rtype_unchr_compare_template(hop, 'eq')
    def rtype_ne(_, hop): return _rtype_unchr_compare_template(hop, 'ne')
##    def rtype_lt(_, hop): return _rtype_unchr_compare_template(hop, 'lt')
##    def rtype_le(_, hop): return _rtype_unchr_compare_template(hop, 'le')
##    def rtype_gt(_, hop): return _rtype_unchr_compare_template(hop, 'gt')
##    def rtype_ge(_, hop): return _rtype_unchr_compare_template(hop, 'ge')

#Helper functions for comparisons

def _rtype_unchr_compare_template(hop, func):
    rstr = hop.rtyper.type_system.rstr
    vlist = hop.inputargs(rstr.unichar_repr, rstr.unichar_repr)
    return hop.genop('unichar_'+func, vlist, resulttype=Bool)


#
# _________________________ Conversions _________________________

class __extend__(pairtype(AbstractCharRepr, AbstractStringRepr)):
    def convert_from_to((r_from, r_to), v, llops):
        rstr = llops.rtyper.type_system.rstr
        if r_from == rstr.char_repr and r_to == rstr.string_repr:
            return llops.gendirectcall(r_from.ll.ll_chr2str, v)
        return NotImplemented

class __extend__(pairtype(AbstractStringRepr, AbstractCharRepr)):
    def convert_from_to((r_from, r_to), v, llops):
        rstr = llops.rtyper.type_system.rstr
        if r_from == rstr.string_repr and r_to == rstr.char_repr:
            c_zero = inputconst(Signed, 0)
            return llops.gendirectcall(r_from.ll.ll_stritem_nonneg, v, c_zero)
        return NotImplemented

class __extend__(pairtype(AbstractCharRepr, AbstractUniCharRepr)):
    def convert_from_to((r_from, r_to), v, llops):
        v2 = llops.genop('cast_char_to_int', [v], resulttype=Signed)
        return llops.genop('cast_int_to_unichar', [v2], resulttype=UniChar)

# ____________________________________________________________
#
#  Iteration.

class AbstractStringIteratorRepr(IteratorRepr):

    def newiter(self, hop):
        string_repr = hop.rtyper.type_system.rstr.string_repr
        v_str, = hop.inputargs(string_repr)
        return hop.gendirectcall(self.ll_striter, v_str)

    def rtype_next(self, hop):
        v_iter, = hop.inputargs(self)
        hop.has_implicit_exception(StopIteration) # record that we know about it
        hop.exception_is_here()
        return hop.gendirectcall(self.ll_strnext, v_iter)


# ____________________________________________________________
#
#  Low-level methods.  These can be run for testing, but are meant to
#  be direct_call'ed from rtyped flow graphs, which means that they will
#  get flowed and annotated, mostly with SomePtr.
#

# this class contains low level helpers used both by lltypesystem and
# ootypesystem; each typesystem should subclass it and add its own
# primitives.
class AbstractLLHelpers:
    __metaclass__ = StaticMethods

    def ll_char_isspace(ch):
        c = ord(ch) 
        return c == 32 or (c <= 13 and c >= 9)   # c in (9, 10, 11, 12, 13, 32)

    def ll_char_isdigit(ch):
        c = ord(ch)
        return c <= 57 and c >= 48

    def ll_char_isalpha(ch):
        c = ord(ch)
        if c >= 97:
            return c <= 122
        else:
            return 65 <= c <= 90

    def ll_char_isalnum(ch):
        c = ord(ch)
        if c >= 65:
            if c >= 97:
                return c <= 122
            else:
                return c <= 90
        else:
            return 48 <= c <= 57

    def ll_char_isupper(ch):
        c = ord(ch)
        return 65 <= c <= 90

    def ll_char_islower(ch):   
        c = ord(ch)
        return 97 <= c <= 122

    def ll_char_hash(ch):
        return ord(ch)

    def ll_unichar_hash(ch):
        return ord(ch)

    def ll_str_is_true(cls, s):
        # check if a string is True, allowing for None
        return bool(s) and cls.ll_strlen(s) != 0
    ll_str_is_true = classmethod(ll_str_is_true)

    def ll_stritem_nonneg_checked(cls, s, i):
        if i >= cls.ll_strlen(s):
            raise IndexError
        return cls.ll_stritem_nonneg(s, i)
    ll_stritem_nonneg_checked = classmethod(ll_stritem_nonneg_checked)

    def ll_stritem(cls, s, i):
        if i < 0:
            i += cls.ll_strlen(s)
        return cls.ll_stritem_nonneg(s, i)
    ll_stritem = classmethod(ll_stritem)

    def ll_stritem_checked(cls, s, i):
        length = cls.ll_strlen(s)
        if i < 0:
            i += length
        if i >= length or i < 0:
            raise IndexError
        return cls.ll_stritem_nonneg(s, i)
    ll_stritem_checked = classmethod(ll_stritem_checked)

    def parse_fmt_string(fmt):
        # we support x, d, s, f, [r]
        it = iter(fmt)
        r = []
        curstr = ''
        for c in it:
            if c == '%':
                f = it.next()
                if f == '%':
                    curstr += '%'
                    continue

                if curstr:
                    r.append(curstr)
                curstr = ''
                if f not in 'xdosrf':
                    raise TyperError("Unsupported formatting specifier: %r in %r" % (f, fmt))

                r.append((f,))
            else:
                curstr += c
        if curstr:
            r.append(curstr)
        return r

    def ll_float(ll_str):
        from pypy.rpython.annlowlevel import hlstr
        from pypy.rlib.rarithmetic import break_up_float, parts_to_float
        s = hlstr(ll_str)
        assert s is not None

        n = len(s)
        beg = 0
        while beg < n:
            if s[beg] == ' ':
                beg += 1
            else:
                break
        if beg == n:
            raise ValueError
        end = n-1
        while end >= 0:
            if s[end] == ' ':
                end -= 1
            else:
                break
        assert end >= 0
        sign, before_point, after_point, exponent = break_up_float(s[beg:end+1])
    
        if not before_point and not after_point:
            raise ValueError

        return parts_to_float(sign, before_point, after_point, exponent)
