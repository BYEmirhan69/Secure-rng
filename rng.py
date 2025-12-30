from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from secrets import token_bytes

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms

MAX_REQUEST = 10_000_000  


def _hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, out_len: int) -> bytes:
    """Minimal HKDF-SHA256 (extract+expand)."""
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    t = b""
    c = 1
    while len(okm) < out_len:
        t = hmac.new(prk, t + info + bytes([c]), hashlib.sha256).digest()
        okm += t
        c += 1
    return okm[:out_len]


@dataclass
class SecureRNG:
    """
    SecureRNG: OS CSPRNG entropy + ChaCha20-based DRBG

    API:
      - next_bytes(n) -> bytes
      - reseed(extra=b"") -> None
      - randbelow(k) -> int (opsiyonel)
    """

    _key: bytes
    _nonce: bytes
    _counter: int
    _generated: int
    _reseed_interval: int

    @staticmethod
    def new(reseed_interval_bytes: int = 1_048_576, extra_seed: bytes = b"") -> "SecureRNG":
        """Create a new SecureRNG instance."""
        entropy = token_bytes(32)

        noise = (
            os.urandom(16)
            + str(os.getpid()).encode()
            + str(os.getppid()).encode()
            + str(id(object())).encode()   
        )

        ikm = entropy + extra_seed + noise
        salt = token_bytes(32)

        material = _hkdf_sha256(ikm=ikm, salt=salt, info=b"SecureRNG-v1 init", out_len=48)
        return SecureRNG(
            _key=material[:32],
            _nonce=material[32:48],
            _counter=0,
            _generated=0,
            _reseed_interval=max(64 * 1024, reseed_interval_bytes),
        )

    def reseed(self, extra: bytes = b"") -> None:
        """Refresh internal state with new entropy."""
        entropy = token_bytes(32)
        salt = token_bytes(32)

        ikm = self._key + self._nonce + self._counter.to_bytes(8, "big") + entropy + extra
        material = _hkdf_sha256(ikm=ikm, salt=salt, info=b"SecureRNG-v1 reseed", out_len=48)

        self._key = material[:32]
        self._nonce = material[32:48]
        self._counter = 0
        self._generated = 0

    def next_bytes(self, n: int) -> bytes:
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a non-negative integer")
        if n == 0:
            return b""
        if n > MAX_REQUEST:
            raise ValueError(f"n too large (max {MAX_REQUEST})")

        if self._generated >= self._reseed_interval:
            self.reseed()

        out = bytearray()
        backend = default_backend()

        while len(out) < n:
            cbytes = self._counter.to_bytes(8, "big")

            per_nonce = _hkdf_sha256(
                ikm=self._nonce + cbytes,
                salt=b"SecureRNG-nonce-salt",
                info=b"SecureRNG-v1 per-block nonce",
                out_len=16,
            )

            cipher = Cipher(algorithms.ChaCha20(self._key, per_nonce), mode=None, backend=backend)
            block = cipher.encryptor().update(b"\x00" * 64)

            out.extend(block)
            self._counter += 1

        self._generated += n
        return bytes(out[:n])

    def randbelow(self, k: int) -> int:
        """Uniform integer in [0, k)."""
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k must be a positive integer")

        bits = k.bit_length()
        nbytes = (bits + 7) // 8
        mask = (1 << bits) - 1

        while True:
            x = int.from_bytes(self.next_bytes(nbytes), "big") & mask
            if x < k:
                return x

    def __repr__(self) -> str:
        return (
            f"SecureRNG(reseed_interval={self._reseed_interval}, "
            f"counter={self._counter}, generated={self._generated})"
        )
