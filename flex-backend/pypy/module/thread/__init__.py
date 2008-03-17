
# Package initialisation
from pypy.interpreter.mixedmodule import MixedModule

class Module(MixedModule):
    appleveldefs = {
        'exit':                   'app_thread.exit',
        'exit_thread':            'app_thread.exit',   # obsolete synonym
        'error':                  'app_thread.error',
    }

    interpleveldefs = {
        'start_new_thread':       'os_thread.start_new_thread',
        'start_new':              'os_thread.start_new_thread', # obsolete syn.
        'get_ident':              'os_thread.get_ident',
        'allocate_lock':          'os_lock.allocate_lock',
        'allocate':               'os_lock.allocate_lock',  # obsolete synonym
        'LockType':               'os_lock.getlocktype(space)',
        '_local':                 'os_local.getlocaltype(space)',
        '_please_provide_import_lock': '(space.w_True)',   # for imp.py
    }

    def __init__(self, space, *args):
        "NOT_RPYTHON: patches space.threadlocals to use real threadlocals"
        from pypy.module.thread import gil
        MixedModule.__init__(self, space, *args)
        prev = space.threadlocals.getvalue()
        space.threadlocals = gil.GILThreadLocals()
        space.threadlocals.setvalue(prev)
        space.threadlocals.enter_thread(space)   # setup the main thread
        # add the GIL-releasing callback as an action on the space
        space.pending_actions.append(gil.GILReleaseAction(space.threadlocals))

    def setup_after_space_initialization(self):
        # the import lock is in imp.py.  Import it after the space is fully
        # initialized.
        from pypy.module.__builtin__.importing import importhook
        importhook(self.space, 'imp')
