from pypy.annotation.pairtype import pairtype
from pypy.rpython.error import TyperError
from pypy.rpython.lltypesystem.lltype import Signed, Void, Ptr
from pypy.rpython.rmodel import Repr, IntegerRepr, IteratorRepr
from pypy.objspace.flow.model import Constant
from pypy.rpython.rlist import dum_nocheck, dum_checkidx


class AbstractRangeRepr(Repr):
    def __init__(self, step):
        self.step = step
        if step != 0:
            self.lowleveltype = self.RANGE
        else:
            self.lowleveltype = self.RANGEST

    def _getstep(self, v_rng, hop):
        return hop.genop(self.getfield_opname,
                [v_rng, hop.inputconst(Void, 'step')], resulttype=Signed)

    def rtype_len(self, hop):
        v_rng, = hop.inputargs(self)
        if self.step != 0:
            cstep = hop.inputconst(Signed, self.step)
        else:
            cstep = self._getstep(v_rng, hop)
        return hop.gendirectcall(ll_rangelen, v_rng, cstep)

class __extend__(pairtype(AbstractRangeRepr, IntegerRepr)):

    def rtype_getitem((r_rng, r_int), hop):
        if hop.has_implicit_exception(IndexError):
            spec = dum_checkidx
        else:
            spec = dum_nocheck
        v_func = hop.inputconst(Void, spec)
        v_lst, v_index = hop.inputargs(r_rng, Signed)
        if r_rng.step != 0:
            cstep = hop.inputconst(Signed, r_rng.step)
        else:
            cstep = r_rng._getstep(v_lst, hop)
        if hop.args_s[1].nonneg:
            llfn = ll_rangeitem_nonneg
        else:
            llfn = ll_rangeitem
        hop.exception_is_here()
        return hop.gendirectcall(llfn, v_func, v_lst, v_index, cstep)

# ____________________________________________________________
#
#  Low-level methods.

def _ll_rangelen(start, stop, step):
    if step > 0:
        result = (stop - start + (step-1)) // step
    else:
        result = (start - stop - (step+1)) // (-step)
    if result < 0:
        result = 0
    return result

def ll_rangelen(l, step):
    return _ll_rangelen(l.start, l.stop, step)

def ll_rangeitem_nonneg(func, l, index, step):
    if func is dum_checkidx and index >= _ll_rangelen(l.start, l.stop, step):
        raise IndexError
    return l.start + index * step

def ll_rangeitem(func, l, index, step):
    if func is dum_checkidx:
        length = _ll_rangelen(l.start, l.stop, step)
        if index < 0:
            index += length
        if index < 0 or index >= length:
            raise IndexError
    else:
        if index < 0:
            length = _ll_rangelen(l.start, l.stop, step)
            index += length
    return l.start + index * step

# ____________________________________________________________
#
#  Irregular operations.

def rtype_builtin_range(hop):
    vstep = hop.inputconst(Signed, 1)
    if hop.nb_args == 1:
        vstart = hop.inputconst(Signed, 0)
        vstop, = hop.inputargs(Signed)
    elif hop.nb_args == 2:
        vstart, vstop = hop.inputargs(Signed, Signed)
    else:
        vstart, vstop, vstep = hop.inputargs(Signed, Signed, Signed)
        if isinstance(vstep, Constant) and vstep.value == 0:
            # not really needed, annotator catches it. Just in case...
            raise TyperError("range cannot have a const step of zero")
    if isinstance(hop.r_result, AbstractRangeRepr):
        if hop.r_result.step != 0:
            c_rng = hop.inputconst(Void, hop.r_result.RANGE)
            return hop.gendirectcall(hop.r_result.ll_newrange, c_rng, vstart, vstop)
        else:
            return hop.gendirectcall(hop.r_result.ll_newrangest, vstart, vstop, vstep)
    else:
        # cannot build a RANGE object, needs a real list
        r_list = hop.r_result
        ITEMTYPE = r_list.lowleveltype
        if isinstance(ITEMTYPE, Ptr):
            ITEMTYPE = ITEMTYPE.TO
        cLIST = hop.inputconst(Void, ITEMTYPE)
        return hop.gendirectcall(ll_range2list, cLIST, vstart, vstop, vstep)

rtype_builtin_xrange = rtype_builtin_range

def ll_range2list(LIST, start, stop, step):
    if step == 0:
        raise ValueError
    length = _ll_rangelen(start, stop, step)
    l = LIST.ll_newlist(length)
    if LIST.ITEM is not Void:
        idx = 0
        while idx < length:
            l.ll_setitem_fast(idx, start)
            start += step
            idx += 1
    return l

# ____________________________________________________________
#
#  Iteration.

class AbstractRangeIteratorRepr(IteratorRepr):
    def __init__(self, r_rng):
        self.r_rng = r_rng
        if r_rng.step != 0:
            self.lowleveltype = r_rng.RANGEITER
        else:
            self.lowleveltype = r_rng.RANGESTITER

    def newiter(self, hop):
        v_rng, = hop.inputargs(self.r_rng)
        citerptr = hop.inputconst(Void, self.lowleveltype)
        return hop.gendirectcall(self.ll_rangeiter, citerptr, v_rng)

    def rtype_next(self, hop):
        v_iter, = hop.inputargs(self)
        args = hop.inputconst(Signed, self.r_rng.step),
        if self.r_rng.step > 0:
            llfn = ll_rangenext_up
        elif self.r_rng.step < 0:
            llfn = ll_rangenext_down
        else:
            llfn = ll_rangenext_updown
            args = ()
        hop.has_implicit_exception(StopIteration) # record that we know about it
        hop.exception_is_here()
        return hop.gendirectcall(llfn, v_iter, *args)

def ll_rangenext_up(iter, step):
    next = iter.next
    if next >= iter.stop:
        raise StopIteration
    iter.next = next + step
    return next

def ll_rangenext_down(iter, step):
    next = iter.next
    if next <= iter.stop:
        raise StopIteration
    iter.next = next + step
    return next

def ll_rangenext_updown(iter):
    step = iter.step
    if step > 0:
        return ll_rangenext_up(iter, step)
    else:
        return ll_rangenext_down(iter, step)
