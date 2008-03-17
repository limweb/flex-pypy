import platform
import os, stat, errno
import py
from pypy.tool import udir
from pypy.translator.cli.test.runtest import CliTest
from pypy.rpython.test.test_rbuiltin import BaseTestRbuiltin

def skip_os(self):
    py.test.skip("CLI doesn't support the os module, yet")

def skip_win():
    if platform.system() == 'Windows':
        py.test.skip("Doesn't work on Windows, yet")

class TestCliBuiltin(CliTest, BaseTestRbuiltin):
    test_os_dup = skip_os
    test_os_path_exists = skip_os
    test_os_isdir = skip_os

    def test_builtin_math_frexp(self):
        self._skip_powerpc("Mono math floating point problem")
        BaseTestRbuiltin.test_builtin_math_frexp(self)
    
    def test_os_flags(self):
        from pypy.translator.cli.support import NT_OS
        def fn():
            return os.O_CREAT
        assert self.interpret(fn, []) == NT_OS['O_CREAT']

    def test_os_read(self):
        BaseTestRbuiltin.test_os_read(self)

    def test_os_read_binary_crlf(self):
        tmpfile = str(udir.udir.join("os_read_test"))
        def fn(flag):
            if flag:
                fd = os.open(tmpfile, os.O_RDONLY|os.O_BINARY, 0666)
            else:
                fd = os.open(tmpfile, os.O_RDONLY, 0666)
            res = os.read(fd, 4096)
            os.close(fd)
            return res
        f = file(tmpfile, 'w')
        f.write('Hello\nWorld')
        f.close()
        res = self.ll_to_string(self.interpret(fn, [True]))
        assert res == file(tmpfile, 'rb').read()
        res = self.ll_to_string(self.interpret(fn, [False]))
        assert res == file(tmpfile, 'r').read()

    # the following tests can't be executed with gencli because they
    # returns file descriptors, and cli code is executed in another
    # process. Instead of those, there is a new test that opens and
    # write to a file all in the same process.
    def test_os_write(self):
        pass
    def test_os_write_single_char(self):
        pass
    def test_os_open(self):
        pass

    def test_os_open_write(self):
        tmpdir = str(udir.udir.join("os_write_test"))
        def fn():
            fd = os.open(tmpdir, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0777)            
            os.write(fd, "hello world")
            os.close(fd)
        self.interpret(fn, [])
        assert file(tmpdir).read() == 'hello world'

    def test_os_write_magic(self):
        MAGIC = 62061 | (ord('\r')<<16) | (ord('\n')<<24)
        tmpfile = str(udir.udir.join("os_write_test"))
        def long2str(x):
            a = x & 0xff
            x >>= 8
            b = x & 0xff
            x >>= 8
            c = x & 0xff
            x >>= 8
            d = x & 0xff
            return chr(a) + chr(b) + chr(c) + chr(d)
        def fn(magic):
            fd = os.open(tmpfile, os.O_BINARY|os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0777)
            os.write(fd, long2str(magic))
            os.close(fd)
        self.interpret(fn, [MAGIC])
        contents = file(tmpfile, 'rb').read()
        assert contents == long2str(MAGIC)

    def test_os_stat(self):
        def fn():
            return os.stat('.')[0]
        mode = self.interpret(fn, [])
        assert stat.S_ISDIR(mode)

    def test_os_stat_oserror(self):
        def fn():
            return os.stat('/directory/unlikely/to/exists')[0]
        self.interpret_raises(OSError, fn, [])

    def test_os_strerror(self):
        def fn():
            return os.strerror(errno.ENOTDIR)
        res = self.ll_to_string(self.interpret(fn, []))
        # XXX assert something about res

    def test_os_opendir(self):
        from pypy.rlib import ros
        def fn():
            d = ros.opendir('.')
            res = []
            while True:
                current = d.readdir()
                if current is None:
                    break
                res.append(current)
            d.closedir()
            return res
        res = self.ll_to_list(self.interpret(fn, []))
        res = [self.ll_to_string(s) for s in res]
        res.sort()
        assert res == sorted(os.listdir('.'))

    # XXX: remember to test ll_os_readlink and ll_os_pipe as soon as
    # they are implemented

    def test_os_path_join(self):
        import os.path
        def fn(a, b):
            return os.path.join(a, b)
        res = self.ll_to_string(self.interpret(fn, ['a', 'b']))
        assert res == os.path.join('a', 'b')
