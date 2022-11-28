import nbdkit
#nbdkit = lambda x: x
#nbdkit.NBDKIT_THREAD_MODEL_SERIALIZE_CONNECTIONS = 1
#nbdkit.debug = print

from PIL import Image
from os.path import exists, abspath

API_VERSION = 2

#RGB565
def encode(r, g, b, v):
    """
    Treats RGB888 as RGB565, with the lowest bits sized enough for a byte
    That lowest byte is XOR'd with the same # of bits above it that it replaced, to add to static

    Example:
    Start:
    RRRRRRRR GGGGGGGG BBBBBBBB VVVVVVVV
    11111??? 101010?? 10101??? xxxyyzzz
    Wipe lowest bits, and seperate values
    RRRRRRRR GGGGGGGG BBBBBBBB VVV-VV-VVV
    11111___ 101010__ 10101___ xxx-yy-zzz
    Shift upper bits into space of lower bits
    11111___ 101010__ 10101___
       11111   101010    10101

        11111xxx 101010yy 10101zzz
    XOR 00000111 00000010 00000101

    All the XORing means there's no longer a _slightly_ whiter box around the magic data.
    """
    nr = (r & 0xF8)
    nr |= (v>>0 & 0x7) ^ (r>>3 & 0x7)

    ng = (g & 0xFC)
    ng |= (v>>3 & 0x3) ^ (g>>2 & 0x3)

    nb = (b & 0xF8)
    nb |= (v>>5 & 0x7) ^ (b>>3 & 0x7)

    return (nr, ng, nb)

def decode(r, g, b):
    return (
        (((r ^ r>>3) & 0x7) << 0) |
        (((g ^ g>>2) & 0x3) << 3) |
        (((b ^ b>>3) & 0x7) << 5)
        )
    return (
        (((r & 0x7) ^ (r>>3 & 0x7)) << 0) |
        (((g & 0x3) ^ (g>>2 & 0x3)) << 3) |
        (((b & 0x7) ^ (b>>3 & 0x7)) << 5)
        )
"""
for i in [0, 1, 2, 4, 8, 16, 32, 64, 128]:
    u = encode(0, 0, 0, i)
    print(i, u, decode(*u))
"""

filename = None
img = None
pixels = None
block_size_w = 1
block_count = 0

def config(key, value):
    global filename
    if key == "file":
        filename = abspath(value)
    else:
        raise RuntimeError(f"unknown parameter: {key}")

def config_complete():
    if filename is None:
        raise RuntimeError("file parameter is required.")
    if not exists(filename):
        raise RuntimeError("File does not exist.")

def get_ready():
    global filename, pixels, img, block_size_w, block_count
    img = Image.open(filename, 'r')
    pixels = img.load()
    block_size_w = 1<<(img.size[0].bit_length()-1)
    block_count = img.size[1]
    nbdkit.debug(f"Detected block size of {block_size_w}")
    nbdkit.debug(f"Detected block count of {block_count}")
    return 0

def thread_model():
    return nbdkit.THREAD_MODEL_SERIALIZE_CONNECTIONS

def open(readonly):
    #random number
    return 0xFF

def get_size(h):
    return block_size_w*block_count

def block_size(h):
    return (1, block_size_w, 0xffffffff)

def pread(h, buf, offset, flags):
    for pos in range(len(buf)):
        index = (pos+offset) % block_size_w
        block = (pos+offset) // block_size_w
        t = decode(*pixels[index, block])
        buf[pos] = t
    return 0

def pwrite(h, buf, offset, flags):
    for pos in range(len(buf)):
        index = (pos+offset) % block_size_w
        block = (pos+offset) // block_size_w
        pixels[index, block] = encode(*pixels[index, block], buf[pos])
    return 0

def can_fua(h):
    return nbdkit.FUA_EMULATE

def flush(h, flags):
    img.save(filename)
    return 0

def close(h):
    pass

def cleanup():
    img.close()
