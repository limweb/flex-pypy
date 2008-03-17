from pypy.rpython.lltypesystem.lltype import *
from pypy.rpython.test.test_llinterp import interpret, gengraph
from pypy.annotation.policy import AnnotatorPolicy

def test_prebuilt_lock():
    import thread
    import pypy.module.thread.rpython.exttable   # for declare()/declaretype()
    lock0 = thread.allocate_lock()
    lock1 = thread.allocate_lock()
    lock1.acquire()
    def fn(i):
        lock = [lock0, lock1][i]
        ok = lock.acquire(False)
        if ok: lock.release()
        return ok
    policy = AnnotatorPolicy()
    policy.allow_someobjects = False
    res = interpret(fn, [0], policy=policy)
    assert res is True
    res = interpret(fn, [1], policy=policy)
    assert res is False

def test_lock_or_None():
    import thread
    import pypy.module.thread.rpython.exttable   # for declare()/declaretype()
    def makelock(i):
        if i > 0:
            return thread.allocate_lock()
        else:
            return None
    def fn(i):
        lock = makelock(i)
        return lock is not None and lock.acquire(False)
    policy = AnnotatorPolicy()
    policy.allow_someobjects = False
    res = interpret(fn, [0], policy=policy)
    assert res is False
    res = interpret(fn, [1], policy=policy)
    assert res is True
