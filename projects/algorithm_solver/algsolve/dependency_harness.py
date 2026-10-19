"""Static in-sandbox bootstrap for the explicitly approved SortedList profile.

The host passes the wheel as one flat read-only task file. No site initialization,
search-path injection, package installer, mount or security policy is changed.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import zipimport

_CONTROL=os.fdopen(os.dup(1),'w',buffering=1)
_WHEEL='/task/vendor-sortedcontainers-2.4.0.whl'
_SHA256='a163dcaede0f1c021485e957a39245190e74249897e2ae4b2aa38595db237ee0'


def main():
    data=Path(_WHEEL).read_bytes()
    if len(data)!=29575 or hashlib.sha256(data).hexdigest()!=_SHA256:
        raise ValueError('Dependency wheel identity mismatch')
    spec=zipimport.zipimporter(_WHEEL).find_spec('sortedcontainers')
    if spec is None or spec.loader is None or not spec.submodule_search_locations:
        raise ValueError('Dependency package spec missing')
    package=importlib.util.module_from_spec(spec)
    sys.modules['sortedcontainers']=package
    spec.loader.exec_module(package)
    if package.__version__!='2.4.0':raise ValueError('Dependency version mismatch')
    spec=importlib.util.spec_from_file_location('_qualified_base_harness','/task/base_harness.py')
    harness=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    # Convenience binding for stored LC references with an implicit import.
    harness.PREAMBLE+='\nfrom sortedcontainers import SortedList\n'
    harness.main()


if __name__=='__main__':
    try:main()
    except BaseException as error:
        _CONTROL.write(json.dumps({'load_error':type(error).__name__,'detail':str(error)[:500]})+'\n')
        raise SystemExit(1)
