"""Literal selection packets with an explicit fixed width of 4 through 12 bits."""
import hashlib,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from literals import dictionary_bytes,reconstruct,decode_bytes

def encode(literals, sequence, bits):
    if type(bits) is not int or not 4 <= bits <= 12: raise ValueError('width must be 4..12')
    reconstruct(literals,sequence)
    if len(literals)>1<<bits: raise ValueError('dictionary exceeds width')
    payload=bytearray();value=occupied=0
    for index in sequence:
        value=(value<<bits)|index;occupied+=bits
        while occupied>=8:
            occupied-=8;payload.append((value>>occupied)&255)
            value&=(1<<occupied)-1
    if occupied:payload.append(value<<(8-occupied))
    return b'LTV1'+bytes([bits])+hashlib.sha256(dictionary_bytes(literals)).digest()+struct.pack('>I',len(sequence))+payload

def decode(dictionary, packet):
    if len(packet)<41 or packet[:4]!=b'LTV1':raise ValueError('packet header')
    bits=packet[4]
    if not 4<=bits<=12:raise ValueError('width')
    if len(dictionary)<8 or dictionary[:4]!=b'LTD1':raise ValueError('dictionary header')
    if struct.unpack_from('>I',dictionary,4)[0]>1<<bits:raise ValueError('dictionary exceeds width')
    count=struct.unpack_from('>I',packet,37)[0]
    if len(packet)!=41+(count*bits+7)//8:raise ValueError('packet length')
    padding=(-count*bits)%8
    if padding and packet[-1]&((1<<padding)-1):raise ValueError('nonzero padding')
    sequence=[];value=occupied=0
    for byte in packet[41:]:
        value=(value<<8)|byte;occupied+=8
        while occupied>=bits and len(sequence)<count:
            occupied-=bits;sequence.append((value>>occupied)&((1<<bits)-1));value&=(1<<occupied)-1
    expanded=b'LTP1'+packet[5:37]+packet[37:41]+b''.join(struct.pack('>I',i) for i in sequence)
    return decode_bytes(dictionary,expanded)
