from pypy.rpython import rclass
from pypy.rpython.extfunctable import standardexceptions
from pypy.annotation import model as annmodel

class AbstractExceptionData:
    """Public information for the code generators to help with exceptions."""
    standardexceptions = standardexceptions

    def __init__(self, rtyper):
        self.make_standard_exceptions(rtyper)
        # (NB. rclass identifies 'Exception' and 'object')
        r_type = rclass.getclassrepr(rtyper, None)
        r_instance = rclass.getinstancerepr(rtyper, None)
        r_type.setup()
        r_instance.setup()
        self.r_exception_type  = r_type
        self.r_exception_value = r_instance
        self.lltype_of_exception_type  = r_type.lowleveltype
        self.lltype_of_exception_value = r_instance.lowleveltype

    def make_standard_exceptions(self, rtyper):
        bk = rtyper.annotator.bookkeeper
        for cls in self.standardexceptions:
            classdef = bk.getuniqueclassdef(cls)

    def finish(self, rtyper):
        bk = rtyper.annotator.bookkeeper
        for cls in self.standardexceptions:
            classdef = bk.getuniqueclassdef(cls)
            rclass.getclassrepr(rtyper, classdef).setup()

    def make_raise_OSError(self, rtyper):
        # ll_raise_OSError(errno)
        def ll_raise_OSError(errno):
            raise OSError(errno, None)
        helper_fn = rtyper.annotate_helper_fn(ll_raise_OSError, [annmodel.SomeInteger()])
        return helper_fn

