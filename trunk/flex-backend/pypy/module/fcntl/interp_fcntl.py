from pypy.rpython.rctypes.tool import ctypes_platform
from pypy.rpython.rctypes.tool.libc import libc
import pypy.rpython.rctypes.implementation # this defines rctypes magic
from pypy.rpython.rctypes.aerrno import geterrno
from pypy.interpreter.error import OperationError
from pypy.interpreter.baseobjspace import W_Root, ObjSpace
from ctypes import *
import sys

class CConfig:
    _header_ = """
    #include <fcntl.h>
    #include <sys/file.h>
    #include <sys/ioctl.h>
    """
    flock = ctypes_platform.Struct("struct flock",
        [('l_start', c_longlong), ('l_len', c_longlong),
        ('l_pid', c_long), ('l_type', c_short),
        ('l_whence', c_short)])
    
# constants, look in fcntl.h and platform docs for the meaning
# some constants are linux only so they will be correctly exposed outside 
# depending on the OS
constants = {}
constant_names = ['LOCK_SH', 'LOCK_EX', 'LOCK_NB', 'LOCK_UN', 'F_DUPFD',
    'F_GETFD', 'F_SETFD', 'F_GETFL', 'F_SETFL', 'F_UNLCK', 'FD_CLOEXEC',
    'LOCK_MAND', 'LOCK_READ', 'LOCK_WRITE', 'LOCK_RW', 'F_GETSIG', 'F_SETSIG', 
    'F_GETLK64', 'F_SETLK64', 'F_SETLKW64', 'F_GETLK', 'F_SETLK', 'F_SETLKW',
    'F_GETOWN', 'F_SETOWN', 'F_RDLCK', 'F_WRLCK', 'F_SETLEASE', 'F_GETLEASE',
    'F_NOTIFY', 'F_EXLCK', 'F_SHLCK', 'DN_ACCESS', 'DN_MODIFY', 'DN_CREATE',
    'DN_DELETE', 'DN_RENAME', 'DN_ATTRIB', 'DN_MULTISHOT', 'I_NREAD',
    'I_PUSH', 'I_POP', 'I_LOOK', 'I_FLUSH', 'I_SRDOPT', 'I_GRDOPT', 'I_STR', 
    'I_SETSIG', 'I_GETSIG', 'I_FIND', 'I_LINK', 'I_UNLINK', 'I_PEEK',
    'I_FDINSERT', 'I_SENDFD', 'I_RECVFD', 'I_SWROPT', 'I_LIST', 'I_PLINK',
    'I_PUNLINK', 'I_FLUSHBAND', 'I_CKBAND', 'I_GETBAND', 'I_ATMARK',
    'I_SETCLTIME', 'I_GETCLTIME', 'I_CANPUT']
for name in constant_names:
    setattr(CConfig, name, ctypes_platform.DefinedConstantInteger(name))

class cConfig:
    pass

cConfig.__dict__.update(ctypes_platform.configure(CConfig))
cConfig.flock.__name__ = "_flock"

if "linux" in sys.platform:
    cConfig.F_GETSIG = 11
    cConfig.F_SETSIG = 10
    cConfig.F_GETLEASE = 1025
    cConfig.F_SETLEASE = 1024

# needed to export the constants inside and outside. see __init__.py
for name in constant_names:
    value = getattr(cConfig, name)
    if value is not None:
        constants[name] = value
locals().update(constants)

_flock = cConfig.flock
libc.strerror.restype = c_char_p
libc.strerror.argtypes = [c_int]

fcntl_int = libc['fcntl']
fcntl_int.argtypes = [c_int, c_int, c_int]
fcntl_int.restype = c_int

fcntl_str = libc['fcntl']
fcntl_str.argtypes = [c_int, c_int, c_char_p]
fcntl_str.restype = c_int

fcntl_flock = libc['fcntl']
fcntl_flock.argtypes = [c_int, c_int, POINTER(_flock)]
fcntl_flock.restype = c_int

ioctl_int = libc['ioctl']
ioctl_int.argtypes = [c_int, c_int, c_int]
ioctl_int.restype = c_int

ioctl_str = libc['ioctl']
ioctl_str.argtypes = [c_int, c_int, c_char_p]
ioctl_str.restype = c_int


