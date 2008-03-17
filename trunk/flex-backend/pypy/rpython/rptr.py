from pypy.annotation.pairtype import pairtype
from pypy.annotation import model as annmodel
from pypy.objspace.flow import model as flowmodel
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.error import TyperError
from pypy.rpython.rmodel import Repr, IntegerRepr
from pypy.rlib.rarithmetic import r_uint


class __extend__(annmodel.SomePtr):
    def rtyper_makerepr(self, rtyper):
##        if self.is_constant() and not self.const:   # constant NULL
##            return nullptr_repr
##        else:
        return PtrRepr(self.ll_ptrtype)
    def rtyper_makekey(self):
##        if self.is_constant() and not self.const:
##            return None
##        else:
        return self.__class__, self.ll_ptrtype


class PtrRepr(Repr):

    def __init__(self, ptrtype):
        assert isinstance(ptrtype, lltype.Ptr)
        self.lowleveltype = ptrtype

    def ll_str(self, p):
        from pypy.rpython.lltypesystem.rstr import ll_str
        id = lltype.cast_ptr_to_int(p)
        return ll_str.ll_int2hex(r_uint(id), True)

    def rtype_getattr(self, hop):
        attr = hop.args_s[1].const
        if isinstance(hop.s_result, annmodel.SomeLLADTMeth):
            return hop.inputarg(hop.r_result, arg=0)
        FIELD_TYPE = getattr(self.lowleveltype.TO, attr)
        if isinstance(FIELD_TYPE, lltype.ContainerType):
            newopname = 'getsubstruct'
        else:
            newopname = 'getfield'
        vlist = hop.inputargs(self, lltype.Void)
        return hop.genop(newopname, vlist,
                         resulttype = hop.r_result.lowleveltype)

    def rtype_setattr(self, hop):
        attr = hop.args_s[1].const
        FIELD_TYPE = getattr(self.lowleveltype.TO, attr)
        assert not isinstance(FIELD_TYPE, lltype.ContainerType)
        vlist = hop.inputargs(self, lltype.Void, hop.args_r[2])
        hop.genop('setfield', vlist)

    def rtype_len(self, hop):
        ARRAY = hop.args_r[0].lowleveltype.TO
        if isinstance(ARRAY, lltype.FixedSizeArray):
            return hop.inputconst(lltype.Signed, ARRAY.length)
        else:
            vlist = hop.inputargs(self)
            return hop.genop('getarraysize', vlist,
                             resulttype = hop.r_result.lowleveltype)

    def rtype_is_true(self, hop):
        vlist = hop.inputargs(self)
        return hop.genop('ptr_nonzero', vlist, resulttype=lltype.Bool)

    def rtype_simple_call(self, hop):
        if not isinstance(self.lowleveltype.TO, lltype.FuncType):
            raise TyperError("calling a non-function %r", self.lowleveltype.TO)
        vlist = hop.inputargs(*hop.args_r)
        nexpected = len(self.lowleveltype.TO.ARGS)
        nactual = len(vlist)-1
        if nactual != nexpected: 
            raise TyperError("argcount mismatch:  expected %d got %d" %
                            (nexpected, nactual))
        if isinstance(vlist[0], flowmodel.Constant):
            if hasattr(vlist[0].value, 'graph'):
                hop.llops.record_extra_call(vlist[0].value.graph)
            opname = 'direct_call'
        else:
            opname = 'indirect_call'
            vlist.append(hop.inputconst(lltype.Void, None))
        hop.exception_is_here()
        return hop.genop(opname, vlist,
                         resulttype = self.lowleveltype.TO.RESULT)

    def rtype_call_args(self, hop):
        from pypy.rpython.rbuiltin import call_args_expand
        hop, _ = call_args_expand(hop, takes_kwds=False)
        hop.swap_fst_snd_args()
        hop.r_s_popfirstarg()
        return self.rtype_simple_call(hop)
        

class __extend__(pairtype(PtrRepr, IntegerRepr)):

    def rtype_getitem((r_ptr, r_int), hop):
        ARRAY = r_ptr.lowleveltype.TO
        ITEM_TYPE = ARRAY.OF
        if isinstance(ITEM_TYPE, lltype.ContainerType):
            newopname = 'getarraysubstruct'
        else:
            newopname = 'getarrayitem'
        vlist = hop.inputargs(r_ptr, lltype.Signed)
        return hop.genop(newopname, vlist,
                         resulttype = hop.r_result.lowleveltype)

    def rtype_setitem((r_ptr, r_int), hop):
        ARRAY = r_ptr.lowleveltype.TO
        ITEM_TYPE = ARRAY.OF
        assert not isinstance(ITEM_TYPE, lltype.ContainerType)
        vlist = hop.inputargs(r_ptr, lltype.Signed, hop.args_r[2])
        hop.genop('setarrayitem', vlist)

# ____________________________________________________________
#
#  Null Pointers

##class NullPtrRepr(Repr):
##    lowleveltype = lltype.Void

##    def rtype_is_true(self, hop):
##        return hop.inputconst(lltype.Bool, False)

##nullptr_repr = NullPtrRepr()

##class __extend__(pairtype(NullPtrRepr, PtrRepr)):
##    def convert_from_to((r_null, r_ptr), v, llops):
##        # nullptr to general pointer
##        return inputconst(r_ptr, _ptr(r_ptr.lowleveltype, None))

# ____________________________________________________________
#
#  Comparisons

class __extend__(pairtype(PtrRepr, Repr)):

    def rtype_eq((r_ptr, r_any), hop):
        vlist = hop.inputargs(r_ptr, r_ptr)
        return hop.genop('ptr_eq', vlist, resulttype=lltype.Bool)

    def rtype_ne((r_ptr, r_any), hop):
        vlist = hop.inputargs(r_ptr, r_ptr)
        return hop.genop('ptr_ne', vlist, resulttype=lltype.Bool)


class __extend__(pairtype(Repr, PtrRepr)):

    def rtype_eq((r_any, r_ptr), hop):
        vlist = hop.inputargs(r_ptr, r_ptr)
        return hop.genop('ptr_eq', vlist, resulttype=lltype.Bool)

    def rtype_ne((r_any, r_ptr), hop):
        vlist = hop.inputargs(r_ptr, r_ptr)
        return hop.genop('ptr_ne', vlist, resulttype=lltype.Bool)

# ________________________________________________________________
# ADT  methods

class __extend__(annmodel.SomeLLADTMeth):
    def rtyper_makerepr(self, rtyper):
        return LLADTMethRepr(self)
    def rtyper_makekey(self):
        return self.__class__, self.ll_ptrtype, self.func

class LLADTMethRepr(Repr):

    def __init__(self, adtmeth):
        self.func = adtmeth.func
        self.lowleveltype = adtmeth.ll_ptrtype

    def rtype_simple_call(self, hop):
        hop2 = hop.copy()
        func = self.func
        s_func = hop.rtyper.annotator.bookkeeper.immutablevalue(func)
        v_ptr = hop2.args_v[0]
        hop2.r_s_popfirstarg()
        hop2.v_s_insertfirstarg(v_ptr, annmodel.SomePtr(self.lowleveltype))
        hop2.v_s_insertfirstarg(flowmodel.Constant(func), s_func)
        return hop2.dispatch()

class __extend__(pairtype(PtrRepr, LLADTMethRepr)):

    def convert_from_to((r_from, r_to), v, llops):
        if r_from.lowleveltype == r_to.lowleveltype:
            return v
        return NotImplemented

    
