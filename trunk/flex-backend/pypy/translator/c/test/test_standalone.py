import py
import sys, os

from pypy.translator.translator import TranslationContext
from pypy.translator.backendopt import all
from pypy.translator.c.genc import CStandaloneBuilder
from pypy.annotation.listdef import s_list_of_strings
from pypy.tool.udir import udir


def test_hello_world():
    def entry_point(argv):
        os.write(1, "hello world\n")
        argv = argv[1:]
        os.write(1, "argument count: " + str(len(argv)) + "\n")
        for s in argv:
            os.write(1, "   '" + str(s) + "'\n")
        return 0

    t = TranslationContext()
    t.buildannotator().build_types(entry_point, [s_list_of_strings])
    t.buildrtyper().specialize()

    cbuilder = CStandaloneBuilder(t, entry_point, t.config)
    cbuilder.generate_source()
    cbuilder.compile()
    data = cbuilder.cmdexec('hi there')
    assert data.startswith('''hello world\nargument count: 2\n   'hi'\n   'there'\n''')

def test_print():
    def entry_point(argv):
        print "hello simpler world"
        argv = argv[1:]
        print "argument count:", len(argv)
        print "arguments:", argv
        print "argument lengths:",
        print [len(s) for s in argv]
        return 0

    t = TranslationContext()
    t.buildannotator().build_types(entry_point, [s_list_of_strings])
    t.buildrtyper().specialize()

    cbuilder = CStandaloneBuilder(t, entry_point, t.config)
    cbuilder.generate_source()
    cbuilder.compile()
    data = cbuilder.cmdexec('hi there')
    assert data.startswith('''hello simpler world\n'''
                           '''argument count: 2\n'''
                           '''arguments: [hi, there]\n'''
                           '''argument lengths: [2, 5]\n''')
    # NB. RPython has only str, not repr, so str() on a list of strings
    # gives the strings unquoted in the list

def test_counters():
    if sys.platform == 'win32':
        py.test.skip("instrument counters support is unix only for now")
    from pypy.rpython.lltypesystem import lltype
    from pypy.rpython.lltypesystem.lloperation import llop
    def entry_point(argv):
        llop.instrument_count(lltype.Void, 'test', 2)
        llop.instrument_count(lltype.Void, 'test', 1)
        llop.instrument_count(lltype.Void, 'test', 1)
        llop.instrument_count(lltype.Void, 'test', 2)
        llop.instrument_count(lltype.Void, 'test', 1)        
        return 0
    t = TranslationContext()
    t.config.translation.instrument = True
    t.buildannotator().build_types(entry_point, [s_list_of_strings])
    t.buildrtyper().specialize()

    cbuilder = CStandaloneBuilder(t, entry_point, config=t.config) # xxx
    cbuilder.generate_source()
    cbuilder.compile()

    counters_fname = udir.join("_counters_")
    os.putenv('_INSTRUMENT_COUNTERS', str(counters_fname))
    try:
        data = cbuilder.cmdexec()
    finally:
        os.unsetenv('_INSTRUMENT_COUNTERS')

    f = counters_fname.open('rb')
    counters_data = f.read()
    f.close()

    import struct
    counters = struct.unpack("LLL", counters_data)

    assert counters == (0,3,2)

def test_prof_inline():
    if sys.platform == 'win32':
        py.test.skip("instrumentation support is unix only for now")
    def add(a,b):
        return a + b - b + b - b + b - b + b - b + b - b + b - b + b
    def entry_point(argv):
        tot =  0
        x = int(argv[1])
        while x > 0:
            tot = add(tot, x)
            x -= 1
        os.write(1, str(tot))
        return 0
    from pypy.translator.interactive import Translation
    t = Translation(entry_point, backend='c', standalone=True)
    # no counters
    t.backendopt(inline_threshold=100, profile_based_inline="500")
    exe = t.compile()
    out = py.process.cmdexec("%s 500" % exe)
    assert int(out) == 500*501/2

    t = Translation(entry_point, backend='c', standalone=True)
    # counters
    t.backendopt(inline_threshold=all.INLINE_THRESHOLD_FOR_TEST*0.5,
                 profile_based_inline="500")
    exe = t.compile()
    out = py.process.cmdexec("%s 500" % exe)
    assert int(out) == 500*501/2
    
def test_frexp():
    import math
    def entry_point(argv):
        m, e = math.frexp(0)
        x, y = math.frexp(0)
        print m, x
        return 0

    t = TranslationContext()
    t.buildannotator().build_types(entry_point, [s_list_of_strings])
    t.buildrtyper().specialize()

    cbuilder = CStandaloneBuilder(t, entry_point, t.config)
    cbuilder.generate_source()
    cbuilder.compile()
    data = cbuilder.cmdexec('hi there')
    assert map(float, data.split()) == [0.0, 0.0]

def test_profopt():
    if sys.platform == 'win32':
        py.test.skip("instrumentation support is unix only for now")
    def add(a,b):
        return a + b - b + b - b + b - b + b - b + b - b + b - b + b
    def entry_point(argv):
        tot =  0
        x = int(argv[1])
        while x > 0:
            tot = add(tot, x)
            x -= 1
        os.write(1, str(tot))
        return 0
    from pypy.translator.interactive import Translation
    # XXX this is mostly a "does not crash option"
    t = Translation(entry_point, backend='c', standalone=True, profopt="")
    # no counters
    t.backendopt()
    exe = t.compile()
    out = py.process.cmdexec("%s 500" % exe)
    assert int(out) == 500*501/2
    t = Translation(entry_point, backend='c', standalone=True, profopt="",
                    noprofopt=True)
    # no counters
    t.backendopt()
    exe = t.compile()
    out = py.process.cmdexec("%s 500" % exe)
    assert int(out) == 500*501/2
