from pypy.rpython.lltypesystem.lltype import Signed, Unsigned, Void, Bool, Float
from pypy.rpython.lltypesystem.lltype import SignedLongLong, UnsignedLongLong
from pypy.rlib.objectmodel import CDefinedIntSymbolic
from pypy.rpython.ootypesystem import ootype
from pypy.translator.oosupport.metavm import Generator
from pypy.translator.oosupport.constant import push_constant
from pypy.objspace.flow import model as flowmodel
from pypy.translator.cli.support import string_literal

def isnan(v):
    return v != v*1.0 or (v == 1.0 and v == 2.0)

def isinf(v):
    return v!=0 and (v == v*2)

class CodeGenerator(object):
    def __init__(self, out, indentstep = 4, startblock = '{', endblock = '}'):
        self._out = out
        self._indent = 0
        self._bol = True # begin of line
        self._indentstep = indentstep
        self._startblock = startblock
        self._endblock = endblock

    def write(self, s, indent = 0):
        indent = self._indent + (indent * self._indentstep)
        
        if self._bol:
            self._out.write(' ' * indent)

        self._out.write(s)
        self._bol = (s and s[-1] == '\n')

    def writeline(self, s=''):
        self.write(s)
        self.write('\n')

    def openblock(self):
        self.writeline(self._startblock)
        self._indent += self._indentstep

    def closeblock(self):
        self._indent -= self._indentstep
        self.writeline(self._endblock)


