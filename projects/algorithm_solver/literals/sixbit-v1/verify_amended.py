"""verify.py with one post-freeze correction; verify.py itself stays as frozen.

bitpack.decode returns text, but verify.py compared it with source bytes, so that check
failed on every LTV1 packet even after literal_codec.verify_packet had accepted it. This
wrapper encodes the decoded text before the same comparison. Nothing else changes."""
import verify
from bitpack import decode

verify.ltv_decode = lambda dictionary, packet: decode(dictionary, packet).encode('utf-8')

if __name__ == '__main__':
    verify.main()
