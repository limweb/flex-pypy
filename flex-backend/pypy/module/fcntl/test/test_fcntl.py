from pypy.conftest import gettestobjspace
import os

if os.name == "nt":
    from py.test import skip
    skip("fcntl module is not available on Windows")

def teardown_module(mod):
    for i in "abcde":
        if os.path.exists(i):
            os.unlink(i)

class AppTestFcntl:
    def setup_class(cls):
        space = gettestobjspace(usemodules=('fcntl',))
        cls.space = space

    def test_conv_descriptor(self):
        import fcntl
        
        f = open("a", "w+")
        
        raises(TypeError, fcntl._conv_descriptor, "foo")
        raises(TypeError, fcntl._conv_descriptor, 2.0)
        import cStringIO
        raises(TypeError, fcntl._conv_descriptor, cStringIO.StringIO())
        res = fcntl._conv_descriptor(10)
        res_1 = fcntl._conv_descriptor(f)
        assert res == 10
        assert res_1 == f.fileno()
        
        f.close()

    def test_fcntl(self):
        import fcntl
        import os
        import sys
        import struct
        
        f = open("b", "w+")
        
        fcntl.fcntl(f, 1, 0)
        fcntl.fcntl(f, 1)
        raises(TypeError, fcntl.fcntl, "foo")
        raises(TypeError, fcntl.fcntl, f, "foo")
        raises(IOError, fcntl.fcntl, -1, 1, 0)
        assert fcntl.fcntl(f, 1, 0) == 0
        assert fcntl.fcntl(f, 2, "foo") == "foo"
        
        try:
            os.O_LARGEFILE
        except AttributeError:
            start_len = "ll"
        else:
            start_len = "qq"

        if sys.platform in ('netbsd1', 'netbsd2', 'netbsd3', 
                            'Darwin1.2', 'darwin',
                            'freebsd2', 'freebsd3', 'freebsd4', 'freebsd5',
                            'freebsd6', 'freebsd7', 
                            'bsdos2', 'bsdos3', 'bsdos4',
                            'openbsd', 'openbsd2', 'openbsd3'):
            if struct.calcsize('l') == 8:
                off_t = 'l'
                pid_t = 'i'
            else:
                off_t = 'lxxxx'
                pid_t = 'l'

            format = "%s%s%shh" % (off_t, off_t, pid_t)
            lockdata = struct.pack(format, 0, 0, 0, fcntl.F_WRLCK, 0)
        else:
            format = "hh%shh" % start_len
            lockdata = struct.pack(format, fcntl.F_WRLCK, 0, 0, 0, 0, 0)

        rv = fcntl.fcntl(f.fileno(), fcntl.F_SETLKW, lockdata)
        assert rv == lockdata
        assert fcntl.fcntl(f, fcntl.F_SETLKW, lockdata) == lockdata

        # test duplication of file descriptor
        rv = fcntl.fcntl(f, fcntl.F_DUPFD)
        assert rv > 2 # > (stdin, stdout, stderr) at least
        assert fcntl.fcntl(f, fcntl.F_DUPFD) > rv
        assert fcntl.fcntl(f, fcntl.F_DUPFD, 99) == 99

        # test descriptor flags
        assert fcntl.fcntl(f, fcntl.F_GETFD) == 0
        fcntl.fcntl(f, fcntl.F_SETFD, 1)
        assert fcntl.fcntl(f, fcntl.F_GETFD, fcntl.FD_CLOEXEC) == 1

        # test status flags
        assert fcntl.fcntl(f.fileno(), fcntl.F_SETFL, os.O_NONBLOCK) == 0
        assert fcntl.fcntl(f.fileno(), fcntl.F_SETFL, os.O_NDELAY) == 0
        assert fcntl.fcntl(f, fcntl.F_SETFL, os.O_NONBLOCK) == 0
        assert fcntl.fcntl(f, fcntl.F_SETFL, os.O_NDELAY) == 0

        if "linux" in sys.platform:
            # test managing signals
            assert fcntl.fcntl(f, fcntl.F_GETOWN) == 0
            fcntl.fcntl(f, fcntl.F_SETOWN, 20)
            assert fcntl.fcntl(f, fcntl.F_GETOWN) == 20
            assert fcntl.fcntl(f, fcntl.F_GETSIG) == 0
            fcntl.fcntl(f, fcntl.F_SETSIG, 20)
            assert fcntl.fcntl(f, fcntl.F_GETSIG) == 20

            # test leases
            assert fcntl.fcntl(f, fcntl.F_GETLEASE) == fcntl.F_UNLCK
            fcntl.fcntl(f, fcntl.F_SETLEASE, fcntl.F_WRLCK)
            assert fcntl.fcntl(f, fcntl.F_GETLEASE) == fcntl.F_WRLCK
        else:
            # this tests should fail under BSD
            # with "Inappropriate ioctl for device"
            raises(IOError, fcntl.fcntl, f, fcntl.F_GETOWN)
            raises(IOError, fcntl.fcntl, f, fcntl.F_SETOWN, 20)
        
        f.close()

    def test_flock(self):
        import fcntl
        import sys
        
        f = open("c", "w+")
        
        raises(TypeError, fcntl.flock, "foo")
        raises(TypeError, fcntl.flock, f, "foo")
        fcntl.flock(f, fcntl.LOCK_SH)
        # this is an error EWOULDBLOCK, man: The file is locked and the
        # LOCK_NB flag was selected.
        raises(IOError, fcntl.flock, f, fcntl.LOCK_NB)
        fcntl.flock(f, fcntl.LOCK_UN)
        
        f.close()

    def test_lockf(self):
        import fcntl
        
        f = open("d", "w+")
        
        raises(TypeError, fcntl.lockf, f, "foo")
        raises(TypeError, fcntl.lockf, f, fcntl.LOCK_UN, "foo")
        raises(ValueError, fcntl.lockf, f, -1)
        raises(ValueError, fcntl.lockf, f, 255)
        
        fcntl.lockf(f, fcntl.LOCK_SH)
        fcntl.lockf(f, fcntl.LOCK_UN)
        
        f.close()

    def test_ioctl(self):
        import fcntl
        import array
        import sys
        
        f = open("e", "w+")
        
        if "linux" in sys.platform:
            TIOCGPGRP = 0x540f
        elif "darwin" in sys.platform or "freebsd6" == sys.platform:
            TIOCGPGRP = 0x40047477
        
        raises(TypeError, fcntl.ioctl, "foo")
        raises(TypeError, fcntl.ioctl, f, "foo")
        raises(TypeError, fcntl.ioctl, f, TIOCGPGRP, float(0))
        raises(TypeError, fcntl.ioctl, f, TIOCGPGRP, 1, "foo")

        # buf = array.array('h', [0])
        # fcntl.ioctl(0, TIOCGPGRP, buf, True)
        # buf = array.array('c', "a"*1025)
        # py.test.raises(ValueError, cfcntl.ioctl, 0, termios.TIOCGPGRP, buf, 0)
        # py.test.raises(ValueError, cfcntl.ioctl, 0, termios.TIOCGPGRP,
        #                "a"*1025, 0)
