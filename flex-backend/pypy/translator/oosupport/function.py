import py
from pypy.tool.ansi_print import ansi_log
log = py.log.Producer("oosupport") 
py.log.setconsumer("oosupport", ansi_log) 

from pypy.objspace.flow import model as flowmodel
from pypy.rpython.ootypesystem import ootype
from pypy.translator.oosupport.treebuilder import SubOperation
from pypy.translator.oosupport.metavm import InstructionList, StoreResult



class Function(object):

    def __init__(self, db, graph, name = None, is_method = False, is_entrypoint = False):
        self.db = db
        self.cts = db.genoo.TypeSystem(db)
        self.graph = graph
        self.name = self.cts.escape_name(name or graph.name)
        self.is_method = is_method
        self.is_entrypoint = is_entrypoint
        self.generator = None # set in render()
        self.label_counters = {}
        
        # If you want to enumerate args/locals before processing, then
        # add these functions into your __init__() [they are defined below]
        #   self._set_args()
        #   self._set_locals()

    def current_label(self, prefix='label'):
        current = self.label_counters.get(prefix, 0)
        return '__%s_%d' % (prefix, current)

    def next_label(self, prefix='label'):
        current = self.label_counters.get(prefix, 0)
        self.label_counters[prefix] = current+1
        return self.current_label(prefix)

    def get_name(self):
        return self.name

    def __repr__(self):
        return '<Function %s>' % self.name

    def __hash__(self):
        return hash(self.graph)

    def __eq__(self, other):
        return self.graph == other.graph

    def __ne__(self, other):
        return not self == other

    def _is_return_block(self, block):
        return (not block.exits) and len(block.inputargs) == 1

    def _is_raise_block(self, block):
        return (not block.exits) and len(block.inputargs) == 2        

    def _is_exc_handling_block(self, block):
        return block.exitswitch == flowmodel.c_last_exception
        
    def begin_render(self):
        raise NotImplementedError

    def render_return_block(self, block):
        raise NotImplementedError

    def render_raise_block(self, block):
        raise NotImplementedError

    def begin_try(self):
        """ Begins a try block; end_try will be called exactly once, then
        some number of begin_ and end_catch pairs """
        raise NotImplementedError

    def end_try(self, target_label):
        """ Ends the try block, and branchs to the given target_label if
        no exception occurred """
        raise NotImplementedError

    def begin_catch(self, llexitcase):
        """ Begins a catch block for the exception type specified in
        llexitcase"""
        raise NotImplementedError
    
    def end_catch(self, target_label):
        """ Ends the catch block, and branchs to the given target_label as the
        last item in the catch block """
        raise NotImplementedError

    def render(self, ilasm):
        if self.db.graph_name(self.graph) is not None and not self.is_method:
            return # already rendered

        if getattr(self.graph.func, 'suggested_primitive', False):
            assert False, 'Cannot render a suggested_primitive'

        self.ilasm = ilasm
        self.generator = self._create_generator(self.ilasm)
        graph = self.graph
        self.begin_render()

        self.return_block = None
        self.raise_block = None
        for block in graph.iterblocks():
            if self._is_return_block(block):
                self.return_block = block
            elif self._is_raise_block(block):
                self.raise_block = block
            else:
                self.set_label(self._get_block_name(block))
                if self._is_exc_handling_block(block):
                    self.render_exc_handling_block(block)
                else:
                    self.render_normal_block(block)

        # render return blocks at the end just to please the .NET
        # runtime that seems to need a return statement at the end of
        # the function

        self.before_last_blocks()

        if self.raise_block:
            self.set_label(self._get_block_name(self.raise_block))
            self.render_raise_block(self.raise_block)
        if self.return_block:
            self.set_label(self._get_block_name(self.return_block))
            self.render_return_block(self.return_block)

        self.end_render()
        if not self.is_method:
            self.db.record_function(self.graph, self.name)

    def before_last_blocks(self):
        pass

    def render_exc_handling_block(self, block):
        # renders all ops but the last one
        for op in block.operations[:-1]:
            self._render_op(op)

        # render the last one (if any!) and prepend a .try
        if block.operations:
            self.begin_try()
            self._render_op(block.operations[-1])

        # search for the "default" block to be executed when no
        # exception is raised
        for link in block.exits:
            if link.exitcase is None:
                self._setup_link(link)
                self.end_try(self._get_block_name(link.target))
                break
        else:
            assert False, "No non-exceptional case from exc_handling block"

        # catch the exception and dispatch to the appropriate block
        for link in block.exits:
            if link.exitcase is None:
                continue # see above
            assert issubclass(link.exitcase, py.builtin.BaseException)
            ll_meta_exc = link.llexitcase
            self.record_ll_meta_exc(ll_meta_exc)
            self.begin_catch(link.llexitcase)
            self.store_exception_and_link(link)
            target_label = self._get_block_name(link.target)
            self.end_catch(target_label)

        self.after_except_block()

    def after_except_block(self):
        pass

    def record_ll_meta_exc(self, ll_meta_exc):
        self.db.constant_generator.record_const(ll_meta_exc)

    def store_exception_and_link(self, link):
        raise NotImplementedError
            
    def render_normal_block(self, block):
        for op in block.operations:
            self._render_op(op)

        if block.exitswitch is None:
            assert len(block.exits) == 1
            link = block.exits[0]
            target_label = self._get_block_name(link.target)
            self._setup_link(link)
            self.generator.branch_unconditionally(target_label)
        elif block.exitswitch.concretetype is ootype.Bool:
            self.render_bool_switch(block)
        elif block.exitswitch.concretetype in (ootype.Signed, ootype.SignedLongLong,
                                               ootype.Unsigned, ootype.UnsignedLongLong,
                                               ootype.Char, ootype.UniChar):
            self.render_numeric_switch(block)
        else:
            assert False, 'Unknonw exitswitch type: %s' % block.exitswitch.concretetype

    # XXX: soon or later we should use the implementation in
    # cli/function.py, but at the moment jvm and js fail with it.
    def render_bool_switch(self, block):
        for link in block.exits:
            self._setup_link(link)
            target_label = self._get_block_name(link.target)
            if link is block.exits[-1]:
                self.generator.branch_unconditionally(target_label)
            else:
                assert type(link.exitcase) is bool
                assert block.exitswitch is not None
                self.generator.load(block.exitswitch)
                self.generator.branch_conditionally(link.exitcase, target_label)

    def render_numeric_switch(self, block):
        log.WARNING("The default version of render_numeric_switch is *slow*: please override it in the backend")
        self.render_numeric_switch_naive(block)

    def render_numeric_switch_naive(self, block):
        for link in block.exits:
            target_label = self._get_block_name(link.target)
            self._setup_link(link)
            if link.exitcase == 'default':
                self.generator.branch_unconditionally(target_label)
            else:
                self.generator.push_primitive_constant(block.exitswitch.concretetype, link.exitcase)
                self.generator.load(block.exitswitch)
                self.generator.branch_if_equal(target_label)

    def _follow_link(self, link):
        target_label = self._get_block_name(link.target)
        self._setup_link(link)
        self.generator.branch_unconditionally(target_label)

    def _setup_link(self, link):
        target = link.target
        for to_load, to_store in zip(link.args, target.inputargs):
            if isinstance(to_load, flowmodel.Variable) and to_load.name == to_store.name:
                continue
            if to_load.concretetype is ootype.Void:
                continue
            self.generator.add_comment("%r --> %r" % (to_load, to_store))
            self.generator.load(to_load)
            self.generator.store(to_store)

    def _render_op(self, op):
        instr_list = self.db.genoo.opcodes.get(op.opname, None)
        assert instr_list is not None, 'Unknown opcode: %s ' % op
        assert isinstance(instr_list, InstructionList)
        instr_list.render(self.generator, op)

    def _render_sub_op(self, sub_op):
        op = sub_op.op
        instr_list = self.db.genoo.opcodes.get(op.opname, None)
        assert instr_list is not None, 'Unknown opcode: %s ' % op
        assert isinstance(instr_list, InstructionList)
        assert instr_list[-1] is StoreResult, "Cannot inline an operation that doesn't store the result"

        # record that we know about the type of result and args
        self.cts.lltype_to_cts(op.result.concretetype)
        for v in op.args:
            self.cts.lltype_to_cts(v.concretetype)

        instr_list = InstructionList(instr_list[:-1]) # leave the value on the stack if this is a sub-op
        instr_list.render(self.generator, op)
        # now the value is on the stack

    # ---------------------------------------------------------#
    # These methods are quite backend independent, but not     #
    # used in all backends. Invoke them from your __init__ if  #
    # desired.                                                 #
    # ---------------------------------------------------------#

    def _get_block_name(self, block):
        # Note: this implementation requires that self._set_locals() be
        # called to gather the blocknum's
        return 'block%s' % self.blocknum[block]
    
    def _set_locals(self):
        # this code is partly borrowed from
        # pypy.translator.c.funcgen.FunctionCodeGenerator
        # TODO: refactoring to avoid code duplication

        self.blocknum = {}

        graph = self.graph
        mix = [graph.getreturnvar()]
        for block in graph.iterblocks():
            self.blocknum[block] = len(self.blocknum)
            mix.extend(block.inputargs)

            for op in block.operations:
                mix.extend(op.args)
                mix.append(op.result)
                if getattr(op, "cleanup", None) is not None:
                    cleanup_finally, cleanup_except = op.cleanup
                    for cleanupop in cleanup_finally + cleanup_except:
                        mix.extend(cleanupop.args)
                        mix.append(cleanupop.result)
            for link in block.exits:
                mix.extend(link.getextravars())
                mix.extend(link.args)

        # filter only locals variables, i.e.:
        #  - must be variables
        #  - must appear only once
        #  - must not be function parameters
        #  - must not have 'void' type

        args = {}
        for ctstype, name in self.args:
            args[name] = True
        
        locals = []
        seen = {}
        for v in mix:
            is_var = isinstance(v, flowmodel.Variable)
            if id(v) not in seen and is_var and v.name not in args and v.concretetype is not ootype.Void:
                locals.append(self.cts.llvar_to_cts(v))
                seen[id(v)] = True

        self.locals = locals

    def _set_args(self):
        args = [arg for arg in self.graph.getargs() if arg.concretetype is not ootype.Void]
        self.args = map(self.cts.llvar_to_cts, args)
        self.argset = set([argname for argtype, argname in self.args])
