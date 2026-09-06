"""Build the observation-only SHA successor; retain the existing bundle interface."""
from tools import midas_open_boundary_observer_v1 as original

SOURCES = (original.ROOT / "tools/midas_open_boundary_observer_sha_v1.cpp", *original.SOURCES[1:])


def build(cache_dir):
    return original.parent.build_cpp_cached(sources=SOURCES, flags=original.parent.FLAGS,
                                           cache_dir=cache_dir, timeout_seconds=120)


def __getattr__(name):
    return getattr(original, name)
