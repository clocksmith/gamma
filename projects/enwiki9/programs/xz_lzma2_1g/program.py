import subprocess


ARGS = [
    "xz",
    "-q",
    "-c",
    "-T1",
    "--check=crc32",
    "--lzma2=preset=9e,dict=1024MiB",
]


def compress(data: bytes) -> bytes:
    return subprocess.run(
        ARGS,
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def decompress(data: bytes) -> bytes:
    return subprocess.run(
        ["xz", "-q", "-d", "-c", "--memlimit-decompress=0"],
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
