"""Conservative next-bit support for one dictionary-enabled WRT text body.

The first byte is encode_text's flag, after the separate five-byte TEXT header.
Only code continuation ranges are constrained; literals and escapes stay broad.
The automaton consumes decoded bits, never eventual event boundaries or lengths.
"""
from hashlib import sha256
import json


def _prefix_mask(prefix):
    length=prefix.bit_length()-1
    width=1<<(8-length)
    start=(prefix-(1<<length))*width
    return ((1<<width)-1)<<start


PREFIX_MASKS=tuple(_prefix_mask(i) if i else 0 for i in range(512))
ALL=(1<<256)-1
SHORT=((1<<80)-1)<<128       # 0x80..0xcf
LONG=((1<<112)-1)<<128      # 0x80..0xef


class WrtSupport:
    def __init__(self):
        self.phase='mode'
        self.prefix=1

    def forced(self):
        allowed=SHORT if self.phase in ('short','third') else LONG if self.phase=='long' else ALL
        zero=bool(allowed&PREFIX_MASKS[self.prefix*2])
        one=bool(allowed&PREFIX_MASKS[self.prefix*2+1])
        if not zero and not one:raise ValueError('empty WRT support')
        return None if zero and one else int(one)

    def observe(self,bit):
        if type(bit) is not int or bit not in (0,1):raise ValueError('nonbinary truth')
        forced=self.forced()
        if forced is not None and bit!=forced:raise ValueError('invalid WRT continuation')
        prefix=self.prefix*2+bit
        if prefix<256:
            self.prefix=prefix
            return
        byte=prefix-256
        phase=self.phase
        if phase=='mode':
            if byte not in (0,7):raise ValueError('unsupported WRT mode')
            phase='disabled' if byte==0 else 'neutral'
        elif phase in ('short','third','escape'):phase='neutral'
        elif phase=='long':phase='third' if byte>=0xd0 else 'neutral'
        elif phase=='neutral':
            # Storage permutation changes only ASCII values unrelated to these
            # control/range transitions; escape0x0c and high code bytes agree.
            if byte==12:phase='escape'
            elif byte>=0xf0:phase='long'
            elif byte>=0xd0:phase='short'
        self.phase=phase
        self.prefix=1

    def finish(self):
        if self.prefix!=1 or self.phase not in ('neutral','disabled'):
            raise ValueError('truncated WRT body')

    def state_digest(self):
        return sha256(json.dumps([self.phase,self.prefix],separators=(',',':')).encode()).hexdigest()