class IlasmGenerator(object):
    """
    Generate IL code by writing to a file and compiling it with ilasm
    """
    def __init__(self, outfile, name, config):
        self.out = outfile
        self.config = config
        self.code = CodeGenerator(self.out)
        self.code.writeline('.assembly extern mscorlib {}')
        self.code.writeline('.assembly extern pypylib {}')
        self.code.writeline('.assembly %s {}' % name)
        self.code.writeline('.field static object last_exception') # XXX

    def close(self):
        self.out.close()

    def begin_namespace(self, name):
        self.code.writeline('.namespace ' + name)
        self.code.openblock()

    def end_namespace(self):
        self.code.closeblock()

    def write(self, s, indent=0):
        self.code.write(s, indent)

    def writeline(self, s=''):
        self.code.writeline(s)

    def openblock(self):
        self.code.openblock()

    def closeblock(self):
        self.code.closeblock()

    def begin_class(self, name, base=None, sealed=False, interfaces=(), abstract=False,
                    beforefieldinit=False, serializable=False):
        if base is None:
            base = '[mscorlib]System.Object'
        s = ''
        if abstract:
            s += 'abstract '
        if sealed:
            s += 'sealed '
        if beforefieldinit:
            s += 'beforefieldinit '
        if serializable:
            s += 'serializable '

        self.code.writeline('.class public %s %s extends %s' % (s, name, base))
        if interfaces:
            self.code.writeline('  implements %s' % ', '.join(interfaces))
        self.code.openblock()

    def end_class(self):
        self.code.closeblock()

    def field(self, name, type_, static = False):
        if static:
            s = 'static'
        else:
            s = ''

        self.code.writeline('.field public %s %s %s' % (s, type_, name))

    def begin_function(self, name, arglist, returntype, is_entrypoint = False, *args, **kwds):
        # TODO: .maxstack
        self.func_name = name
        runtime = kwds.get('runtime', False)
        if runtime:
            method_type = 'runtime'
        else:
            method_type = 'il'
        attributes = ' '.join(args)
        arglist = ', '.join(['%s %s' % arg for arg in arglist])
        self.code.writeline('.method public %s %s %s(%s) %s managed' %\
                            (attributes, returntype, name, arglist, method_type))
        
        self.code.openblock()
        if is_entrypoint:
            self.code.writeline('.entrypoint')
        self.code.writeline('.maxstack 32')
        self.stderr('start %s' % name, self.config.translation.cli.trace_calls
                    and name!='.ctor' and method_type!='runtime')

    def end_function(self):
        self.flush()
        self.code.closeblock()

    def begin_try(self):
        self.writeline('.try')
        self.openblock()

    def end_try(self):
        self.closeblock()

    def begin_catch(self, type_):
        self.writeline('catch ' + type_)
        self.openblock()

    def end_catch(self):
        self.closeblock()

    def locals(self, vars):
        varlist = ', '.join(['%s %s' % var for var in vars])        
        self.code.write('.locals init (')
        self.code.write(varlist)
        self.code.writeline(')')

    def label(self, lbl):
        self.code.writeline()
        self.code.write(lbl + ':', indent=-1)
        self.code.writeline()

    def leave(self, lbl):
        self.opcode('leave', lbl)

    def branch(self, lbl):
        self.opcode('br', lbl)

    def branch_if(self, cond, lbl):
        if cond:
            opcode = 'brtrue'
        else:
            opcode = 'brfalse'

        self.opcode(opcode, lbl)

    def call(self, func):
        self.opcode('call', func)

    def call_method(self, meth, virtual):
        if virtual:
            self.opcode('callvirt instance', meth)
        else:
            self.opcode('call instance', meth)

    def new(self, class_):
        self.opcode('newobj', class_)

    def set_field(self, field_data ):
        self.opcode('stfld', '%s %s::%s' % field_data )

    def get_field(self, field_data):
        self.opcode('ldfld', '%s %s::%s' % field_data )
    
    def throw(self):
        self.opcode('throw')
    
    def pop(self):
        self.opcode('pop')
    
    def ret(self):
        self.opcode('ret')

    def castclass(self, cts_type):
        self.opcode('castclass', cts_type)
    
    def load_self(self):
        self.opcode('ldarg.0')
    
    def load_arg(self,v):
        self.opcode('ldarg', repr(v.name))
    
    def load_local(self,v):
        self.opcode('ldloc', repr(v.name))

    def switch(self, targets):
        cmd = 'switch(%s)' % ', '.join(targets)
        self.opcode(cmd)

    def load_const(self,type_,v):
        if type_ is Void:
            pass
        elif type_ is Bool:
            self.opcode('ldc.i4', str(int(v)))
        elif type_ is Float:
            self.opcode('ldc.r8', repr(v))
        elif type_ in (Signed, Unsigned):
            self.opcode('ldc.i4', str(v))
        elif type_ in (SignedLongLong, UnsignedLongLong):
            self.opcode('ldc.i8', str(v))

    def store_local (self, v):
        self.opcode('stloc', repr(v.name))

    def store_static_constant(self, cts_type, CONST_NAMESPACE, CONST_CLASS, name):
        self.opcode('stsfld', '%s %s.%s::%s' % (cts_type, CONST_NAMESPACE, CONST_CLASS, name))

    def load_static_constant(self, cts_type, CONST_NAMESPACE, CONST_CLASS, name):
        self.opcode('ldsfld', '%s %s.%s::%s' % (cts_type, CONST_NAMESPACE, CONST_CLASS, name))

    def load_static_field(self, cts_type, name):
        self.opcode('ldsfld', '%s %s' % (cts_type, name))

    def emit(self, opcode, *args):
        self.opcode(opcode,*args)

    def begin_link(self):
        pass

    def opcode(self, opcode, *args):
        self.code.write(opcode + ' ')
        self.code.writeline(' '.join(map(str, args)))

    def stderr(self, msg, cond=True):
        from pypy.translator.cli.support import string_literal
        if cond:
            self.call('class [mscorlib]System.IO.TextWriter class [mscorlib]System.Console::get_Error()')
            self.opcode('ldstr', string_literal(msg))
            self.call_method('void class [mscorlib]System.IO.TextWriter::WriteLine(string)', virtual=True)

    def add_comment(self, text):
        self.code.writeline('// %s' % text)

    def flush(self):
        pass

DEFINED_INT_SYMBOLICS = {'MALLOC_ZERO_FILLED': 1,
                         '0 /* we are not jitted here */': 0}

