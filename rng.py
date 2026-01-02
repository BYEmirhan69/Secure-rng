from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from secrets import token_bytes

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAX_REQUEST = 10_000_000  


def _hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, out_len: int) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=out_len,
        salt=salt,
        info=info,
    )
    return hkdf.derive(ikm)


def _zero_bytes(b: bytearray) -> None:
    """Best-effort memory zeroing."""
    for i in range(len(b)):
        b[i] = 0


@dataclass(slots=True)
class SecureRNG:
    _key: bytearray          
    _nonce_base: bytearray   
    _counter: int
    _generated: int

    _reseed_interval_bytes: int
    _reseed_interval_seconds: float
    _last_reseed_time: float

    _pid: int              
    _lock: threading.Lock

    @staticmethod
    def new(
        reseed_interval_bytes: int = 1_048_576,
        reseed_interval_seconds: float = 60.0,
        extra_seed: bytes = b"",
    ) -> "SecureRNG":

        entropy = token_bytes(32)
        noise = os.urandom(32)

        ikm = entropy + extra_seed + noise
        salt = token_bytes(32)

        material = _hkdf_sha256(
            ikm=ikm,
            salt=salt,
            info=b"SecureRNG-v4 init",
            out_len=48,
        )

        key = bytearray(material[:32])
        nonce_base = bytearray(material[32:48])

        _zero_bytes(bytearray(material))
        _zero_bytes(bytearray(entropy))

        now = time.monotonic()

        return SecureRNG(
            _key=key,
            _nonce_base=nonce_base,
            _counter=0,
            _generated=0,
            _reseed_interval_bytes=max(64 * 1024, reseed_interval_bytes),
            _reseed_interval_seconds=float(reseed_interval_seconds),
            _last_reseed_time=now,
            _pid=os.getpid(),
            _lock=threading.Lock(),
        )

    def _reseed_locked(self, extra: bytes) -> None:
        entropy = token_bytes(32)
        salt = token_bytes(32)

        ikm = (
            bytes(self._key)
            + bytes(self._nonce_base)
            + self._counter.to_bytes(8, "big")
            + entropy
            + extra
        )

        material = _hkdf_sha256(
            ikm=ikm,
            salt=salt,
            info=b"SecureRNG-v4 reseed",
            out_len=48,
        )

        _zero_bytes(self._key)
        _zero_bytes(self._nonce_base)

        self._key = bytearray(material[:32])
        self._nonce_base = bytearray(material[32:48])

        self._counter = 0
        self._generated = 0
        self._last_reseed_time = time.monotonic()
        self._pid = os.getpid()

        _zero_bytes(bytearray(material))
        _zero_bytes(bytearray(entropy))

    def reseed(self, extra: bytes = b"") -> None:
        with self._lock:
            self._reseed_locked(extra)

    def next_bytes(self, n: int) -> bytes:
        if not isinstance(n, int) or n < 0:
            raise ValueError("n must be a non-negative integer")
        if n == 0:
            return b""
        if n > MAX_REQUEST:
            raise ValueError(f"n too large (max {MAX_REQUEST})")

        with self._lock:
            if os.getpid() != self._pid:
                self._reseed_locked(b"")

            now = time.monotonic()
            if (
                self._generated >= self._reseed_interval_bytes
                or (now - self._last_reseed_time) >= self._reseed_interval_seconds
            ):
                self._reseed_locked(b"")

            out = bytearray()
            backend = default_backend()

            while len(out) < n:
                per_nonce = self._nonce_base[:8] + self._counter.to_bytes(8, "big")

                cipher = Cipher(
                    algorithms.ChaCha20(bytes(self._key), per_nonce),
                    mode=None,
                    backend=backend,
                )

                out.extend(cipher.encryptor().update(b"\x00" * 64))
                self._counter += 1

            new_key = _hkdf_sha256(
                ikm=bytes(self._key) + self._counter.to_bytes(8, "big"),
                salt=bytes(self._nonce_base),
                info=b"SecureRNG-v4 key-evolve",
                out_len=32,
            )

            _zero_bytes(self._key)
            self._key = bytearray(new_key)
            _zero_bytes(bytearray(new_key))

            self._generated += n
            return bytes(out[:n])

    def randbelow(self, k: int) -> int:
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
            f"SecureRNG(counter={self._counter}, "
            f"generated={self._generated}, "
            f"pid={self._pid})"
        )
