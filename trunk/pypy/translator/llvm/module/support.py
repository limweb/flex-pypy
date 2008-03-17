
extdeclarations = """
%last_exception_type  = internal global %RPYTHON_EXCEPTION_VTABLE* null
%last_exception_value = internal global %RPYTHON_EXCEPTION* null

declare ccc uint %strlen(sbyte*)
declare ccc void %llvm.memsetPOSTFIX(sbyte*, ubyte, UWORD, UWORD)
declare ccc void %llvm.memcpyPOSTFIX(sbyte*, sbyte*, UWORD, UWORD)
"""

extfunctions = """
internal fastcc sbyte* %RPyString_AsString(%RPyString* %structstring) {
    %source1ptr = getelementptr %RPyString* %structstring, int 0, uint 1, uint 1
    %source1 = cast [0 x sbyte]* %source1ptr to sbyte*
    ret sbyte* %source1
}

internal fastcc WORD %RPyString_Size(%RPyString* %structstring) {
    %sizeptr = getelementptr %RPyString* %structstring, int 0, uint 1, uint 0
    %size = load WORD* %sizeptr
    ret WORD %size
}

internal fastcc int %RPyExceptionOccurred() {
    %tmp.0 = load %RPYTHON_EXCEPTION_VTABLE** %last_exception_type
    %bool_res = setne %RPYTHON_EXCEPTION_VTABLE* %tmp.0, null
    %res = cast bool %bool_res to int
    ret int %res
}

internal fastcc %RPyString* %RPyString_FromString(sbyte* %s) {
    %lenu      = call ccc uint %strlen(sbyte* %s)
    %lenuword  = cast uint %lenu to UWORD
    %lenword   = cast uint %lenu to WORD
    %rpy       = call fastcc %RPyString* %pypy_RPyString_New__Signed(WORD %lenword)
    %rpystrptr = getelementptr %RPyString* %rpy, int 0, uint 1, uint 1
    %rpystr    = cast [0 x sbyte]* %rpystrptr to sbyte*

    call ccc void %llvm.memcpyPOSTFIX(sbyte* %rpystr, sbyte* %s, UWORD %lenuword, UWORD 0)

    ret %RPyString* %rpy
}

internal fastcc WORD %pypyop_int_abs(WORD %x) {
block0:
    %cond1 = setge WORD %x, 0
    br bool %cond1, label %return_block, label %block1
block1:
    %x2 = sub WORD 0, %x
    br label %return_block
return_block:
    %result = phi WORD [%x, %block0], [%x2, %block1]
    ret WORD %result
}

internal fastcc long %pypyop_llong_abs(long %x) {
block0:
    %cond1 = setge long %x, 0
    br bool %cond1, label %return_block, label %block1
block1:
    %x2 = sub long 0, %x
    br label %return_block
return_block:
    %result = phi long [%x, %block0], [%x2, %block1]
    ret long %result
}

internal fastcc double %pypyop_float_abs(double %x) {
block0:
    %cond1 = setge double %x, 0.0
    br bool %cond1, label %return_block, label %block1
block1:
    %x2 = sub double 0.0, %x
    br label %return_block
return_block:
    %result = phi double [%x, %block0], [%x2, %block1]
    ret double %result
}

"""

from sys import maxint
if maxint != 2**31-1:
    extfunctions += """
internal fastcc void %pypy_ll_raise_OSError__Signed(int %errno_0) {
    %tmp = cast int %errno_0 to long
    call fastcc void %pypy_ll_raise_OSError__Signed(long %tmp)
    ret void
}

internal fastcc void %pypy__RPyListOfString_SetItem__listPtr_Signed_rpy_stringPtr(%RPyListOfString* %l_1, int %index_0, %RPyString* %newstring_0) {
    %index_0_long = cast int %index_0 to long
    call fastcc void %pypy__RPyListOfString_SetItem__listPtr_Signed_rpy_stringPtr(%RPyListOfString* %l_1, long %index_0_long, %RPyString* %newstring_0)
    ret void
}

"""

extfunctions_standalone = """
"""
if maxint != 2**31-1:
    extfunctions_standalone += """
internal fastcc int %pypy_entry_point(%RPyListOfString* %argv) {
    %result = call fastcc long %pypy_entry_point(%RPyListOfString* %argv)
    %tmp = cast long %result to int
    ret int %tmp
}

"""

def write_raise_exc(c_name, exc_repr, codewriter):

    l = """
internal fastcc void %%raise%s(sbyte* %%msg) {
    %%exception_value = cast %s to %%RPYTHON_EXCEPTION*
    %%tmp             = getelementptr %%RPYTHON_EXCEPTION* %%exception_value, int 0, uint 0
    %%exception_type  = load %%RPYTHON_EXCEPTION_VTABLE** %%tmp
    store %%RPYTHON_EXCEPTION_VTABLE* %%exception_type, %%RPYTHON_EXCEPTION_VTABLE** %%last_exception_type
    store %%RPYTHON_EXCEPTION* %%exception_value, %%RPYTHON_EXCEPTION** %%last_exception_value
    call fastcc void %%unwind()
    ret void
}
""" % (c_name, exc_repr)
    codewriter.write_lines(l)

