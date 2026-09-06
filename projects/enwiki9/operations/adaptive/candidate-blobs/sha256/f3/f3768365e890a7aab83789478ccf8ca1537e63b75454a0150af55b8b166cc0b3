import json
import signal
from projects.enwiki9.tools import causal_wordcode_fifo128_bz2_v1 as codec

def compress_arm(data, arm):
    signal.alarm(180)
    try:
        return codec.compress_arm(data, arm)
    finally:
        signal.alarm(0)

def decompress_arm(data, arm):
    signal.alarm(180)
    try:
        raw = codec.decompress_arm(data, arm)
        print("CAUSAL_WORDCODE_DECODE " + json.dumps(codec.stats(), sort_keys=True))
        return raw
    finally:
        signal.alarm(0)

stats = codec.stats
