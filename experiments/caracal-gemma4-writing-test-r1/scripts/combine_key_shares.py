"""Caracal Gemma-4 writing test — reconstruct the archive password from the two 2-of-2 shares.

2-of-2 scheme: password_bytes = share_1_bytes XOR share_2_bytes.
Each share is grouped Base32: <body groups> + final <CRC group>. The CRC group is the last 7 Base32
characters (base32 of the body's 4-byte CRC32, unpadded). Neither share alone reveals any password
byte. This is the reference (CLI) implementation; combine-reveal-shares.html mirrors it offline.

Encode (reference, used by build_reveal_archive.py):
    body_b32 = base32(body).rstrip("=")                 # grouped in 4s for readability
    crc_b32  = base32(crc32(body).to_bytes(4,"big")).rstrip("=")   # 7 chars
    share    = "-".join(4-char groups of body_b32) + "-" + crc_b32

Usage: py combine_key_shares.py <SHARE1> <SHARE2>
"""
import base64, re, sys, zlib

CRC_LEN = 7   # base32 of 4 bytes, unpadded


def _pad(x):
    return x + "=" * ((8 - len(x) % 8) % 8)


def _decode(share):
    raw = re.sub(r"[^A-Z2-7]", "", share.upper())
    if len(raw) <= CRC_LEN:
        raise ValueError("share too short")
    body_b32, crc_b32 = raw[:-CRC_LEN], raw[-CRC_LEN:]
    body = base64.b32decode(_pad(body_b32))
    crc = base64.b32decode(_pad(crc_b32))[:4]
    if (zlib.crc32(body) & 0xffffffff).to_bytes(4, "big") != crc:
        raise ValueError("share checksum mismatch")
    return body


def combine(share1, share2):
    b1, b2 = _decode(share1), _decode(share2)
    if len(b1) != len(b2):
        raise ValueError("share length mismatch")
    return bytes(x ^ y for x, y in zip(b1, b2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: py combine_key_shares.py <SHARE1> <SHARE2>"); sys.exit(2)
    pw = combine(sys.argv[1], sys.argv[2])
    print(pw.decode("utf-8", "replace"))