has_flock = False
if hasattr(libc, "flock"):
    libc.flock.argtypes = [c_int, c_int]
    libc.flock.restype = c_int
    has_flock = True

def _get_error_msg():
    errno = geterrno()
    return libc.strerror(errno)

def _get_module_object(space, obj_name):
    w_module = space.getbuiltinmodule('fcntl')
    w_obj = space.getattr(w_module, space.wrap(obj_name))
    return w_obj

def _conv_descriptor(space, w_f):
    w_conv_descriptor = _get_module_object(space, "_conv_descriptor")
    w_fd = space.call_function(w_conv_descriptor, w_f)
    return space.int_w(w_fd)

def _check_flock_op(space, op):
    l = _flock()

    if op == LOCK_UN:
        l.l_type = F_UNLCK
    elif op & LOCK_SH:
        l.l_type = F_RDLCK
    elif op & LOCK_EX:
        l.l_type = F_WRLCK
    else:
        raise OperationError(space.w_ValueError,
            space.wrap("unrecognized flock argument"))
    return l

def fcntl(space, w_fd, op, w_arg=0):
    """fcntl(fd, op, [arg])

    Perform the requested operation on file descriptor fd.  The operation
    is defined by op and is operating system dependent.  These constants are
    available from the fcntl module.  The argument arg is optional, and
    defaults to 0; it may be an int or a string. If arg is given as a string,
    the return value of fcntl is a string of that length, containing the
    resulting value put in the arg buffer by the operating system. The length
    of the arg string is not allowed to exceed 1024 bytes. If the arg given
    is an integer or if none is specified, the result value is an integer
    corresponding to the return value of the fcntl call in the C code."""

    fd = _conv_descriptor(space, w_fd)
    
    if space.is_w(space.type(w_arg), space.w_int):
        rv = fcntl_int(fd, op, space.int_w(w_arg))
        if rv < 0:
            raise OperationError(space.w_IOError,
                space.wrap(_get_error_msg()))
        return space.wrap(rv)
    elif space.is_w(space.type(w_arg), space.w_str):
        arg = space.str_w(w_arg)
        if len(arg) > 1024:
            raise OperationError(space.w_ValueError,
                space.wrap("fcntl string arg too long"))
        rv = fcntl_str(fd, op, arg)
        if rv < 0:
            raise OperationError(space.w_IOError,
                space.wrap(_get_error_msg()))
        return space.wrap(arg)
    else:
        raise OperationError(space.w_TypeError,
            space.wrap("int or string required"))
fcntl.unwrap_spec = [ObjSpace, W_Root, int, W_Root]

def flock(space, w_fd, op):
    """flock(fd, operation)

    Perform the lock operation op on file descriptor fd.  See the Unix
    manual flock(3) for details.  (On some systems, this function is
    emulated using fcntl().)"""

    fd = _conv_descriptor(space, w_fd)

    if has_flock:
        rv = libc.flock(fd, op)
        if rv < 0:
            raise OperationError(space.w_IOError,
                space.wrap(_get_error_msg()))
    else:
        l = _check_flock_op(space, op)
        l.l_whence = l.l_start = l.l_len = 0
        op = [F_SETLKW, F_SETLK][op & LOCK_NB]
        fcntl_flock(fd, op, byref(l))
flock.unwrap_spec = [ObjSpace, W_Root, int]

