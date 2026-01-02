import pytest
from rng import SecureRNG
import time

def test_length():
    r = SecureRNG.new()
    assert len(r.next_bytes(0)) == 0
    assert len(r.next_bytes(1)) == 1
    assert len(r.next_bytes(32)) == 32
    assert len(r.next_bytes(1000)) == 1000


def test_not_constant():
    r = SecureRNG.new()
    a = r.next_bytes(64)
    b = r.next_bytes(64)
    assert a != b


def test_reseed_changes_stream():
    r = SecureRNG.new()
    a = r.next_bytes(64)
    r.reseed(b"extra")
    b = r.next_bytes(64)
    assert a != b


@pytest.mark.parametrize("k", [2, 3, 7, 17, 100, 1000])
def test_randbelow_range(k: int):
    r = SecureRNG.new()
    x = r.randbelow(k)
    assert 0 <= x < k

def test_time_based_reseed_changes_stream():
    r = SecureRNG.new(reseed_interval_seconds=0.01)
    a = r.next_bytes(64)
    time.sleep(0.02)
    b = r.next_bytes(64)
    assert a != b