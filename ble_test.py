import struct

def writeBytes(file, value = 65535):
    f = None
    try:
        f = open(file, "wb+")
        f.write(struct.pack('H', value))
    finally:
        if f is not None:
            f.close()

writeBytes('id', 65535)