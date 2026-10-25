# ps2cdec.py <in.BIN.ENC> <out.iso> [klic_hex]
# Decrypt a PS3 "PS2 Classics" image (cex) to a plain PS2 ISO. Own Python re-implementation of the
# GPLv3 ps2classic algorithm (flatz): AES-128-CBC with a zero IV; the data and meta keys are
# AES-CBC-encrypt(constant key, klicensee). Default klicensee = the public "PS2 Classics Placeholder" one.
import sys, struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CEX_META = bytes.fromhex('389DCBA5203C8159ECF94C9393164CC9')
CEX_DATA = bytes.fromhex('1017823463F468C1AA41D700B140F257')
IV = bytes(16)

inp, outp = sys.argv[1], sys.argv[2]
klic = bytes.fromhex(sys.argv[3] if len(sys.argv) > 3 else 'E4E54FD67C16C316F47829A30484D843')


def enc(key, data):
    e = Cipher(algorithms.AES(key), modes.CBC(IV)).encryptor()
    return e.update(data) + e.finalize()


def dec(key, data):
    d = Cipher(algorithms.AES(key), modes.CBC(IV)).decryptor()
    return d.update(data) + d.finalize()


dkey, mkey = enc(CEX_DATA, klic), enc(CEX_META, klic)
with open(inp, 'rb') as f, open(outp, 'wb') as o:
    h = f.read(256)
    assert h[:4] == b'PS2\0', h[:8]
    seg = struct.unpack('>I', h[0x84:0x88])[0]
    size = struct.unpack('>Q', h[0x88:0x90])[0]
    nchild = seg // 0x20
    print('segment %x size %d' % (seg, size), flush=True)
    f.seek(seg)
    left = size
    done = 0
    while left > 0:
        meta = f.read(seg)
        if not meta:
            break
        data = f.read(seg * nchild)
        out = b''.join(dec(dkey, data[i:i + seg]) for i in range(0, len(data), seg))
        o.write(out[:min(len(out), left)])
        left -= len(out)
        done += len(out)
        if done % (512 << 20) == 0:
            print(done >> 20, 'MB', flush=True)
print('done', size)
