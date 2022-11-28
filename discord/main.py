import nbdkit
import errno
import random
import base64

from multiprocessing import Process, Queue, Pipe, freeze_support

import sys, os
sys.path.append(os.path.dirname(__file__))
from server import callabl

API_VERSION = 2

class microcord():
    def __init__(self):
        read_c, self.write_p = Pipe()
        self.read_p, write_c = Pipe()
        p = Process(target=callabl, args=(write_c, read_c))
        p.start()

    def send(self, message: str):
        self.write_p.send("SEND")
        self.write_p.send(message)

    def history(self):
        self.write_p.send("HIST")
        while True:
            self.write_p.send("WANT")
            get = self.read_p.recv()
            if not get:
                return
            yield get

    def end(self):
        self.write_p.send("ENDR")

    def fua(self, prefixes):
        self.write_p.send("FUA")
        self.write_p.send(prefixes)

    def flush(self):
        self.write_p.send("FLUSH")

header = int

def config(key, value):
    nbdkit.debug("ignored parameter %s=%s" % (key, value))

def config_complete():
    global client
    client = microcord()

def thread_model():
    return nbdkit.THREAD_MODEL_SERIALIZE_ALL_REQUESTS

def open(readonly: bool) -> header:
    nbdkit.debug("open: readonly=%d" % readonly)
    return 1

atom_size = 1024

def get_size(h: header) -> int:
    """
    Discord doesn't really have a chat limit.
    """
    return 128*atom_size

def block_size(h: header) -> list:
    return (atom_size, atom_size, 0xFFFFFFFF)

def encode_text(buf: bytes) -> str:
    return base64.b64encode(buf).decode('ascii')

def decode_text(text: str) -> bytes:
    return base64.b64decode(text.split(",")[1])

def pwrite(h: header, buf: bytearray, offset: int, flags: int) -> None:
    assert(len(buf) % atom_size == 0)
    assert(offset % atom_size == 0)
    #if flags | nbdkit.FLAG_FUA:
    client.fua(list(f"{alig+offset:08x}," for alig in range(0, len(buf), atom_size)))

    for alig in range(0, len(buf), atom_size):
        client.send(f"{alig+offset:08x},{encode_text(buf[alig:alig+atom_size])}")

def pread(h: header, buf: bytearray, offset: int, flags: int) -> None:
    assert(len(buf) % atom_size == 0)
    assert(offset % atom_size == 0)
    find_list = list(i for i in range(0, len(buf), atom_size))

    for message in client.history():
        for alig in find_list:
            if message.startswith(f"{alig+offset:08x}," ):
                buf[alig:alig+atom_size] = decode_text(message)
                find_list.remove(alig)
                break
        if not find_list:
            break

    if find_list:
        #nbdkit.set_error(errno.EOPNOTSUPP)
        #raise Exception
        pass

def flush(h, flags):
    client.flush()
    return 0

def unload():
    client.end()

if __name__ == '__main__':
    freeze_support()
    #client = microcord()
    #pwrite(1, b'5678', 12, 0)
    #pwrite(1, b'1234', 4, 0)
    #pwrite(1, b'asdf', 8, 0)
    #pwrite(1, b'CAT?', 0, 0)
    #buf = bytearray(4*4)
    #pread(1, buf, 0, 0)
    #print(buf.decode('ascii'))

    #client.flush()

    #client.end()
