"""
The database centralizes information about the state of our translation,
and the mapping between the OOTypeSystem and the Java type system.
"""

from cStringIO import StringIO
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.ootypesystem import ootype, rclass
from pypy.translator.jvm import typesystem as jvmtype
from pypy.translator.jvm import node, methods
from pypy.translator.jvm.option import getoption
import pypy.translator.jvm.generator as jvmgen
from pypy.translator.jvm.generator import Method, Property, Field
import pypy.translator.jvm.constant as jvmconst
from pypy.translator.jvm.typesystem import \
     jStringBuilder, jInt, jVoid, jString, jChar, jPyPyConst, jObject, \
     jThrowable
from pypy.translator.jvm.builtin import JvmBuiltInType
from pypy.rpython.lltypesystem.llmemory import WeakGcAddress

from pypy.translator.oosupport.database import Database as OODatabase


# ______________________________________________________________________
# Database object

class Database(OODatabase):
    def __init__(self, genoo):
        OODatabase.__init__(self, genoo)
        
        # Private attributes:
        self._jasmin_files = [] # list of strings --- .j files we made
        self._classes = {} # Maps ootype class objects to node.Class objects,
                           # and JvmType objects as well
        self._functions = {}      # graph -> jvmgen.Method

        # (jargtypes, jrettype) -> node.StaticMethodInterface
        self._delegates = {}

        # (INSTANCE, method_name) -> node.StaticMethodImplementation
        self._bound_methods = {}

        self._function_names = {} # graph --> function_name

        self._constants = {}      # flowmodel.Variable --> jvmgen.Const

        # Special fields for the Object class, see _translate_Object
        self._object_interf = None
        self._object_impl = None
        self._object_exc_impl = None

    # _________________________________________________________________
    # Java String vs Byte Array
    #
    # We allow the user to configure whether Python strings are stored
    # as Java strings, or as byte arrays.  The latter saves space; the
    # former may be faster.  

    using_byte_array = False

    # XXX have to fill this in
    
    # _________________________________________________________________
    # Miscellaneous
    
    def _uniq(self, nm):
        return nm + "_" + str(self.unique())

    def _pkg(self, nm):
        return "%s.%s" % (getoption('package'), nm)

    def class_name(self, TYPE):
        jtype = self.lltype_to_cts(TYPE)
        assert isinstance(jtype, jvmtype.JvmClassType)
        return jtype.name

    def add_jasmin_file(self, jfile):
        """ Adds to the list of files we need to run jasmin on """
        self._jasmin_files.append(jfile)

    def jasmin_files(self):
        """ Returns list of files we need to run jasmin on """
        return self._jasmin_files

    def is_Object(self, OOTYPE):
        return isinstance(OOTYPE, ootype.Instance) and OOTYPE._name == "Object"

    # _________________________________________________________________
    # Node Creation
    #
    # Creates nodes that represents classes, functions, simple constants.

    def create_interlink_node(self, methods):
        """ This is invoked by create_interlinke_node() in
        jvm/prebuiltnodes.py.  It creates a Class node that will
        be an instance of the Interlink interface, which is used
        to allow the static java code to throw PyPy exceptions and the
        like.

        The 'methods' argument should be a dictionary whose keys are
        method names and whose entries are jvmgen.Method objects which
        the corresponding method should invoke. """

        nm = self._pkg(self._uniq('InterlinkImplementation'))
        cls = node.Class(nm, supercls=jObject)
        for method_name, helper in methods.items():
            cls.add_method(node.InterlinkFunction(cls, method_name, helper))
        cls.add_interface(jvmtype.jPyPyInterlink)
        self.interlink_class = cls
        self.pending_node(cls)

    def types_for_graph(self, graph):
        """
        Given a graph, returns a tuple like so:
          ( (java argument types...), java return type )
        For example, if the graph took two strings and returned a bool,
        then the return would be:
          ( (jString, jString), jBool )
        """
        argtypes = [arg.concretetype for arg in graph.getargs()
                    if arg.concretetype is not ootype.Void]
        jargtypes = tuple([self.lltype_to_cts(argty) for argty in argtypes])
        rettype = graph.getreturnvar().concretetype
        jrettype = self.lltype_to_cts(rettype)
        return jargtypes, jrettype        
    
    def _function_for_graph(self, classobj, funcnm, is_static, graph):
        
        """
        Creates a node.Function object for a particular graph.  Adds
        the method to 'classobj', which should be a node.Class object.
        """
        jargtypes, jrettype = self.types_for_graph(graph)
        funcobj = node.GraphFunction(
            self, classobj, funcnm, jargtypes, jrettype, graph, is_static)
        return funcobj
    
    def _translate_record(self, OOTYPE):
        assert OOTYPE is not ootype.ROOT

        # Create class object if it does not already exist:
        if OOTYPE in self._classes:
            return self._classes[OOTYPE]

        # Create the class object first
        clsnm = self._pkg(self._uniq('Record'))
        clsobj = node.Class(clsnm, jObject)
        self._classes[OOTYPE] = clsobj

        # Add fields:
        self._translate_class_fields(clsobj, OOTYPE)

        # generate toString
        dump_method = methods.RecordDumpMethod(self, OOTYPE, clsobj)
        clsobj.add_method(dump_method)

        # generate equals and hash
        equals_method = methods.DeepEqualsMethod(self, OOTYPE, clsobj)
        clsobj.add_method(equals_method)
        hash_method = methods.DeepHashMethod(self, OOTYPE, clsobj)
        clsobj.add_method(hash_method)

        self.pending_node(clsobj)
        return clsobj

    def _translate_Object(self, OBJ):
        """
        We handle the class 'Object' quite specially: we translate it
        into an interface with two implementations.  One
        implementation serves as the root of most objects, and the
        other as the root for all exceptions.
        """
        assert self.is_Object(OBJ)
        assert OBJ._superclass == ootype.ROOT

        # Have we already translated Object?
        if self._object_interf: return self._object_interf

        # Create the interface and two implementations:
        def gen_name(): return self._pkg(self._uniq(OBJ._name))
        internm, implnm, exc_implnm = gen_name(), gen_name(), gen_name()
        self._object_interf = node.Interface(internm)
        self._object_impl = node.Class(implnm, supercls=jObject)
        self._object_exc_impl = node.Class(exc_implnm, supercls=jThrowable)
        self._object_impl.add_interface(self._object_interf)
        self._object_exc_impl.add_interface(self._object_interf)

        # Translate the fields into properties on the interface,
        # and into actual fields on the implementations.
        for fieldnm, (FIELDOOTY, fielddef) in OBJ._fields.iteritems():
            if FIELDOOTY is ootype.Void: continue
            fieldty = self.lltype_to_cts(FIELDOOTY)

            # Currently use hacky convention of _jvm_FieldName for the name
            methodnm = "_jvm_"+fieldnm

            def getter_method_obj(node):
                return Method.v(node, methodnm+"_g", [], fieldty)
            def putter_method_obj(node):
                return Method.v(node, methodnm+"_p", [fieldty], jVoid)
            
            # Add get/put methods to the interface:
            prop = Property(
                fieldnm, 
                getter_method_obj(self._object_interf),
                putter_method_obj(self._object_interf),
                OOTYPE=FIELDOOTY)
            self._object_interf.add_property(prop)

            # Generate implementations:
            def generate_impl(clsobj):
                clsnm = clsobj.name
                fieldobj = Field(clsnm, fieldnm, fieldty, False, FIELDOOTY)
                clsobj.add_field(fieldobj, fielddef)
                clsobj.add_method(node.GetterFunction(
                    self, clsobj, getter_method_obj(clsobj), fieldobj))
                clsobj.add_method(node.PutterFunction(
                    self, clsobj, putter_method_obj(clsobj), fieldobj))
            generate_impl(self._object_impl)
            generate_impl(self._object_exc_impl)

        # Ensure that we generate all three classes.
        self.pending_node(self._object_interf)
        self.pending_node(self._object_impl)
        self.pending_node(self._object_exc_impl)

    def _translate_superclass_of(self, OOSUB):
        """
        Invoked to translate OOSUB's super class.  Normally just invokes
        pending_class, but we treat "Object" differently so that we can
        make all exceptions descend from Throwable.
        """
        OOSUPER = OOSUB._superclass
        if not self.is_Object(OOSUPER):
            return self.pending_class(OOSUPER)
        self._translate_Object(OOSUPER)          # ensure this has been done
        if OOSUB._name == "exceptions.Exception":
            return self._object_exc_impl
        return self._object_impl        

    def _translate_instance(self, OOTYPE):
        assert isinstance(OOTYPE, ootype.Instance)
        assert OOTYPE is not ootype.ROOT

        # Create class object if it does not already exist:
        if OOTYPE in self._classes:
            return self._classes[OOTYPE]

        # Create the class object first
        clsnm = self._pkg(self._uniq(OOTYPE._name))
        clsobj = node.Class(clsnm)
        self._classes[OOTYPE] = clsobj

        # Resolve super class 
        assert OOTYPE._superclass
        supercls = self._translate_superclass_of(OOTYPE)
        clsobj.set_super_class(supercls)

        # TODO --- mangle field and method names?  Must be
        # deterministic, or use hashtable to avoid conflicts between
        # classes?
        
        # Add fields:
        self._translate_class_fields(clsobj, OOTYPE)
            
        # Add methods:
        for mname, mimpl in OOTYPE._methods.iteritems():
            if not hasattr(mimpl, 'graph'):
                # Abstract method
                METH = mimpl._TYPE
                arglist = [self.lltype_to_cts(ARG) for ARG in METH.ARGS
                           if ARG is not ootype.Void]
                returntype = self.lltype_to_cts(METH.RESULT)
                clsobj.add_abstract_method(jvmgen.Method.v(
                    clsobj, mname, arglist, returntype))
            else:
                # if the first argument's type is not a supertype of
                # this class it means that this method this method is
                # not really used by the class: don't render it, else
                # there would be a type mismatch.
                args =  mimpl.graph.getargs()
                SELF = args[0].concretetype
                if not ootype.isSubclass(OOTYPE, SELF): continue
                mobj = self._function_for_graph(
                    clsobj, mname, False, mimpl.graph)
                clsobj.add_method(mobj)

        # currently, we always include a special "dump" method for debugging
        # purposes
        dump_method = node.InstanceDumpMethod(self, OOTYPE, clsobj)
        clsobj.add_method(dump_method)

        self.pending_node(clsobj)
        return clsobj

    def _translate_class_fields(self, clsobj, OOTYPE):
        for fieldnm, (FIELDOOTY, fielddef) in OOTYPE._fields.iteritems():
            if FIELDOOTY is ootype.Void: continue
            fieldty = self.lltype_to_cts(FIELDOOTY)
            clsobj.add_field(
                jvmgen.Field(clsobj.name, fieldnm, fieldty, False, FIELDOOTY),
                fielddef)

    def pending_class(self, OOTYPE):
        return self.lltype_to_cts(OOTYPE)

    def pending_function(self, graph):
        """
        This is invoked when a standalone function is to be compiled.
        It creates a class named after the function with a single
        method, invoke().  This class is added to the worklist.
        Returns a jvmgen.Method object that allows this function to be
        invoked.
        """
        if graph in self._functions:
            return self._functions[graph]
        classnm = self._pkg(self._uniq(graph.name))
        classobj = node.Class(classnm, self.pending_class(ootype.ROOT))
        funcobj = self._function_for_graph(classobj, "invoke", True, graph)
        classobj.add_method(funcobj)
        self.pending_node(classobj)
        res = self._functions[graph] = funcobj.method()
        return res

    def record_delegate(self, TYPE):
        """
        Creates and returns a StaticMethodInterface type; this type
        represents an abstract base class for functions with a given
        signature, represented by TYPE, a ootype.StaticMethod
        instance.
        """

        # Translate argument/return types into java types, check if
        # we already have such a delegate:
        jargs = tuple([self.lltype_to_cts(ARG) for ARG in TYPE.ARGS
                       if ARG is not ootype.Void])
        jret = self.lltype_to_cts(TYPE.RESULT)
        return self.record_delegate_sig(jargs, jret)

    def record_delegate_sig(self, jargs, jret):
        """
        Like record_delegate, but the signature is in terms of java
        types.  jargs is a list of JvmTypes, one for each argument,
        and jret is a JvmType.  Note that jargs does NOT include an
        entry for the this pointer of the resulting object.  
        """
        key = (jargs, jret)
        if key in self._delegates:
            return self._delegates[key]

        # TODO: Make an intelligent name for this interface by
        # mangling the list of parameters
        name = self._pkg(self._uniq('Delegate'))

        # Create a new one if we do not:
        interface = node.StaticMethodInterface(name, jargs, jret)
        self._delegates[key] = interface
        self.pending_node(interface)
        return interface
    
    def record_delegate_standalone_func_impl(self, graph):
        """
        Creates a class with an invoke() method that invokes the given
        graph.  This object can be used as a function pointer.  It
        will extend the appropriate delegate for the graph's
        signature.
        """
        jargtypes, jrettype = self.types_for_graph(graph)
        super_class = self.record_delegate_sig(jargtypes, jrettype)
        pfunc = self.pending_function(graph)
        implnm = self._pkg(self._uniq(graph.name+'_delegate'))
        n = node.StaticMethodImplementation(implnm, super_class, None, pfunc)
        self.pending_node(n)
        return n

    def record_delegate_bound_method_impl(self, INSTANCE, method_name):
        """
        Creates an object with an invoke() method which invokes
        a method named method_name on an instance of INSTANCE.
        """
        key = (INSTANCE, method_name)
        if key in self._bound_methods:
            return self._bound_methods[key]
        METH_TYPE = INSTANCE._lookup(method_name)[1]._TYPE
        super_class = self.record_delegate(METH_TYPE)
        self_class = self.lltype_to_cts(INSTANCE)
        mthd_obj = self_class.lookup_method(method_name)
        implnm = self._pkg(self._uniq(
            self_class.simple_name()+"_"+method_name+"_delegate"))
        n = self._bound_methods[key] = node.StaticMethodImplementation(
            implnm, super_class, self_class, mthd_obj)
        self.pending_node(n)
        return n

    # _________________________________________________________________
    # toString functions
    #
    # Obtains an appropriate method for serializing an object of
    # any type.
    
    _toString_methods = {
        ootype.Signed:jvmgen.INTTOSTRINGI,
        ootype.Unsigned:jvmgen.PYPYSERIALIZEUINT,
        ootype.SignedLongLong:jvmgen.LONGTOSTRINGL,
        ootype.Float:jvmgen.DOUBLETOSTRINGD,
        ootype.Bool:jvmgen.PYPYSERIALIZEBOOLEAN,
        ootype.Void:jvmgen.PYPYSERIALIZEVOID,
        ootype.Char:jvmgen.PYPYESCAPEDCHAR,
        ootype.String:jvmgen.PYPYESCAPEDSTRING,
        }

    def toString_method_for_ootype(self, OOTYPE):
        """
        Assuming than an instance of type OOTYPE is pushed on the
        stack, returns a Method object that you can invoke.  This method
        will return a string representing the contents of that type.

        Do something like:
        
        > gen.load(var)
        > mthd = db.toString_method_for_ootype(var.concretetype)
        > mthd.invoke(gen)

        to print the value of 'var'.
        """
        return self._toString_methods.get(OOTYPE, jvmgen.PYPYSERIALIZEOBJECT)

    # _________________________________________________________________
    # Type translation functions
    #
    # Functions which translate from OOTypes to JvmType instances.
    # FIX --- JvmType and their Class nodes should not be different.

    def escape_name(self, nm):
        # invoked by oosupport/function.py; our names don't need escaping?
        return nm

    def llvar_to_cts(self, llv):
        """ Returns a tuple (JvmType, str) with the translated type
        and name of the given variable"""
        return self.lltype_to_cts(llv.concretetype), llv.name

    # Dictionary for scalar types; in this case, if we see the key, we
    # will return the value
    ootype_to_scalar = {
        ootype.Void:             jvmtype.jVoid,
        ootype.Signed:           jvmtype.jInt,
        ootype.Unsigned:         jvmtype.jInt,
        ootype.SignedLongLong:   jvmtype.jLong,
        ootype.UnsignedLongLong: jvmtype.jLong,
        ootype.Bool:             jvmtype.jBool,
        ootype.Float:            jvmtype.jDouble,
        ootype.Char:             jvmtype.jChar,    # byte would be sufficient, but harder
        ootype.UniChar:          jvmtype.jChar,
        ootype.Class:            jvmtype.jClass,
        ootype.ROOT:             jvmtype.jObject,  # treat like a scalar
        WeakGcAddress:           jvmtype.jWeakRef
        }

    # Dictionary for non-scalar types; in this case, if we see the key, we
    # will return a JvmBuiltInType based on the value
    ootype_to_builtin = {
        ootype.String:           jvmtype.jString,
        ootype.StringBuilder:    jvmtype.jStringBuilder,
        ootype.List:             jvmtype.jArrayList,
        ootype.Dict:             jvmtype.jHashMap,
        ootype.DictItemsIterator:jvmtype.jPyPyDictItemsIterator,
        ootype.CustomDict:       jvmtype.jPyPyCustomDict,
        }

    def lltype_to_cts(self, OOT):
        """ Returns an instance of JvmType corresponding to
        the given OOType """

        # Handle built-in types:
        if OOT in self.ootype_to_scalar:
            return self.ootype_to_scalar[OOT]
        if isinstance(OOT, lltype.Ptr) and isinstance(t.TO, lltype.OpaqueType):
            return jObject
        if OOT in self.ootype_to_builtin:
            return JvmBuiltInType(self, self.ootype_to_builtin[OOT], OOT)
        if OOT.__class__ in self.ootype_to_builtin:
            return JvmBuiltInType(
                self, self.ootype_to_builtin[OOT.__class__], OOT)

        # Handle non-built-in-types:
        if isinstance(OOT, ootype.Instance):
            if self.is_Object(OOT):
                return self._translate_Object(OOT)
            return self._translate_instance(OOT)
        if isinstance(OOT, ootype.Record):
            return self._translate_record(OOT)
        if isinstance(OOT, ootype.StaticMethod):
            return self.record_delegate(OOT)
        
        assert False, "Untranslatable type %s!" % OOT

    def exception_root_object(self):
        """
        Returns a JvmType representing the version of Object that
        serves as the root of all exceptions.
        """
        self.lltype_to_cts(rclass.OBJECT)
        assert self._object_interf
        return self._object_exc_impl

    # _________________________________________________________________
    # Uh....
    #
    # These functions are invoked by the code in oosupport, but I
    # don't think we need them or use them otherwise.

    def record_function(self, graph, name):
        self._function_names[graph] = name

    def graph_name(self, graph):
        # XXX: graph name are not guaranteed to be unique
        return self._function_names.get(graph, None)
