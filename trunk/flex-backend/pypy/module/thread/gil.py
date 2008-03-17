"""
Global Interpreter Lock.
"""

# This module adds a global lock to an object space.
# If multiple threads try to execute simultaneously in this space,
# all but one will be blocked.  The other threads get a chance to run
# from time to time, using the executioncontext's XXX

import thread
from pypy.interpreter.miscutils import Action
from pypy.module.thread.threadlocals import OSThreadLocals


class GILThreadLocals(OSThreadLocals):
    """A version of OSThreadLocals that enforces a GIL."""

    def __init__(self):
        OSThreadLocals.__init__(self)
        self.GIL = thread.allocate_lock()

    def enter_thread(self, space):
        "Notification that the current thread is just starting: grab the GIL."
        self.GIL.acquire(True)
        OSThreadLocals.enter_thread(self, space)

    def leave_thread(self, space):
        "Notification that the current thread is stopping: release the GIL."
        OSThreadLocals.leave_thread(self, space)
        self.GIL.release()

    def yield_thread(self):
        """Notification that the current thread is between two bytecodes:
        release the GIL for a little while."""
        GIL = self.GIL
        GIL.release()
        # Other threads can run here
        GIL.acquire(True)
    yield_thread._annspecialcase_ = 'specialize:yield_thread'

    def getGIL(self):
        return self.GIL    # XXX temporary hack!


class GILReleaseAction(Action):
    """An action called when the current thread is between two bytecodes
    (so that it's a good time to yield some time to other threads).
    """
    repeat = True

    def __init__(self, threadlocals):
        self.threadlocals = threadlocals

    def perform(self):
        self.threadlocals.yield_thread()