def lockf(space, w_fd, op, length=0, start=0, whence=0):
    """lockf (fd, operation, length=0, start=0, whence=0)

    This is essentially a wrapper around the fcntl() locking calls.  fd is the
    file descriptor of the file to lock or unlock, and operation is one of the
    following values:

    LOCK_UN - unlock
    LOCK_SH - acquire a shared lock
    LOCK_EX - acquire an exclusive lock

    When operation is LOCK_SH or LOCK_EX, it can also be bit-wise OR'd with
    LOCK_NB to avoid blocking on lock acquisition.  If LOCK_NB is used and the
    lock cannot be acquired, an IOError will be raised and the exception will
    have an errno attribute set to EACCES or EAGAIN (depending on the
    operating system -- for portability, check for either value).

    length is the number of bytes to lock, with the default meaning to lock to
    EOF.  start is the byte offset, relative to whence, to that the lock
    starts.  whence is as with fileobj.seek(), specifically:

    0 - relative to the start of the file (SEEK_SET)
    1 - relative to the current buffer position (SEEK_CUR)
    2 - relative to the end of the file (SEEK_END)"""

    fd = _conv_descriptor(space, w_fd)

    l = _check_flock_op(space, op)
    l.l_start = l.l_len = 0

    if start:
        l.l_start = int(start)
    if len:
        l.l_len = int(length)
    l.l_whence = whence

    try:
        op = [F_SETLKW, F_SETLK][op & LOCK_NB]
    except IndexError:
        raise OperationError(space.w_ValueError,
            space.wrap("invalid value for operation"))
    fcntl_flock(fd, op, byref(l))
lockf.unwrap_spec = [ObjSpace, W_Root, int, int, int, int]

def ioctl(space, w_fd, op, w_arg=0, mutate_flag=True):
    """ioctl(fd, opt[, arg[, mutate_flag]])

    Perform the requested operation on file descriptor fd.  The operation is
    defined by opt and is operating system dependent.  Typically these codes
    are retrieved from the fcntl or termios library modules.

    The argument arg is optional, and defaults to 0; it may be an int or a
    buffer containing character data (most likely a string or an array).

    If the argument is a mutable buffer (such as an array) and if the
    mutate_flag argument (which is only allowed in this case) is true then the
    buffer is (in effect) passed to the operating system and changes made by
    the OS will be reflected in the contents of the buffer after the call has
    returned.  The return value is the integer returned by the ioctl system
    call.

    If the argument is a mutable buffer and the mutable_flag argument is not
    passed or is false, the behavior is as if a string had been passed.  This
    behavior will change in future releases of Python.

    If the argument is an immutable buffer (most likely a string) then a copy
    of the buffer is passed to the operating system and the return value is a
    string of the same length containing whatever the operating system put in
    the buffer.  The length of the arg buffer in this case is not allowed to
    exceed 1024 bytes.

    If the arg given is an integer or if none is specified, the result value
    is an integer corresponding to the return value of the ioctl call in the
    C code."""
    fd = _conv_descriptor(space, w_fd)
    # Python turns number > sys.maxint into long, we need the signed C value
    op = c_int(op).value

    IOCTL_BUFSZ = 1024
    
    if space.is_w(space.type(w_arg), space.w_int):
        arg = space.int_w(w_arg)
        rv = ioctl_int(fd, op, arg)
        if rv < 0:
            raise OperationError(space.w_IOError,
                space.wrap(_get_error_msg()))
        return space.wrap(rv)
    elif space.is_w(space.type(w_arg), space.w_str): # immutable
        arg = space.str_w(w_arg)
        if len(arg) > IOCTL_BUFSZ:
            raise OperationError(space.w_ValueError,
                space.wrap("ioctl string arg too long"))
    
        buf = create_string_buffer(len(arg))
    
        rv = ioctl_str(fd, op, buf)
        if rv < 0:
            raise OperationError(space.w_IOError,
                space.wrap(_get_error_msg()))
        return space.wrap(buf.raw)
    else:
        raise OperationError(space.w_TypeError,
                space.wrap("an integer or a buffer required"))
        # try:
        #     # array.array instances
        #     arg = space.call_method(w_arg, "tostring")
        #     buf = create_string_buffer(len(arg))
        # except:
        #     raise OperationError(space.w_TypeError,
        #         space.wrap("an integer or a buffer required"))
        # 
        # if not mutate_flag:
        #     if len(arg) > IOCTL_BUFSZ:
        #         raise OperationError(space.w_ValueError,
        #             space.wrap("ioctl string arg too long"))
        # 
        # rv = ioctl_str(fd, op, buf)
        # if rv < 0:
        #     raise OperationError(space.w_IOError,
        #         space.wrap(_get_error_msg()))
        # 
        # if mutate_flag:
        #     return space.wrap(rv)
        # else:
        #     return space.wrap(buf.value)
ioctl.unwrap_spec = [ObjSpace, W_Root, int, W_Root, int]
