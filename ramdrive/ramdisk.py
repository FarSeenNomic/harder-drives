import nbdkit
import errno

disk = bytearray(1024 * 1024)

API_VERSION = 2

def config(key, value):
    nbdkit.debug("ignored parameter %s=%s" % (key, value))

def open(readonly):
    nbdkit.debug("opening!~")
    return 1

def block_size(h):
    nbdkit.debug("block_size")
    return (32, 512, 1024)

def get_size(h):
    global disk
    return len(disk)

def pread(h, buf, offset, flags):
    global disk
    end = offset + len(buf)
    buf[:] = disk[offset:end]

def pwrite(h, buf, offset, flags):
    global disk
    end = offset + len(buf)
    disk[offset:end] = buf

def zero(h, count, offset, flags):
    global disk
    if flags & nbdkit.FLAG_MAY_TRIM:
        disk[offset:offset+count] = bytearray(count)
    else:
        nbdkit.set_error(errno.EOPNOTSUPP)
        raise Exception
