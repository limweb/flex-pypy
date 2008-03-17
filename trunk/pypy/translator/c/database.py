from pypy.rpython.lltypesystem.lltype import \
     Primitive, Ptr, typeOf, RuntimeTypeInfo, \
     Struct, Array, FuncType, PyObject, Void, \
     ContainerType, OpaqueType, FixedSizeArray, _uninitialized
from pypy.rpython.lltypesystem import lltype
from pypy.rpython.lltypesystem.llmemory import Address
from pypy.tool.sourcetools import valid_identifier
from pypy.translator.c.primitive import PrimitiveName, PrimitiveType
from pypy.translator.c.primitive import PrimitiveErrorValue
from pypy.translator.c.node import StructDefNode, ArrayDefNode
from pypy.translator.c.node import FixedSizeArrayDefNode
from pypy.translator.c.node import ContainerNodeFactory, ExtTypeOpaqueDefNode
from pypy.translator.c.support import cdecl, CNameManager, ErrorValue
from pypy.translator.c.support import log
from pypy.translator.c.extfunc import do_the_getting
from pypy import conftest
from pypy.translator.c import gc


# ____________________________________________________________

class LowLevelDatabase(object):
    gctransformer = None

    def __init__(self, translator=None, standalone=False,
                 gcpolicyclass=None,
                 stacklesstransformer=None,
                 thread_enabled=False):
        self.translator = translator
        self.standalone = standalone
        self.stacklesstransformer = stacklesstransformer
        if gcpolicyclass is None:
            gcpolicyclass = gc.RefcountingGcPolicy
        self.gcpolicy = gcpolicyclass(self, thread_enabled)

        self.structdefnodes = {}
        self.pendingsetupnodes = []
        self.containernodes = {}
        self.containerlist = []
        self.delayedfunctionnames = {}
        self.delayedfunctionptrs = []
        self.completedcontainers = 0
        self.containerstats = {}
        self.externalfuncs = {}
        self.helper2ptr = {}

        # late_initializations is for when the value you want to
        # assign to a constant object is something C doesn't think is
        # constant
        self.late_initializations = []
        self.namespace = CNameManager()
        if not standalone:
            from pypy.translator.c.pyobj import PyObjMaker
            self.pyobjmaker = PyObjMaker(self.namespace, self, translator)

        if translator is None or translator.rtyper is None:
            self.exctransformer = None
        else:
            self.exctransformer = translator.getexceptiontransformer()
        if translator is not None:
            self.gctransformer = self.gcpolicy.transformerclass(translator)
        self.completed = False

        self.instrument_ncounter = 0

    def gettypedefnode(self, T, varlength=1):
        if varlength <= 1:
            varlength = 1   # it's C after all
            key = T
        else:
            key = T, varlength
        try:
            node = self.structdefnodes[key]
        except KeyError:
            if isinstance(T, Struct):
                if isinstance(T, FixedSizeArray):
                    node = FixedSizeArrayDefNode(self, T)
                else:
                    node = StructDefNode(self, T, varlength)
            elif isinstance(T, Array):
                node = ArrayDefNode(self, T, varlength)
            elif isinstance(T, OpaqueType) and hasattr(T, '_exttypeinfo'):
                node = ExtTypeOpaqueDefNode(self, T)
            else:
                raise Exception("don't know about %r" % (T,))
            self.structdefnodes[key] = node
            self.pendingsetupnodes.append(node)
        return node

    def gettype(self, T, varlength=1, who_asks=None, argnames=[]):
        if isinstance(T, Primitive):
            return PrimitiveType[T]
        elif isinstance(T, Ptr):
            if isinstance(T.TO, FixedSizeArray):
                # /me blames C
                node = self.gettypedefnode(T.TO)
                return node.getptrtype()
            else:
                typename = self.gettype(T.TO)   # who_asks not propagated
                return typename.replace('@', '*@')
        elif isinstance(T, (Struct, Array)):
            node = self.gettypedefnode(T, varlength=varlength)
            if who_asks is not None:
                who_asks.dependencies[node] = True
            return node.gettype()
        elif T == PyObject:
            return 'PyObject @'
        elif isinstance(T, FuncType):
            resulttype = self.gettype(T.RESULT)
            argtypes = []
            for i in range(len(T.ARGS)):
                if T.ARGS[i] is not Void:
                    argtype = self.gettype(T.ARGS[i])
                    try:
                        argname = argnames[i]
                    except IndexError:
                        argname = ''
                    argtypes.append(cdecl(argtype, argname))
            argtypes = ', '.join(argtypes) or 'void'
            return resulttype.replace('@', '(@)(%s)' % argtypes)
        elif isinstance(T, OpaqueType):
            if T == RuntimeTypeInfo:
                return  self.gcpolicy.rtti_type()
            elif hasattr(T, '_exttypeinfo'):
                # for external types (pypy.rpython.extfunctable.declaretype())
                node = self.gettypedefnode(T, varlength=varlength)
                if who_asks is not None:
                    who_asks.dependencies[node] = True
                return 'struct %s @' % node.name
            else:
                #raise Exception("don't know about opaque type %r" % (T,))
                return 'struct %s @' % (
                    valid_identifier('pypy_opaque_' + T.tag),)
        else:
            raise Exception("don't know about type %r" % (T,))

    def getcontainernode(self, container, **buildkwds):
        try:
            node = self.containernodes[container]
        except KeyError:
            T = typeOf(container)
            if isinstance(T, (lltype.Array, lltype.Struct)):
                if hasattr(self.gctransformer, 'consider_constant'):
                    self.gctransformer.consider_constant(T, container)
            nodefactory = ContainerNodeFactory[T.__class__]
            node = nodefactory(self, T, container, **buildkwds)
            self.containernodes[container] = node
            self.containerlist.append(node)
            kind = getattr(node, 'nodekind', '?')
            self.containerstats[kind] = self.containerstats.get(kind, 0) + 1
            if self.completed:
                assert not node.globalcontainer
                # non-global containers are found very late, e.g. _subarrays
                # via addresses introduced by the GC transformer
        return node

    def get(self, obj):
        if isinstance(obj, ErrorValue):
            T = obj.TYPE
            if isinstance(T, Primitive):
                return PrimitiveErrorValue[T]
            elif isinstance(T, Ptr):
                return 'NULL'
            else:
                raise Exception("don't know about %r" % (T,))
        else:
            T = typeOf(obj)
            if isinstance(T, Primitive):
                return PrimitiveName[T](obj, self)
            elif isinstance(T, Ptr):
                if obj:   # test if the ptr is non-NULL
                    try:
                        container = obj._obj
                    except lltype.DelayedPointer:
                        # hack hack hack
                        name = obj._obj0
                        assert name.startswith('delayed!')
                        n = len('delayed!')
                        if len(name) == n:
                            raise
                        if id(obj) in self.delayedfunctionnames:
                            return self.delayedfunctionnames[id(obj)][0]
                        funcname = name[n:]
                        funcname = self.namespace.uniquename('g_' + funcname)
                        self.delayedfunctionnames[id(obj)] = funcname, obj
                        self.delayedfunctionptrs.append(obj)
                        return funcname
                        # /hack hack hack
                    else:
                        # hack hack hack
                        if id(obj) in self.delayedfunctionnames:
                            # this used to be a delayed function,
                            # make sure we use the same name
                            forcename = self.delayedfunctionnames[id(obj)][0]
                            node = self.getcontainernode(container,
                                                         forcename=forcename)
                            assert node.ptrname == forcename
                            return forcename
                        # /hack hack hack

                    if isinstance(container, int):
                        # special case for tagged odd-valued pointers
                        return '((%s) %d)' % (cdecl(self.gettype(T), ''),
                                              obj._obj)
                    node = self.getcontainernode(container)
                    return node.ptrname
                else:
                    return '((%s) NULL)' % (cdecl(self.gettype(T), ''), )
            else:
                raise Exception("don't know about %r" % (obj,))

    def complete(self, show_progress=True):
        assert not self.completed
        if self.translator and self.translator.rtyper:
            do_the_getting(self, self.translator.rtyper)
        def dump():
            lst = ['%s: %d' % keyvalue
                   for keyvalue in self.containerstats.items()]
            lst.sort()
            log.event('%8d nodes  [ %s ]' % (i, '  '.join(lst)))
        i = self.completedcontainers
        if show_progress:
            show_i = (i//1000 + 1) * 1000
        else:
            show_i = -1

        # The order of database completion is fragile with stackless and
        # gc transformers.  Here is what occurs:
        #
        # 1. follow dependencies recursively from the entry point: data
        #    structures pointing to other structures or functions, and
        #    constants in functions pointing to other structures or functions.
        #    Because of the mixlevelannotator, this might find delayed
        #    (not-annotated-and-rtyped-yet) function pointers.  They are
        #    not followed at this point.  User finalizers (__del__) on the
        #    other hand are followed during this step too.
        #
        # 2. gctransformer.finish_helpers() - after this, all functions in
        #    the program have been rtyped.
        #
        # 3. follow new dependencies.  All previously delayed functions
        #    should have been resolved by 2 - they are gc helpers, like
        #    ll_finalize().  New FuncNodes are built for them.  No more
        #    FuncNodes can show up after this step.
        #
        # 4. stacklesstransform.finish() - freeze the stackless resume point
        #    table.
        #
        # 5. follow new dependencies (this should be only the new frozen
        #    table, which contains only numbers and already-seen function
        #    pointers).
        #
        # 6. gctransformer.finish_tables() - freeze the gc types table.
        #
        # 7. follow new dependencies (this should be only the gc type table,
        #    which contains only numbers and pointers to ll_finalizer
        #    functions seen in step 3).
        #
        # I think that there is no reason left at this point that force
        # step 4 to be done before step 6, nor to have a follow-new-
        # dependencies step inbetween.  It is important though to have step 3
        # before steps 4 and 6.
        #
        # This is implemented by interleaving the follow-new-dependencies
        # steps with calls to the next 'finish' function from the following
        # list:
        finish_callbacks = []
        if self.gctransformer:
            finish_callbacks.append(self.gctransformer.finish_helpers)
        if self.stacklesstransformer:
            finish_callbacks.append(self.stacklesstransformer.finish)
        if self.gctransformer:
            finish_callbacks.append(self.gctransformer.finish_tables)

        def add_dependencies(newdependencies):
            for value in newdependencies:
                #if isinstance(value, _uninitialized):
                #    continue
                if isinstance(typeOf(value), ContainerType):
                    self.getcontainernode(value)
                else:
                    self.get(value)
        
        while True:
            while True:
                if hasattr(self, 'pyobjmaker'):
                    self.pyobjmaker.collect_initcode()
                while self.pendingsetupnodes:
                    lst = self.pendingsetupnodes
                    self.pendingsetupnodes = []
                    for nodedef in lst:
                        nodedef.setup()
                if i == len(self.containerlist):
                    break
                node = self.containerlist[i]
                add_dependencies(node.enum_dependencies())
                i += 1
                self.completedcontainers = i
                if i == show_i:
                    dump()
                    show_i += 1000

            if self.delayedfunctionptrs:
                lst = self.delayedfunctionptrs
                self.delayedfunctionptrs = []
                progress = False
                for fnptr in lst:
                    try:
                        fnptr._obj
                    except lltype.DelayedPointer:   # still not resolved
                        self.delayedfunctionptrs.append(fnptr)
                    else:
                        self.get(fnptr)
                        progress = True
                if progress:
                    continue   # progress - follow all dependencies again

            if finish_callbacks:
                finish = finish_callbacks.pop(0)
                newdependencies = finish()
                if newdependencies:
                    add_dependencies(newdependencies)
                continue       # progress - follow all dependencies again

            break     # database is now complete

        assert not self.delayedfunctionptrs
        self.completed = True
        if show_progress:
            dump()

    def globalcontainers(self):
        for node in self.containerlist:
            if node.globalcontainer:
                yield node

    def get_lltype_of_exception_value(self):
        if self.translator is not None and self.translator.rtyper is not None:
            exceptiondata = self.translator.rtyper.getexceptiondata()
            return exceptiondata.lltype_of_exception_value
        else:
            return Ptr(PyObject)

    def getstructdeflist(self):
        # return the StructDefNodes sorted according to dependencies
        result = []
        seen = {}
        def produce(node):
            if node not in seen:
                for othernode in node.dependencies:
                    produce(othernode)
                result.append(node)
                seen[node] = True
        for node in self.structdefnodes.values():
            produce(node)
        return result
