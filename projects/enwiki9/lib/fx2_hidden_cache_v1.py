"""Bounded C ABI for the fixed hidden-signature cache, with explicit state."""
import ctypes


class Model:
    def __init__(self, library, arm):
        self.lib = ctypes.CDLL(str(library))
        signatures = {
            'cache_new': ([ctypes.c_char], ctypes.c_void_p),
            'cache_delete': ([ctypes.c_void_p], None),
            'cache_predict': ([ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint64, ctypes.c_uint], ctypes.c_int),
            'cache_observe': ([ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
            'cache_state': ([ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint], ctypes.c_uint),
            'cache_state_size': ([], ctypes.c_uint),
            'cache_distance': ([ctypes.c_uint64, ctypes.c_uint64], ctypes.c_uint),
        }
        for name, (args, result) in signatures.items():
            f = getattr(self.lib, name); f.argtypes = args; f.restype = result
        self.handle = self.lib.cache_new(arm.encode())
        if not self.handle: raise ValueError('invalid cache arm or allocation failure')
        self.size = self.lib.cache_state_size()
        if self.size != 38102: raise ValueError('state layout differs')
        self.buffer = ctypes.create_string_buffer(self.size)

    def predict(self, count, signature, valid):
        if not isinstance(count, int) or not 1 <= count < 65536:
            raise ValueError('count domain')
        if not isinstance(signature, int) or not 0 <= signature < 1 << 64 or valid not in (0, 1):
            raise ValueError('feature domain')
        q = self.lib.cache_predict(self.handle, count, signature, valid)
        if not 1 <= q < 65536: raise ValueError('cache prediction rejected')
        return q

    def observe(self, bit):
        if bit not in (0, 1) or self.lib.cache_observe(self.handle, bit) != 1:
            raise ValueError('cache observation rejected')

    def state(self):
        if self.lib.cache_state(self.handle, self.buffer, self.size) != self.size:
            raise ValueError('cache state rejected')
        return self.buffer.raw

    def close(self):
        if self.handle: self.lib.cache_delete(self.handle); self.handle = None

    def __enter__(self): return self
    def __exit__(self, *args): self.close()
