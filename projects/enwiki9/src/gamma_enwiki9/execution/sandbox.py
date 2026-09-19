"""Restricted read-only source mounts for verification and delivery fixtures."""
from pathlib import Path
import shutil
import sys


def python_command(*, readonly: dict[Path, str], writable: dict[Path, str],
                   argv: list[str], cwd: str) -> list[str]:
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise RuntimeError("restricted replay requires provisioned bubblewrap")
    command = [bwrap, "--unshare-all", "--die-with-parent", "--new-session",
               "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--clearenv",
               "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "LC_ALL", "C",
               "--setenv", "PYTHONDONTWRITEBYTECODE", "1"]
    for path in ("/usr", "/lib", "/lib64", "/bin"):
        if Path(path).exists():
            command += ["--ro-bind", path, path]
    # Python's provisioned environment is an explicit runtime dependency, not
    # a source fallback into the checkout. No project/results directories mount.
    prefix = Path(sys.prefix)
    python = "/usr/bin/python3"
    if sys.prefix != sys.base_prefix:
        command += ["--ro-bind", str(prefix), "/python"]
        python = "/python/bin/python"
    for source, target in readonly.items():
        command += ["--ro-bind", str(source), target]
    for source, target in writable.items():
        command += ["--bind", str(source), target]
    return [*command, "--chdir", cwd, "--", python, "-B", *argv]
