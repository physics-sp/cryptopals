#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import print_function
import io
import sys
sys.path.append("..")
from cryptolib import *

class Sha1Hash(object):
    """A class that mimics that hashlib api and implements the SHA-1 algorithm."""

    name = 'python-sha1'
    digest_size = 20
    block_size = 64

    def __init__(self):
        # Initial digest variables
        self._h = (
            0x67452301,
            0xEFCDAB89,
            0x98BADCFE,
            0x10325476,
            0xC3D2E1F0,
        )

        # bytes object with 0 <= len < 64 used to store the end of the message
        # if the message length is not congruent to 64
        self._unprocessed = b''
        # Length in bytes of all data that has been processed so far
        self._message_byte_length = 0

    def _left_rotate(self, n, b):
        """Left rotate a 32-bit integer n by b bits."""
        return ((n << b) | (n >> (32 - b))) & 0xffffffff


    def _process_chunk(self, chunk, h0, h1, h2, h3, h4):
        """Process a chunk of data and return the new digest variables."""
        assert len(chunk) == 64

        w = [0] * 80

        # Break chunk into sixteen 4-byte big-endian words w[i]
        for i in range(16):
            w[i] = struct.unpack(b'>I', chunk[i * 4:i * 4 + 4])[0]

        # Extend the sixteen 4-byte words into eighty 4-byte words
        for i in range(16, 80):
            w[i] = self._left_rotate(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1)

        # Initialize hash value for this chunk
        a = h0
        b = h1
        c = h2
        d = h3
        e = h4

        for i in range(80):
            if 0 <= i <= 19:
                # Use alternative 1 for f from FIPS PB 180-1 to avoid bitwise not
                f = d ^ (b & (c ^ d))
                k = 0x5A827999
            elif 20 <= i <= 39:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif 40 <= i <= 59:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            elif 60 <= i <= 79:
                f = b ^ c ^ d
                k = 0xCA62C1D6

            a, b, c, d, e = ((self._left_rotate(a, 5) + f + e + k + w[i]) & 0xffffffff,
                             a, self._left_rotate(b, 30), c, d)

        # Add this chunk's hash to result so far
        h0 = (h0 + a) & 0xffffffff
        h1 = (h1 + b) & 0xffffffff
        h2 = (h2 + c) & 0xffffffff
        h3 = (h3 + d) & 0xffffffff
        h4 = (h4 + e) & 0xffffffff
 
        return h0, h1, h2, h3, h4


    def update(self, arg):
        """Update the current digest.

        This may be called repeatedly, even after calling digest or hexdigest.

        Arguments:
            arg: bytes, bytearray, or BytesIO object to read from.
        """
        if isinstance(arg, (bytes, bytearray)):
            arg = io.BytesIO(arg)

        # Try to build a chunk out of the unprocessed data, if any
        chunk = self._unprocessed + arg.read(64 - len(self._unprocessed))

        # Read the rest of the data, 64 bytes at a time
        while len(chunk) == 64:
            self._h = self._process_chunk(chunk, *self._h)
            self._message_byte_length += 64
            chunk = arg.read(64)

        self._unprocessed = chunk
        return self

    def digest(self):
        """Produce the final hash value (big-endian) as a bytes object"""
        return b''.join(struct.pack(b'>I', h) for h in self._produce_digest())

    def hexdigest(self):
        """Produce the final hash value (big-endian) as a hex string"""
        return '%08x%08x%08x%08x%08x' % self._produce_digest()

    def _produce_digest(self):
        """Return finalized digest variables for the data processed so far."""
        # Pre-processing:
        message = self._unprocessed
        message_byte_length = self._message_byte_length + len(message)

        # append the bit '1' to the message
        message += b'\x80'

        # append 0 <= k < 512 bits '0', so that the resulting message length (in bytes)
        # is congruent to 56 (mod 64)
        message += b'\x00' * ((56 - (message_byte_length + 1) % 64) % 64)

        # append length of message (before pre-processing), in bits, as 64-bit big-endian integer
        message_bit_length = message_byte_length * 8
        message += struct.pack(b'>Q', message_bit_length)

        # Process the final chunk
        # At this point, the length of the message is either 64 or 128 bytes.
        h = self._process_chunk(message[:64], *self._h)

        if len(message) == 64:
            return h
        return self._process_chunk(message[64:], *h)

    def set_registers(self, h0, h1, h2, h3, h4):
        self._h = (
            int.from_bytes(h0, "big"),
            int.from_bytes(h1, "big"),
            int.from_bytes(h2, "big"),
            int.from_bytes(h3, "big"),
            int.from_bytes(h4, "big")
        )


def sha1(data=b''):
    return Sha1Hash().update(data).hexdigest()

key = rand_bytes(16)

def HMAC_SHA1(message):
    return sha1(key + message)

def check_mac(message, mac):
    return HMAC_SHA1(message) == mac

def main():
    lenmsg = random.randint(1, 100)
    msg = random_string(lenmsg).encode('utf-8')
    mac = HMAC_SHA1(msg)

    index = random.randint(0, lenmsg - 1)
    new_msg  = msg[:index]
    new_byte = msg[index] ^ (1 << random.randint(0, 8))
    new_byte = bytes([new_byte])
    new_msg += new_byte
    new_msg += msg[index+1:]

    if check_mac(new_msg, mac):
        print('mac bypassed! (bad)')
    else:
        print('mac check failed (good)')

if __name__ == '__main__':
    main()