class CLIBaseGenerator(Generator):
    
    """ Implements those parts of the metavm generator that are not
    tied to any particular function."""

    def __init__(self, db, ilasm):
        self.ilasm = ilasm
        self.db = db
        self.cts = db.genoo.TypeSystem(db)

    def pop(self, TYPE):
        self.ilasm.opcode('pop')
    
    def add_comment(self, text):
        self.ilasm.add_comment(text)
    
    def function_signature(self, graph, func_name=None):
        return self.cts.graph_to_signature(graph, False, func_name)

    def op_signature(self, op, func_name):
        return self.cts.op_to_signature(op, func_name)

    def class_name(self, TYPE):
        if isinstance(TYPE, ootype.Instance):
            return self.db.class_name(TYPE)
        elif isinstance(TYPE, ootype.Record):
            return self.db.get_record_name(TYPE)

    def emit(self, instr, *args):
        self.ilasm.opcode(instr, *args)

    def call_graph(self, graph, func_name=None):
        if func_name is None: # else it is a suggested primitive
            self.db.pending_function(graph)
        func_sig = self.function_signature(graph, func_name)
        self.ilasm.call(func_sig)

    def call_op(self, op, func_name):
        func_sig = self.op_signature(op, func_name)
        self.ilasm.call(func_sig)

    def call_signature(self, signature):
        self.ilasm.call(signature)

    def cast_to(self, lltype):
        cts_type = self.cts.lltype_to_cts(lltype, False)
        self.ilasm.opcode('castclass', cts_type)

    def new(self, obj):
        self.ilasm.new(self.cts.ctor_name(obj))

    def field_name(self, obj, field):
        INSTANCE, type_ = obj._lookup_field(field)
        assert type_ is not None, 'Cannot find the field %s in the object %s' % (field, obj)
        
        class_name = self.class_name(INSTANCE)
        field_type = self.cts.lltype_to_cts(type_)
        field = self.cts.escape_name(field)
        return '%s %s::%s' % (field_type, class_name, field)

    def set_field(self, obj, name):
        self.ilasm.opcode('stfld ' + self.field_name(obj, name))

    def get_field(self, obj, name):
        self.ilasm.opcode('ldfld ' + self.field_name(obj, name))

    def call_method(self, obj, name):
        # TODO: use callvirt only when strictly necessary
        signature, virtual = self.cts.method_signature(obj, name)
        self.ilasm.call_method(signature, virtual)

    def downcast(self, TYPE):
        type = self.cts.lltype_to_cts(TYPE)
        return self.ilasm.opcode('isinst', type)

    def instantiate(self):
        self.call_signature('object [pypylib]pypy.runtime.Utils::RuntimeNew(class [mscorlib]System.Type)')

    def load(self, v):
        if isinstance(v, flowmodel.Constant):
            push_constant(self.db, v.concretetype, v.value, self)
        else:
            assert False

    def isinstance(self, class_name):
        self.ilasm.opcode('isinst', class_name)

    def branch_unconditionally(self, target_label):
        self.ilasm.branch(target_label)

    def branch_conditionally(self, cond, target_label):
        self.ilasm.branch_if(cond, target_label)

    def branch_if_equal(self, target_label):
        self.ilasm.opcode('beq', target_label)

    def push_primitive_constant(self, TYPE, value):
        ilasm = self.ilasm
        if TYPE is ootype.Void:
            pass
        elif TYPE is ootype.Bool:
            ilasm.opcode('ldc.i4', str(int(value)))
        elif TYPE is ootype.Char or TYPE is ootype.UniChar:
            ilasm.opcode('ldc.i4', ord(value))
        elif TYPE is ootype.Float:
            if isinf(value):
                ilasm.opcode('ldc.r8', '(00 00 00 00 00 00 f0 7f)')
            elif isnan(value):
                ilasm.opcode('ldc.r8', '(00 00 00 00 00 00 f8 ff)')
            else:
                ilasm.opcode('ldc.r8', repr(value))
        elif isinstance(value, CDefinedIntSymbolic):
            ilasm.opcode('ldc.i4', DEFINED_INT_SYMBOLICS[value.expr])
        elif TYPE in (ootype.Signed, ootype.Unsigned):
            ilasm.opcode('ldc.i4', str(value))
        elif TYPE in (ootype.SignedLongLong, ootype.UnsignedLongLong):
            ilasm.opcode('ldc.i8', str(value))
        elif TYPE is ootype.String:
            if value._str is None:
                ilasm.opcode('ldnull')
            else:
                ilasm.opcode("ldstr", string_literal(value._str))
        else:
            assert False, "Unexpected constant type"

    def dup(self, TYPE):
        self.ilasm.opcode('dup')
