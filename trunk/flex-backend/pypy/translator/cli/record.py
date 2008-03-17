from pypy.rpython.ootypesystem import ootype
from pypy.translator.cli.node import Node
from pypy.translator.cli.cts import CTS

class Record(Node):
    def __init__(self, db, record, name):
        self.db = db
        self.cts = CTS(db)
        self.record = record
        self.name = name

    def __hash__(self):
        return hash(self.record)

    def __eq__(self, other):
        return self.record == other.record

    def __ne__(self, other):
        return not self == other

    def get_name(self):
        return self.name

    def get_base_class(self):
        return '[mscorlib]System.Object'        

    def render(self, ilasm):
        self.ilasm = ilasm
        ilasm.begin_class(self.name, self.get_base_class())
        for f_name, (FIELD_TYPE, f_default) in self.record._fields.iteritems():
            f_name = self.cts.escape_name(f_name)
            cts_type = self.cts.lltype_to_cts(FIELD_TYPE)
            if cts_type != 'void':
                ilasm.field(f_name, cts_type)
        self._ctor()
        self._toString()
        self._equals()
        self._getHashCode()
        ilasm.end_class()

    def _ctor(self):
        self.ilasm.begin_function('.ctor', [], 'void', False, 'specialname', 'rtspecialname', 'instance')
        self.ilasm.opcode('ldarg.0')
        self.ilasm.call('instance void %s::.ctor()' % self.get_base_class())
        self.ilasm.opcode('ret')
        self.ilasm.end_function()
        
    def _toString(self):
        # only for testing purposes, and only if the Record represents a tuple
        from pypy.translator.cli.test.runtest import format_object

        for f_name in self.record._fields:
            if not f_name.startswith('item'):
                return # it's not a tuple

        self.ilasm.begin_function('ToString', [], 'string', False, 'virtual', 'instance', 'default')
        self.ilasm.opcode('ldstr', '"("')
        for i in xrange(len(self.record._fields)):
            f_name = 'item%d' % i
            FIELD_TYPE, f_default = self.record._fields[f_name]
            if FIELD_TYPE is ootype.Void:
                continue
            self.ilasm.opcode('ldarg.0')
            f_type = self.cts.lltype_to_cts(FIELD_TYPE)
            self.ilasm.get_field((f_type, self.name, f_name))
            format_object(FIELD_TYPE, self.cts, self.ilasm)
            self.ilasm.call('string string::Concat(string, string)')
            self.ilasm.opcode('ldstr ", "')
            self.ilasm.call('string string::Concat(string, string)')
        self.ilasm.opcode('ldstr ")"')
        self.ilasm.call('string string::Concat(string, string)')            
        self.ilasm.opcode('ret')
        self.ilasm.end_function()

    def _equals(self):
        # field by field comparison
        record_type = self.cts.lltype_to_cts(self.record, include_class=False)
        class_record_type = self.cts.lltype_to_cts(self.record, include_class=True)
        self.ilasm.begin_function('Equals', [('object', 'obj')], 'bool',
                                  False, 'virtual', 'instance', 'default')
        self.ilasm.locals([(class_record_type, 'self')])
        self.ilasm.opcode('ldarg.1')
        self.ilasm.opcode('castclass', record_type)
        self.ilasm.opcode('stloc.0')

        equal = 'bool [pypylib]pypy.runtime.Utils::Equal<%s>(!!0, !!0)'
        self.ilasm.opcode('ldc.i4', '1')
        for f_name, (FIELD_TYPE, default) in self.record._fields.iteritems():
            if FIELD_TYPE is ootype.Void:
                continue
            f_type = self.cts.lltype_to_cts(FIELD_TYPE)
            f_name = self.cts.escape_name(f_name)
            self.ilasm.opcode('ldarg.0')
            self.ilasm.get_field((f_type, record_type, f_name))
            self.ilasm.opcode('ldloc.0')
            self.ilasm.get_field((f_type, record_type, f_name))
            self.ilasm.call(equal % f_type)
            self.ilasm.opcode('and')

        self.ilasm.opcode('ret')
        self.ilasm.end_function()

    def _getHashCode(self):
        # return the hash of the first field. XXX: it can lead to a bad distribution
        record_type = self.cts.lltype_to_cts(self.record, include_class=False)
        self.ilasm.begin_function('GetHashCode', [], 'int32', False, 'virtual', 'instance', 'default')
        gethash = 'int32 [pypylib]pypy.runtime.Utils::GetHashCode<%s>(!!0)'
        if self.record._fields:
            f_name, (FIELD_TYPE, default) = self.record._fields.iteritems().next()
            if FIELD_TYPE is ootype.Void:
                self.ilasm.opcode('ldc.i4.0')
            else:
                f_name = self.cts.escape_name(f_name)
                f_type = self.cts.lltype_to_cts(FIELD_TYPE)
                self.ilasm.opcode('ldarg.0')
                self.ilasm.get_field((f_type, record_type, f_name))
                self.ilasm.call(gethash % f_type)
        else:
            self.ilasm.opcode('ldc.i4.0')
        self.ilasm.opcode('ret')
        self.ilasm.end_function()
