"""Release clean pages of closed, owned observation files without changing bytes."""
import os
import stat
from pathlib import Path


def release_closed_file(path):
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):raise ValueError('trace is not a regular file')
        os.fdatasync(fd)
        os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        if identity(before)!=identity(after):raise ValueError('trace changed during cache release')
        return dict(path=str(path),bytes=after.st_size,flushed=True,cache_release_requested=True)
    finally:
        os.close(fd)


def memory_snapshot(group):
    try:
        fields=dict(line.split() for line in (Path(group)/'memory.stat').read_text().splitlines())
        return dict(current_bytes=int((Path(group)/'memory.current').read_text()),
                    anon_bytes=int(fields['anon']),file_bytes=int(fields['file']),missing_diagnostics=[])
    except (OSError,ValueError,KeyError) as error:
        return dict(missing_diagnostics=['optional cache attribution unavailable: '+str(error)])
