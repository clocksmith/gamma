"""An inherited cgroup memory limit, distinct from virtual address space."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


CGROUP_ROOT = Path("/sys/fs/cgroup")


def current_cgroup() -> Path:
    rows = [line.split(":", 2)[2] for line in Path("/proc/self/cgroup").read_text().splitlines()
            if line.startswith("0::")]
    if len(rows) != 1 or not rows[0].startswith("/") or ".." in Path(rows[0]).parts:
        raise ValueError("unified process cgroup is unavailable")
    return CGROUP_ROOT / rows[0].lstrip("/")


@dataclass(frozen=True)
class CgroupMemoryGuard:
    path: Path
    descriptor: int
    device: int
    inode: int
    limit_bytes: int

    @classmethod
    def current(cls, limit_bytes: int):
        if type(limit_bytes) is not int or limit_bytes <= 0:
            raise ValueError("positive resident memory limit required")
        path = current_cgroup()
        if path.resolve() != path or not path.is_relative_to(CGROUP_ROOT):
            raise ValueError("redirected cgroup")
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        info = os.fstat(descriptor)
        guard = cls(path, descriptor, info.st_dev, info.st_ino, limit_bytes)
        try:
            guard.verify(limit_bytes)
        except BaseException:
            os.close(descriptor)
            raise
        return guard

    def _read(self, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=self.descriptor)
        try:
            return os.read(fd, 128).decode().strip()
        finally:
            os.close(fd)

    def verify(self, budget_bytes: int):
        descriptor = os.fstat(self.descriptor)
        path = self.path.stat(follow_symlinks=False)
        if (descriptor.st_dev, descriptor.st_ino) != (self.device, self.inode) or not os.path.samestat(descriptor, path):
            raise ValueError("memory cgroup identity changed")
        membership = current_cgroup()
        if not membership.is_relative_to(self.path):
            raise ValueError("process left the inherited memory cgroup")
        maximum = self._read("memory.max")
        if maximum == "max" or not 0 < int(maximum) <= min(self.limit_bytes, budget_bytes):
            raise ValueError("inherited cgroup does not enforce the resident memory budget")
        if self._read("memory.swap.max") != "0":
            raise ValueError("inherited cgroup permits unbudgeted swap")
        return {"path": str(self.path), "device": self.device, "inode": self.inode,
                "memory_max_bytes": int(maximum), "swap_max_bytes": 0}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.descriptor)
