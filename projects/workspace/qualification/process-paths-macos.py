#!/usr/bin/env python3
"""Read exact live executable paths from libproc, without trusting argv/ps titles."""
from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os


def parse_pids() -> list[int]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pids', help='JSON array of owned process IDs')
    pids = json.loads(parser.parse_args().pids)
    if not isinstance(pids, list) or any(
        type(pid) is not int or not 0 < pid <= 0x7fffffff for pid in pids
    ):
        raise ValueError('expected an array of positive 32-bit process IDs')
    return pids


def main() -> int:
    libproc = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    libproc.proc_pidpath.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    libproc.proc_pidpath.restype = ctypes.c_int
    paths: dict[str, str] = {}
    for pid in parse_pids():
        buffer = ctypes.create_string_buffer(4096)  # PROC_PIDPATHINFO_MAXSIZE
        ctypes.set_errno(0)
        if libproc.proc_pidpath(pid, buffer, len(buffer)) <= 0:
            error = ctypes.get_errno()
            if error == errno.ESRCH:
                continue  # exited between the snapshot and kernel query
            raise OSError(error, f'proc_pidpath({pid}): {os.strerror(error)}')
        paths[str(pid)] = os.fsdecode(buffer.value)
    print(json.dumps(paths, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
