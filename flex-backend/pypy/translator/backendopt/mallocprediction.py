from pypy.translator.backendopt.escape import AbstractDataFlowInterpreter
from pypy.translator.backendopt.all import remove_mallocs
from pypy.translator.backendopt import inline
from pypy.rpython.lltypesystem import lltype
from pypy.translator import simplify
from pypy.translator.backendopt import removenoops
from pypy.translator.backendopt.support import log

SMALL_THRESHOLD = 15
BIG_THRESHOLD = 50

def find_malloc_creps(graph, adi, translator):
    # mapping from malloc creation point to graphs that it flows into
    malloc_creps = {}
    # find all mallocs that don't escape
    for block, op in graph.iterblockops():
        if op.opname == 'malloc':
            STRUCT = op.args[0].value
            # must not remove mallocs of structures that have a RTTI with a destructor
            try:
                destr_ptr = lltype.getRuntimeTypeInfo(
                    STRUCT)._obj.destructor_funcptr
                if destr_ptr:
                    continue
            except (ValueError, AttributeError), e:
                pass
            varstate = adi.getstate(op.result)
            assert len(varstate.creation_points) == 1
            crep = varstate.creation_points.keys()[0]
            if not crep.escapes:
                malloc_creps[crep] = {}
    return malloc_creps

def find_calls_where_creps_go(interesting_creps, graph, adi,
                              translator, seen):
    #print "find_calls_where_creps_go", interesting_creps, graph.name
    #print seen
    # drop creps that are merged with another creation point
    for block in graph.iterblocks():
        for var in block.getvariables():
            varstate = adi.getstate(var)
            if varstate is None:
                continue
            for crep in varstate.creation_points:
                if crep in interesting_creps:
                    if len(varstate.creation_points) != 1:
                        del interesting_creps[crep]
                        break

    # drop creps that are passed into an indirect_call
    for block, op in graph.iterblockops():
        if not interesting_creps:
            return
        if op.opname == "indirect_call":
            for var in op.args[:-1]:
                varstate = adi.getstate(var)
                if varstate is None:
                    continue
                for crep in varstate.creation_points:
                    if crep in interesting_creps:
                        del interesting_creps[crep]
        elif op.opname == "direct_call":
            #print op, interesting_creps
            called_graph = simplify.get_graph(op.args[0], translator)
            interesting = {}
            for i, var in enumerate(op.args[1:]):
                #print i, var,
                varstate = adi.getstate(var)
                if varstate is None:
                    #print "no varstate"
                    continue
                if len(varstate.creation_points) == 1:
                    crep = varstate.creation_points.keys()[0]
                    if crep not in interesting_creps:
                        #print "not interesting"
                        continue
                    if called_graph is None:
                        del interesting_creps[crep]
                        #print "graph not found"
                        continue
                    if (called_graph, i) in seen:
                        seen[(called_graph, i)][graph] = True
                        #print "seen already"
                    else:
                        #print "taking", crep
                        seen[(called_graph, i)] = {graph: True}
                        arg = called_graph.startblock.inputargs[i]
                        argstate = adi.getstate(arg)
                        argcrep = [c for c in argstate.creation_points
                                    if c.creation_method == "arg"][0]
                        interesting[argcrep] = True
            #print interesting
            if interesting:
                find_calls_where_creps_go(interesting, called_graph,
                                          adi, translator, seen)
    return interesting_creps

def find_malloc_removal_candidates(t, graphs):
    adi = AbstractDataFlowInterpreter(t)
    for graph in graphs:
        if graph.startblock not in adi.flown_blocks:
            adi.schedule_function(graph)
            adi.complete()
    targetset = dict.fromkeys(graphs)
    caller_candidates = {}
    seen = {}
    for graph in adi.seen_graphs():
        creps = find_malloc_creps(graph, adi, t)
        #print "malloc creps", creps
        if creps:
            find_calls_where_creps_go(creps, graph, adi, t, seen)
            if creps:
                if graph in targetset:
                    caller_candidates[graph] = True
    callgraph = []
    for (called_graph, i), callers in seen.iteritems():
        for caller in callers:
            if caller in targetset:
                callgraph.append((caller, called_graph))
            else:
                log.inlineandremove.WARNING("would like to inline into"
                                            " out of target set: %r"
                                            % caller)
    return callgraph, caller_candidates

def inline_and_remove(t, graphs, threshold=BIG_THRESHOLD,
                      heuristic=inline.inlining_heuristic):
    callgraph, caller_candidates = find_malloc_removal_candidates(t, graphs)
    log.inlineandremove("found %s malloc removal candidates" %
                        len(caller_candidates))
    if callgraph:
        count = inline.auto_inlining(t, callgraph=callgraph,
                                     threshold=threshold,
                                     heuristic=heuristic)
        if not count:
            return False
        log.inlineandremove('inlined %d callsites.'% (count,))
        count = remove_mallocs(t, caller_candidates.keys())
        return count
    else:
        return False

def preparation(translator, graphs, threshold=SMALL_THRESHOLD,
                heuristic=inline.inlining_heuristic):
    count = 0
    inline.auto_inline_graphs(translator, graphs, threshold,
                              heuristic=heuristic)
    count += remove_mallocs(translator, graphs)
    log.inlineandremove("preparation removed %s mallocs in total" % count)
    return count

def clever_inlining_and_malloc_removal(translator, graphs=None,
                                       threshold=BIG_THRESHOLD,
                                       heuristic=inline.inlining_heuristic):
    if graphs is None:
        graphs = translator.graphs
    count = 0
    while 1:
        newcount = inline_and_remove(translator, graphs, threshold=threshold,
                                     heuristic=heuristic)
        if not newcount:
            break
        count += newcount
    for graph in graphs:
        removenoops.remove_superfluous_keep_alive(graph)
        removenoops.remove_duplicate_casts(graph, translator)
    return count

