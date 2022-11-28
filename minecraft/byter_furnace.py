import configparser
import math
from time import sleep
from mcrcon import MCRcon
from random import randint

"""
Key:
Air = 0
Redstone block = 1
Diamond block at lowest bit of layer = Empty Layer else 0
"""

#1 block = 1 bit
#1 byte = 8 bits
#1 line = 1 short = 2 bytes = 16 bits = 16 blocks
#1 layer = 16 lines
#1 sub-chunk = 16 layers
#1 chuck = 16 sub-chunks

def ceil_to(x, n):
    return int(math.ceil(x / n)) * n

def bit_count(n):
    """Returns the count of high bits in n"""
    return bin(n).count("1")

def xnor(a, b):
    """Returns the bitwise XNOR operation of a and b"""
    return ~(a^b)

base_x, base_z = 0,0

def bitptr2pos(bitptr):
    """Turns a bit pointer into a 3D position."""
    x = bitptr & 15
    z = (bitptr >> 4) & 15
    y = (bitptr >> 8)
    return [base_x+x, y, base_z+z]

def ptr2bitptr(ptr, index):
    """Turns a byte pointer and the bit's index into a bit pointer."""
    return (ptr<<3)+index

####

def set_bit(bitptr, val):
    x,y,z = bitptr2pos(bitptr)
    if val:
        w=mcr.command(f'setblock {x} {y} {z} redstone_block')
    else:
        w=mcr.command(f'setblock {x} {y} {z} air')

    if w=="The block couldn't be placed":
        return 0^val

    if w=="Block placed":
        return 1^val

    if "The number you have entered" in w:
        raise ValueError("Out of bounds")

    raise ValueError(f"Unknown return code '{w}'")

def set_bits(from_bitptr, to_bitptr, val):
    #no safety yet
    fx,fy,fz=bitptr2pos(from_bitptr)
    tx,ty,tz=bitptr2pos(to_bitptr)
    if val:
        mcr.command(f'fill {fx} {fy} {fz} {tx} {ty} {tz} redstone_block')
    else:
        mcr.command(f'fill {fx} {fy} {fz} {tx} {ty} {tz} air')

def copy_bits(from_bitptr, leng, to_bitptr):
    #no safety yet
    fx1,fy1,fz1=bitptr2pos(from_bitptr)
    fx2,fy2,fz2=bitptr2pos(from_bitptr+leng-1)
    tx, ty, tz =bitptr2pos(to_bitptr)
    mcr.command(f'clone {fx1} {fy1} {fz1} {fx2} {fy2} {fz2} {tx} {ty} {tz}')

#def read_bit(bitptr):
#    x,y,z=bitptr2pos(bitptr)
#    w = mcr.command(f'blockdata {x} {y} {z} {{}}')
#    return "data holder block" not in w

def test_bit(bitptr, block):
    x,y,z = bitptr2pos(bitptr)
    w = mcr.command(f'testforblock {x} {y} {z} {block}')
    return "Successful" in w

def read_bit(bitptr):
    return test_bit(bitptr, "redstone_block")

####

def copy_byte(from_ptr, to_ptr):
    copy_bits(ptr2bitptr(from_ptr, 0), 8, ptr2bitptr(to_ptr, 0))

def write_byte(ptr, byte):
    """
    Writes the byte to the given position.
    Brute force is exactly 8 operations.
    Optimal is mean 3 max 4
    This is mean ? max 5
    """
    from_bitptr = ptr2bitptr(ptr, 0)
    to_bitptr = ptr2bitptr(ptr, 7)

    if bit_count(byte)<=4:
        #Fills space with 0s, then sets up to 4 bits
        set_bits(from_bitptr, to_bitptr, False)
        for i in range(8):
            if byte&(1<<i):
                set_bit(ptr2bitptr(ptr,i), True)
    else:
        #Fills space with 1s, then clears up to 3 bits
        set_bits(from_bitptr, to_bitptr, True)
        for i in range(8):
            if not byte&(1<<i):
                set_bit(ptr2bitptr(ptr,i), False)

    """
    for i in range(8):
        set_bit(ptr2bitptr(ptr,i), byte&(1<<i))
    """

