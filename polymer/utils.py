from hashlib import sha256
from functools import reduce
from operator import iconcat
from base64 import b32encode

def sexyhash(*args, **kwa):
    h = sha256()
    for _ in list(args) + reduce(iconcat, sorted(list(kwa.items())), []):
        if isinstance(_, (set,list)):
            for x in _:
                h.update(str(x).encode('utf-8'))
        else:
            h.update(str(_).encode('utf-8'))
    return b32encode(h.digest()[:10]).decode('ascii')
