"""The sole approved optional wheel, validated before entering a task sandbox."""
import hashlib
import io
from pathlib import Path,PurePosixPath
import stat
import zipfile
from .records import LANE_ROOT

WHEEL_NAME='sortedcontainers-2.4.0-py2.py3-none-any.whl'
TASK_NAME='vendor-sortedcontainers-2.4.0.whl'
SHA256='a163dcaede0f1c021485e957a39245190e74249897e2ae4b2aa38595db237ee0'
SIZE=29575
PATH=LANE_ROOT/'data/vendor'/WHEEL_NAME
MEMBERS=frozenset(('sortedcontainers/__init__.py','sortedcontainers/sortedlist.py',
    'sortedcontainers/sortedset.py','sortedcontainers/sorteddict.py',
    'sortedcontainers-2.4.0.dist-info/LICENSE','sortedcontainers-2.4.0.dist-info/METADATA',
    'sortedcontainers-2.4.0.dist-info/WHEEL','sortedcontainers-2.4.0.dist-info/top_level.txt',
    'sortedcontainers-2.4.0.dist-info/RECORD'))


def validate_bytes(data):
    if len(data)!=SIZE or hashlib.sha256(data).hexdigest()!=SHA256:
        raise ValueError('Approved sortedcontainers wheel identity mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members=archive.infolist()
        if len(members)!=len(MEMBERS) or {m.filename for m in members}!=MEMBERS:
            raise ValueError('Unexpected dependency archive members')
        for member in members:
            path=PurePosixPath(member.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(member.external_attr>>16) or member.flag_bits&1:
                raise ValueError('Unsafe dependency archive member')
        if archive.testzip() is not None:raise ValueError('Dependency archive CRC mismatch')
    return data


def read_bundle():
    return validate_bytes(PATH.read_bytes())