def read_byte(ptr):
    n = 0
    for i in range(8):
        n |= read_bit(ptr2bitptr(ptr,i))<<i
    return n

"""
def zero_area(from_ptr, to_ptr):
    if from_ptr%32 != 0:
        zero_area(from_ptr, ceil_to(from_ptr, 32)-1)
        zero_area(ceil_to(from_ptr, 32),to_ptr)
        return

    if from_ptr%2 == 1:
        write_byte(from_ptr, 0x00)
"""

####

def copy_layers(from_ptr, count, to_ptr):
    if from_ptr%(2*16) != 0:
        raise Exception(f"'from_ptr' ({from_ptr}) must be aligned to layer.")
    if count <= 0:
        raise Exception(f"'count' ({count}) must be positive.")
    if to_ptr%(2*16) != 0:
        raise Exception(f"'to_ptr' ({to_ptr}) must be aligned to layer.")
    copy_bits(ptr2bitptr(from_ptr, 0), 64*count, ptr2bitptr(to_ptr, 0))

def write_layer(ptr, data):
    assert(len(data) == 32)
    assert(ptr % 32 == 0)

    if all(i==0 for i in data):
        x,y,z = bitptr2pos(ptr2bitptr(ptr, 0))
        mcr.command(f'setblock {x} {y} {z} diamond_block')
        return

    #TODO: Slow
    #for i, v in enumerate(data):
    #    write_byte(ptr+i, v)

    from_layerptr = ptr2bitptr(ptr, 0)
    to_layerptr = ptr2bitptr(ptr+31, 7)

    start_layer_high = sum(bit_count(d) for d in data)>=32*4
    set_bits(from_layerptr, to_layerptr, start_layer_high)

    for sub_ptr, byte in enumerate(data):
        tst = list(data).index(byte)
        if tst < sub_ptr:
            # if the same byte has been written before
            copy_byte(ptr+tst, ptr+sub_ptr)
            continue

        start_byte_high = bit_count(byte)>4

        if start_byte_high ^ start_layer_high:
            from_byteptr = ptr2bitptr(ptr+sub_ptr, 0)
            to_byteptr = ptr2bitptr(ptr+sub_ptr, 7)
            set_bits(from_byteptr, to_byteptr, start_byte_high)

        for index in range(8):
            bit_at_index = byte&(1<<index) != 0
            if start_byte_high ^ bit_at_index:
                set_bit(ptr2bitptr(ptr+sub_ptr, index), bit_at_index)

def read_layer(ptr):
    assert(ptr % 32 == 0)

    if test_bit(ptr2bitptr(ptr, 0), "diamond_block"):
        return [0] * 32

    data = [read_byte(ptr+i) for i in range(32)]

    if all(i==0 for i in data):
        x,y,z = bitptr2pos(ptr2bitptr(ptr, 0))
        mcr.command(f'setblock {x} {y} {z} diamond_block')

    return data

####

def write_cstring(ptr, data):
    for i,v in enumerate(data):
        tst = data.index(v)
        sleep(0.05)
        if tst < i:
            copy_byte(ptr+tst, ptr+i)
        else:
            write_byte(ptr+i, v)
    write_byte(ptr+len(data), 0)

def read_cstring(ptr):
    i = ptr
    li = []
    while True:
        b = read_byte(i)
        if b:
            print(chr(b), end='')
            li.append(b)
            i += 1
        else:
            print("NULL")
            break
    return bytes(li)

def pwrite(h, buf, ptr, f):
    for i, v in enumerate(buf):
        tst = data.index(v)
        if tst < i:
            print("copy_byte", ptr+tst, ptr+i)
            copy_byte(ptr+tst, ptr+i)
        else:
            print("write_byte", ptr+i, v)
            write_byte(ptr+i, v)

def pread(h, buf, ptr, f):
    for i, v in enumerate(buf):
        buf[i] = read_byte(ptr+i)
        if sum(buf[i-5:i])==0:
            break


import nbdkit
#nbdkit = lambda x: x
#nbdkit.THREAD_MODEL_SERIALIZE_CONNECTIONS = 1
#nbdkit.debug = print
import builtins

