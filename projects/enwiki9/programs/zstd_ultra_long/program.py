import subprocess


ARGS = ["zstd", "-q", "--ultra", "-22", "--long=31", "-T1", "--stdout"]


def compress(data: bytes) -> bytes:
    return subprocess.run(
        ARGS,
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def decompress(data: bytes) -> bytes:
    return subprocess.run(
        ["zstd", "-q", "-d", "--long=31", "--stdout"],
        input=data,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
