import pytest

from cidnilib.inmemds import InMemoryDataService
from cidnilib.dssplitter import SplitterDataService


@pytest.fixture
def ds1():
    return InMemoryDataService(":memory:")


@pytest.fixture
def ds2():
    return InMemoryDataService(":memory:")


@pytest.fixture
def ds(ds1, ds2):
    return SplitterDataService(ds1, ds2, size_limit=5)


def test_small_data_goes_to_first_store(ds, ds1, ds2):
    cid, created = ds.know_binary(b"abc")

    assert created
    assert ds1.known_binary(cid)
    assert not ds2.known_binary(cid)
    assert ds.recall_binary(cid) == b"abc"


def test_large_data_goes_to_second_store(ds, ds1, ds2):
    cid, created = ds.know_binary(b"abcdefg")

    assert created
    assert not ds1.known_binary(cid)
    assert ds2.known_binary(cid)
    assert ds2.recall_binary(cid) == b"abcdefg"
    assert ds.recall_binary(cid) == b"abcdefg"


def test_size_limit_boundary_goes_to_second_store(ds, ds1, ds2):
    cid, _ = ds.know_binary(b"12345")

    assert not ds1.known_binary(cid)
    assert ds2.known_binary(cid)


def test_same_data_gets_same_cid(ds):
    cid1, _ = ds.know_binary(b"same")
    cid2, _ = ds.know_binary(b"same")

    assert cid1 == cid2


def test_different_data_get_different_cids(ds):
    cid1, _ = ds.know_binary(b"one")
    cid2, _ = ds.know_binary(b"something larger")

    assert cid1 != cid2


def test_known_binary_checks_both_stores(ds):
    cid1, _ = ds.know_binary(b"abc")
    cid2, _ = ds.know_binary(b"abcdef")

    assert ds.known_binary(cid1)
    assert ds.known_binary(cid2)


def test_recall_binary_checks_both_stores(ds):
    cid1, _ = ds.know_binary(b"abc")
    cid2, _ = ds.know_binary(b"abcdef")

    assert ds.recall_binary(cid1) == b"abc"
    assert ds.recall_binary(cid2) == b"abcdef"


def test_forget_small_data(ds):
    cid, _ = ds.know_binary(b"abc")

    ds.forget_binary(cid)

    assert not ds.known_binary(cid)


def test_forget_large_data(ds):
    cid, _ = ds.know_binary(b"abcdef")

    ds.forget_binary(cid)

    assert not ds.known_binary(cid)


def test_forget_unknown_id_is_silent(ds):
    ds.forget_binary(b"not-real")


def test_list_known_cids_contains_all(ds):
    cid1, _ = ds.know_binary(b"abc")
    cid2, _ = ds.know_binary(b"abcdef")

    cids = set(ds.list_known_cids())

    assert cid1 in cids
    assert cid2 in cids