API_VERSION = 2

def config(key, value):
    nbdkit.debug(f"ignored parameter {key}={value}")

mcr = None
def config_complete():
    global mcr
    nbdkit.debug("Loading config...")
    config_file = configparser.ConfigParser()
    #import os
    config_file.read('secret.ini')
    server_config = config_file['LocalServer']

    address = server_config['address']
    port = int(server_config['port'])
    password = server_config['password']

    mcr = MCRcon(address, password, port=port)
    nbdkit.debug(f"Loaded config for: {address}:{port}")
    nbdkit.debug("Connecting...")
    mcr.connect()

def thread_model():
    return nbdkit.THREAD_MODEL_SERIALIZE_CONNECTIONS

def open(readonly):
    if readonly:
        nbdkit.debug("opened readonly")
    return 1

def get_size(h):
    nbdkit.debug("get_size")
    return 0x80000 #20 chunks

def block_size(h):
    nbdkit.debug("block_size!~")
    return (32, 512, 4096)

def pwrite(h, buf, offset, flags):
    for i in range(0, len(buf), 32):
        write_layer(offset+i, buf[i:i+32])

def pread(h, buf, offset, flags):
    for i in range(0, len(buf), 32):
        read_buff = read_layer(offset+i)
        buf[i:i+32] = bytearray(read_buff)

def close(h):
    pass

def unload():
    mcr.disconnect()

####
if __name__ == '__main__':
    from timeit import default_timer as timer

    config_complete()

    from itertools import zip_longest
    def string_layer_padder(iterable, n, fillvalue=None):
        "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    strw = """Meet Skrillex in Phoenix
    Study zymurgy
    Get a pet axolotl named Hexxus
    Observe a syzygy from Zzyzx, California
    Port the games Zzyzzyxx and Xexyz to Xbox
    Publish a Zzzax/Mister Mxyzptlk crossover
    Bike from Xhafzotaj, Albania to Qazaxbəyli, Azerbaijan
    Paint an Archaeopteryx fighting a Muzquizopteryx
    Finish a game of Scrabble without getting punched
    Make something called xkcd"""

    strw = "Тень, знай своё место"
    strw = "XYZZY"
    strw = "Klaatu barada nikto"

    strw = "Oo ee oo ah ah ting tang walla walla bing bang"
    strw = "By the Power of Grayskull, I HAVE THE POWER!!"

    strw = """~He-man and the Masters of The Universe
    I am Adam, Prince of Eternia, Defender of the secrets of Castle Grayskull.
    This is Cringer, my fearless friend.
    Fabulous secret powers were revealed to me the day I held aloft my magic sword and said "By the Power of Grayskull, I HAVE THE POWER!!"
    Cringer became the mighty BattleCat and I became He-man, the most powerful man in the universe.
    Only three others share this secret: our friends the Sorceress, Man-At-Arms and Orko. Together we defend Castle Grayskull from the evil forces of Skeletor."""


    #mcr.command(f'fill {base_x} {0} {base_z} {base_x+15} {20} {base_z+15} air')
    #mcr.disconnect()
    #0 / 0
    """
    start = timer()
    write_cstring(0, strw.encode("utf-8"))
    end = timer()
    print("Write time:", end - start)
    print("Write time per:", (end - start)/len(strw))

    print("expected time:", (len(strw)+1)*0.03903913695652174)
    start = timer()
    print(read_cstring(0).decode("utf-8"))
    end = timer()
    print("Read time:", end - start)
    print("Read time per:", (end - start)/(len(strw)+1))

    layers = list(string_layer_padder((strw+"\x00").encode("utf-8"), 32, 0))
    for i in range(len(layers)):
        write_layer(32*i, layers[i])

    for i in range(len(layers)):
        print(layers[i])
        print(read_layer(32*i))
    """

    from_bitptr = ptr2bitptr(2048-32, 0)
    to_bitptr = ptr2bitptr(2048-1, 7)
    set_bits(from_bitptr, to_bitptr, False)

    li = list(i & 7 for i in range(32))
    print(li)
    write_layer(2048-32, li)

    unload()