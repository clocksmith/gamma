"""Strict native-payload frame: four-byte magic, table SHA256, byte count, width8."""
import hashlib
import struct
from native import table_from_header,decode


def pack(header,payload):
    decode(table_from_header(header),payload)
    return b'FSN1'+hashlib.sha256(header).digest()+struct.pack('>I',len(payload))+b'\x08'+payload


def unpack(header,packet):
    if len(packet)<41 or packet[:4]!=b'FSN1' or packet[4:36]!=hashlib.sha256(header).digest() or packet[40]!=8:raise ValueError('frame/header mismatch')
    size=struct.unpack('>I',packet[36:40])[0]
    if len(packet)!=41+size:raise ValueError('frame length mismatch')
    return decode(table_from_header(header),packet[41:])
